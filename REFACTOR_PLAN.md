# Content Pipeline Refactor Plan

**Status:** Proposal — 2026-07-20
**Verdict in one sentence:** Replace the free-running AgentCore/Strands agent loop with a
deterministic batch pipeline in a plain Lambda that uses Claude (Bedrock, structured
outputs) for exactly three judgment steps — extract, evaluate, write — and delete
everything else.

---

## 1. Why (evidence from production)

The system's job is fixed and repeatable: *crawl known local sources weekly, find new
events, write trilingual cards, retire expired ones, email the owner.* That is an ETL
job with three LLM-shaped steps — not an open-ended agent task. Running it as a
20+-tool-call autonomous loop is the root cause of every observed failure:

| Observed failure (production) | Root cause |
|---|---|
| 31 of 48 published posts expired (March–June) but never archived; only 1 post archived ever | Archival delegated to model judgment inside the loop; dates stored only as localized display strings ("23–25. maj 2026") so code *can't* do it |
| Runs die silently; SNS email dated 2026-07-19 contains April reasoning | Invoker fire-and-forgets `invoke_agent_runtime` and never drains the response stream; notifier stitches the *current* snapshot to the *latest* (April) `PIPELINE_RUN` row with no run correlation |
| "DuckDuckGo rate-limited after 3 queries" | `ddgs` scrapes DDG from AWS egress IPs, which are fingerprinted; unfixable (confirmed by current research — the library itself carries an "educational purposes only" disclaimer) |
| Source sites failing (DNS/SSL/HTTP 455), 1500-char page truncation | Crawl budget squeezed through serialized agent tool calls; content cap starves extraction |
| Agent forgets what it read | `SlidingWindowConversationManager(window_size=10)` with 20+ tool calls evicts its own findings |
| Validator never catches expired dates | Its docstring promises the check; the code doesn't implement it — and it runs *after* publish anyway |

Also verified (mid-2026 research):
- Anthropic's native `web_search`/`web_fetch` server tools are **not available on Bedrock** (any integration path) — search must be solved client-side regardless.
- **Structured outputs are GA on Bedrock** — schema-enforced JSON, exactly what pipeline stages need.
- Lambda's 15-min cap is unchanged, but the 5–20 min run durations belong to the *old* architecture (30+ serialized model round-trips). The pipeline shape needs ~5–8 model calls and a parallel crawl: ~6–10 min worst case, enforced by code budgets.
- AgentCore is GA and cheap, but its session/streaming semantics (idle timeout, MaxLifetime, killed streams) are built for interactive agents and are precisely where this batch job kept dying.

## 2. Goals (measurable)

1. **Zero silent failures.** Every scheduled run ends in exactly one of: a truthful
   summary email, or an explicit failure alert. Enforced by (a) synchronous execution
   inside one Lambda (errors → existing Errors alarm), and (b) a dead-man canary that
   alerts if no `PIPELINE_RUN` row was written within 3h of schedule.
2. **No expired content on the site.** Any post whose `event_end` has passed is archived
   on the next run — deterministically, by code, not by model judgment.
3. **Zero rate-limit-degraded runs.** Search is a core capability (it drives source
   discovery — see goal 4) but runs on a real API, not scraping: SerpAPI free plan
   (250 Google.dk searches/mo vs ~25 needed, `gl=dk&hl=da`), Brave
   (`country=DK&search_lang=da`) as pluggable fallback, key(s) in SSM SecureString.
   `ddgs`/DuckDuckGo scraping is removed — AWS egress IPs are fingerprinted and it is
   the proven cause of crippled runs.
4. **The source list maintains itself.** The registry moves from hardcoded Python
   (`source_registry.py` — changeable only by deploy) to DynamoDB items the pipeline
   owns end-to-end: discover new sources via search, judge relevance, add on probation,
   track per-source health on every crawl, auto-retire dead ones, and report every
   addition/retirement in the weekly email. This was the original reason the system
   was made agentic; it is delivered here as deterministic lifecycle stages instead.
5. **Validation before publish, not after.** All current validator checks (languages,
   fields, category/tag, URL reachability) run as a gate in the write stage.
