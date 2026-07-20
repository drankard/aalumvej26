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
3. **Zero rate-limit-degraded runs.** No scraping, and no external search API in the
   default build: discovery is registry-crawl only (tiers 1–2 include aggregators —
   Thy360 calendar, KultuNaut, VisitThy — plus tier 4 news for new openings), which is
   what rate-limited production runs have effectively been doing successfully anyway.
   Web search is an optional pluggable sub-stage (`SEARCH_PROVIDER: none|serpapi|brave`;
   SerpAPI free plan = 250 Google.dk searches/mo, `gl=dk&hl=da`, key in SSM) to enable
   later only if run reports show thin candidate counts.
4. **Validation before publish, not after.** All current validator checks (languages,
   fields, category/tag, URL reachability) run as a gate in the write stage.
5. **Radical simplification.** Pipeline compute goes from 1 AgentCore runtime + 3
   Lambdas + 3 SQS queues + snapshot-diff plumbing → **2 Lambdas** (pipeline + canary).
   Deps drop `strands-agents`, `bedrock-agentcore`, `ddgs`, `cachetools`. One deploy
   path (SAM only — no agent zip → S3 → AgentCore resource).
6. **Testable per repo convention.** Every stage is a function with mockable edges
   (httpx, boto3 bedrock/dynamodb) — same philosophy as the existing test suite.
7. **Cost neutral or better.** Infra ≈ $0 either way; token spend drops (no sliding-window
   re-thrash, no 30-turn loops). Search $0/mo at this volume.

## 3. Target architecture

```
EventBridge (cron, unchanged)
   └─► content-pipeline Lambda  (900s timeout, ~1024MB, python3.12)
         stage 0  load state          — code (DDB)
         stage 1  archive expired     — code (event_end < today)
         stage 2  crawl               — code (async httpx, registry tiers 1+2,
                                        per-domain politeness, 15s timeouts,
                                        trafilatura extraction, ~5k chars/page)
                  + search (OPTIONAL) — code (off by default; pluggable SerpAPI/Brave
                                        provider, 3–5 queries, gl=dk&hl=da)
         stage 3  extract candidates  — Claude call(s), structured output:
                                        {title, event_start/end ISO, location,
                                         source_url, category, details}
         stage 4  filter + judge      — code (dedup vs live posts, date window)
                                        then 1 Claude call: accept/reject + reasons
         stage 5  enrich (bounded)    — code: fetch detail URLs of accepted items
         stage 6  write + publish     — Claude call → trilingual copy (schema-
                                        enforced), Pydantic + URL gate, put_item
         stage 7  report              — code: email built from in-memory RunReport,
                                        PIPELINE_RUN row w/ run_id, SNS publish
   └─► pipeline-canary Lambda (Sun 03:00) — alert if no fresh PIPELINE_RUN row
```

- Same skeleton runs `omraadet` monthly with an audit-stage config instead of discovery.
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
- Whether each candidate meets the editorial bar (judge — the excellent rubric in
  `BASE_SYSTEM.md` moves here, verbatim where possible).
- The trilingual copy (write — tone/translation/SEO rules move here).

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

Kept: prompts' editorial content (split into three stage prompts), source registry
(becomes a plain data module), DynamoDB table + single-table design, SNS topic +
subscription + alarms (retargeted), EventBridge schedules, the entire RPC backend and
frontend (untouched).

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

## 6. Migration plan

1. **Phase 0 — stop the bleeding (independent of refactor):** one-off script backfills
   `event_start`/`event_end` and archives expired posts. Site is correct again.
2. **Phase 1 — build:** `backend/pipelines/content/` with stages as pure functions +
   pytest per layer (mock httpx/bedrock/dynamodb at edges).
3. **Phase 2 — infra swap:** new pipeline + canary functions in `template.yaml`;
   retarget schedules and alarms; SerpAPI key to SSM.
4. **Phase 3 — delete:** agentcore_runtimes/, invoker, notifier, validator, queues,
   deploy.yml agent packaging.
5. **Phase 4 — verify:** manual invoke of both pipelines against prod table; confirm
   email, site state, canary; then leave schedules on.