6. **Radical simplification.** Pipeline compute goes from 1 AgentCore runtime + 3
   Lambdas + 3 SQS queues + snapshot-diff plumbing → **2 Lambdas** (pipeline + canary).
   Deps drop `strands-agents`, `bedrock-agentcore`, `ddgs`, `cachetools`. One deploy
   path (SAM only — no agent zip → S3 → AgentCore resource).
7. **Testable per repo convention.** Every stage is a function with mockable edges
   (httpx, boto3 bedrock/dynamodb) — same philosophy as the existing test suite.
8. **Cost neutral or better.** Infra ≈ $0 either way; token spend drops (no sliding-window
   re-thrash, no 30-turn loops). Search $0/mo at this volume.

## 3. Target architecture

```
EventBridge (cron, unchanged)
   └─► content-pipeline Lambda  (900s timeout, ~1024MB, python3.12)
         stage 0  load state          — code (DDB: posts + SOURCE registry items)
         stage 1  archive expired     — code (event_end < today)
         stage 2  crawl               — code (async httpx, active + probation
                                        sources, per-domain politeness, 15s
                                        timeouts, trafilatura, ~5k chars/page);
                                        updates per-source health after every fetch
         stage 3  discover sources    — code: 3–6 search queries (SerpAPI,
                                        gl=dk&hl=da; seasonal + gap-driven) →
                                        result domains not in registry →
                                        1 Claude call: relevant local source?
                                        (tier, type, why) → insert as
                                        status=probation → crawled same run
         stage 4  extract candidates  — Claude call(s), structured output:
                                        {title, event_start/end ISO, location,
                                         source_url, category, details}
         stage 5  filter + judge      — code (dedup vs live posts, date window)
                                        then 1 Claude call: accept/reject + reasons
         stage 6  enrich (bounded)    — code: fetch detail URLs of accepted items
         stage 7  write + publish     — Claude call → trilingual copy (schema-
                                        enforced), Pydantic + URL gate, put_item
         stage 8  source lifecycle    — code: promote probation→active after
                                        first run yielding usable content;
                                        failing→retired after 4 consecutive
                                        failed runs (~1 month); never silent —
                                        every transition goes in the report
         stage 9  report              — code: email built from in-memory RunReport
                                        (published/archived/rejected + NEW SOURCES /
                                        RETIRED SOURCES sections), PIPELINE_RUN row
                                        w/ run_id, SNS publish
   └─► pipeline-canary Lambda (Sun 03:00) — alert if no fresh PIPELINE_RUN row
```

### Source registry as data (the original agentic intent, delivered)

`SOURCE` items in the existing single-table design (pk=`SOURCE`, sk=domain):
`{name, url, tier, type, notes, status: probation|active|failing|retired|closed,
consecutive_failures, last_success, last_checked, discovered_by: seed|search,
added_at}`. Seeded once from today's `source_registry.py` (all marked
`discovered_by: seed`, status active); `KNOWN_CLOSED` becomes `status: closed`.
From then on the pipeline owns the list: search discovers, Claude judges, health
tracking promotes/retires, the email reports every change. The owner can override
any source by editing the item (or via a future RPC action) — no deploy needed.

- Same skeleton runs `omraadet` monthly with an audit-stage config instead of
  discovery; its "new attraction" searches feed the same source-discovery stage.
- Time-budget safety: between stages the pipeline checks
  `context.get_remaining_time_in_millis()`; if low it skips to stage 7 and reports
  partial results honestly. The 15-min cliff cannot produce silence.
- Escape hatch: stages are separable; if the job ever outgrows Lambda, lift stages into
  Step Functions or a Fargate scheduled task without redesign.

### Model access
Plain `boto3` Bedrock (Converse/InvokeModel) with the existing SSM `MODEL_ID_PARAM` —
no agent framework needed once there is no tool loop. Structured outputs (or forced
tool-use with strict schema) + Pydantic validation with one retry on schema failure.
EU inference profile / Mantle ID stays a config value.

### What the LLM still decides (and nothing else)
- Which crawled text fragments are real, relevant candidate events (extract).
- Whether a newly found domain is a relevant local source worth tracking (source judge).
- Whether each candidate meets the editorial bar (judge — the excellent rubric in
  `BASE_SYSTEM.md` moves here, verbatim where possible).
- The trilingual copy (write — tone/translation/SEO rules move here).

Everything mechanical about source curation — health counters, promotion/retirement
thresholds, dedup against the existing registry, reporting — is code, which is why
this version of "maintain a curated source list" will actually happen every run
instead of surviving only as notes in an email.

### Source-judge rubric (the instructions, specified now — precision is the product)

Prompts live as versioned `.md` files per stage (same mechanism as today), each small
and single-purpose. The source judge is the most precision-critical; its contract:

**Evidence rule.** The judge never decides from a search snippet. The pipeline fetches
the candidate domain's homepage (and one internal page if linked: /kalender, /events,
/program) BEFORE the call; the judge sees extracted text only. No fetch → no judgment
→ logged as `unreachable`, not added.

**Accept — ALL must hold:**
1. *Geography:* the source's subject matter lies within the existing zone table
   (Core/Inner/Mid/Outer from BASE_SYSTEM; Occasional zone only for venues that host
   major events). The zone table moves verbatim into this prompt.
2. *Actionability:* publishes information a cottage guest in Agger can act on —
   dated events, opening hours, bookable activities, menus/food, routes. A site
   *about* the region with nothing actionable (pure history/blog archive) is reject.
3. *Freshness:* visible signs of updates within ~6 months (dated posts, current-season
   hours, upcoming events). Stale sites feed the pipeline nothing but risk.
4. *Crawlability:* the fetched extraction actually contains the content (a JS-shell
   site that extracts to boilerplate is `reject: not_crawlable`).

**Hard reject (any one):** national/global portals and OTAs (visitdenmark-scale,
booking.com-likes); SEO listicles/affiliate aggregators; social-media pages (FB/IG —
not crawlable); competitor cottage-rental marketing sites; duplicates of an existing
registry source (same organisation, different domain — judge receives the current
registry list); domains on the closed list.

**Tier assignment** uses the existing tier definitions verbatim (1 Agger-local,
2 Thy-regional, 3 wider/major-events-only, 4 news/background).

**Output schema (structured, enforced):**
`{relevant: bool, confidence: high|medium|low, tier: 1-4, type, suggested_name,
reasoning (1-2 sentences citing evidence from the fetched text), reject_reason?}`

**Code-side policy around the judgment (not model-decided):**
- `relevant + high` → insert as `probation`, crawled from next stage onward.
- `relevant + medium/low` → NOT added; listed in the email as a suggestion for the
  owner. Uncertainty never mutates the registry.
- Max **2 auto-added sources per run** — keeps "curated" meaningful and crawl budget
  bounded.
- Registry cap: **45 non-retired sources.** At the cap, additions require the email to
  propose a swap; nothing is silently evicted.
- Every stage prompt ends with the same instruction: cite evidence, and when
  uncertain, say so — the code treats uncertainty as "don't act, report".

### Schema changes (additive — frontend ignores unknown fields)
- Posts: `event_start`, `event_end` (ISO dates, null = evergreen), `run_id`,
  `url_last_checked`. Display dates stay localized strings in `translations`.
- One-time backfill: single Claude call parses the 48 existing display dates → ISO;
  immediately archive the ~31 already-expired posts (instant site fix).
- Drop write-side use of `relevance_score` (dead field) — judge score maps to
  `sort_order`.

## 4. What gets deleted

| Component | Fate |
|---|---|
| `AWS::BedrockAgentCore::Runtime` + execution role | deleted |
| `content_agent_invoker` Lambda | deleted (EventBridge targets pipeline directly) |
| `content_notifier` Lambda + queue + DLQ + snapshot logic | deleted — reporting is stage 7, race-free by construction |
| `content_validator` Lambda + queue | deleted — checks move pre-publish; link-rot of old posts becomes a small rotating URL check in stage 1 |
| `strands-agents`, `bedrock-agentcore`, `ddgs`, `cachetools` deps | removed |
| Agent zip → S3 packaging in `deploy.yml` | removed |
| `SlidingWindowConversationManager`, `RunStatsHook`, fallback-summary hack | obsolete |

Kept: prompts' editorial content (split into stage prompts), source registry content
(seeded into DynamoDB `SOURCE` items, then pipeline-maintained), DynamoDB table +
single-table design, SNS topic + subscription + alarms (retargeted), EventBridge
schedules, the entire RPC backend and frontend (untouched).

## 5. Non-chosen alternatives (for the record)

- **Keep AgentCore, fix orchestration:** cheapest diff, but keeps chat-session
  semantics under a batch job and keeps every deterministic task inside model judgment
  — the two proven failure sources.
- **Fargate scheduled task:** equally sound compute, but reintroduces Docker/ECR/cluster
  for a job that fits Lambda once the workload is pipeline-shaped.
- **Anthropic Managed Agents (scheduled deployments):** genuinely attractive fully-managed
  path (cron + native web_search built in), but moves off Bedrock/AWS billing and adds a
  second platform; a deterministic pipeline is also simply more reliable for a fixed
  weekly ETL than any agent loop, managed or not.

## 6. CI/CD (GitHub Actions) adjustments

Current state: a single `deploy.yml` on push-to-main. Findings:

- **Tests never run in CI.** The 31-test pytest suite (passes in 0.2s) is not wired
  into any workflow, and deploys don't depend on it. Fixed now (independent of the
  refactor): new `test.yml` runs backend pytest + frontend `tsc && vite build` on
  every PR and push to main.
- **Agent packaging must be removed with Phase 3:** deploy.yml steps "Package agent
  runtime" (aarch64 zip via uv) and "Upload agent runtime to S3", plus the
  `ContentAgentCodeBucket/Key` parameter-overrides — all obsolete once the AgentCore
  resource leaves `template.yaml`. The workflow shrinks by ~20 lines.
- **Gate deploy on tests** (Phase 2): make the deploy job depend on the test jobs
  (`needs:`) or trigger deploy via `workflow_run` after Test succeeds on main. Also
  add `workflow_dispatch` so a deploy can be triggered manually.
- **New pipeline Lambda builds via standard `sam build`** on the ubuntu runner
  (x86_64 manylinux wheels — note trafilatura pulls lxml, a binary wheel; works on
  the runner's default target, no container build needed). No new workflow steps.
- **Verify once in AWS (not visible from the repo):** the OIDC deploy role
  (`AWS_DEPLOY_ROLE_ARN`) must be allowed to DELETE the
  `AWS::BedrockAgentCore::Runtime` + named IAM role and CREATE the new
  Lambda/EventBridge/alarm resources. If the role was written narrowly, the Phase 3
  deploy fails loudly at changeset execution — check its policy first.
- **All AWS access goes through CI** (only the OIDC deploy role has credentials).
  The Phase 0 backfill therefore runs as a `workflow_dispatch` workflow
  (`backfill.yml`): trigger with `apply=false`, read the printed plan in the job
  log, re-run with `apply=true`. Note: workflow_dispatch workflows only become
  triggerable in the GitHub UI once the file is on the default branch — Phase 0
  runs right after this branch merges.
- **One-time manual step:** create the SerpAPI key SSM SecureString parameter
  (console, or a tiny dispatch workflow with the key as a masked input).

## 7. Migration plan

1. **Phase 0 — stop the bleeding (independent of refactor):** one-off script backfills
   `event_start`/`event_end` and archives expired posts. Site is correct again.
2. **Phase 1 — build:** `backend/pipelines/content/` with stages as pure functions +
   pytest per layer (mock httpx/bedrock/dynamodb at edges). Includes the registry
   seed script (`source_registry.py` → `SOURCE` items).
3. **Phase 2 — infra swap:** new pipeline + canary functions in `template.yaml`;
   retarget schedules and alarms; SerpAPI key to SSM.
4. **Phase 3 — delete:** agentcore_runtimes/, invoker, notifier, validator, queues,
   deploy.yml agent packaging.
5. **Phase 4 — verify:** manual invoke of both pipelines against prod table; confirm
   email, site state, canary; then leave schedules on.
