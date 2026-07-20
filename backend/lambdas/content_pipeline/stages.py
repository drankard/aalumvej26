"""Pipeline stages. Each stage is a function over RunState with injected deps.

Determinism policy: everything mechanical (archival, dedup, caps, health,
thresholds, reporting) is code here; the LLM is consulted exactly at extract,
source-judge, judge, write, and area-audit.
"""
from __future__ import annotations

import difflib
import logging
import os
import re
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from string import Template
from urllib.parse import urlparse

import registry as reg
from crawler import crawl, validate_url
from llm import call_structured
from schemas import (
    AreaAuditResult, CandidateEvent, CrawlResult, ExtractResult, JudgeResult,
    Judgment, Source, SourceJudgeResult, SourceVerdict, WriteResult,
)
from seeds import SEED_SOURCES

logger = logging.getLogger(__name__)

PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")

MAX_PUBLISH_PER_RUN = 8
MAX_CANDIDATES = 40
TOO_FAR_FUTURE_DAYS = 60
DUPLICATE_RATIO = 0.82
EXTRACT_PAGES_PER_CALL = 12
WRITE_POSTS_PER_CALL = 4
MAX_NEW_DOMAINS_JUDGED = 6


@dataclass
class RunState:
    pipeline: str
    today: date
    season: str
    model_id: str
    run_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    # loaded
    sources: list[Source] = field(default_factory=list)
    posts: list[dict] = field(default_factory=list)
    areas: list[dict] = field(default_factory=list)
    seeded: int = 0
    # accumulators
    crawl_results: list[CrawlResult] = field(default_factory=list)
    candidates: list[CandidateEvent] = field(default_factory=list)
    judgments: list[Judgment] = field(default_factory=list)
    published: list[dict] = field(default_factory=list)
    archived: list[dict] = field(default_factory=list)
    updated_areas: list[dict] = field(default_factory=list)
    new_sources: list[Source] = field(default_factory=list)
    suggested_sources: list[SourceVerdict] = field(default_factory=list)
    retired_sources: list[str] = field(default_factory=list)
    promoted_sources: list[str] = field(default_factory=list)
    rejections: dict = field(default_factory=dict)
    area_recommendations: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    search_used: str = "none"
    searches_run: int = 0
    error: str | None = None

    def reject(self, key: str, n: int = 1) -> None:
        self.rejections[key] = self.rejections.get(key, 0) + n


def load_prompt(name: str, **vars) -> str:
    with open(os.path.join(PROMPTS_DIR, name)) as f:
        raw = f.read()
    safe = {k: str(v).replace("$", "$$") for k, v in vars.items()}
    return Template(raw).safe_substitute(safe)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _norm_title(t: str) -> str:
    return re.sub(r"[^\wæøå ]", "", t.lower()).strip()


def _published_posts(state: RunState) -> list[dict]:
    return [p for p in state.posts if p.get("status") == "published"]


def _existing_posts_block(state: RunState) -> str:
    lines = []
    for p in _published_posts(state):
        da = p.get("translations", {}).get("da", {})
        lines.append(f"- {da.get('title', '')} | {da.get('date', '')} | {p.get('url', '')}")
    return "\n".join(lines) or "(none)"


# ---------- stages ----------

def stage_load(state: RunState, table) -> None:
    state.seeded = reg.seed_if_empty(table, SEED_SOURCES)
    if state.seeded:
        state.notes.append(f"Source registry seeded with {state.seeded} sources.")
    state.sources = reg.load_sources(table)

    items, resp = [], table.query(
        KeyConditionExpression="pk = :pk", ExpressionAttributeValues={":pk": "POST"})
    items.extend(resp.get("Items", []))
    while "LastEvaluatedKey" in resp:
        resp = table.query(KeyConditionExpression="pk = :pk",
                           ExpressionAttributeValues={":pk": "POST"},
                           ExclusiveStartKey=resp["LastEvaluatedKey"])
        items.extend(resp.get("Items", []))
    state.posts = items

    resp = table.query(KeyConditionExpression="pk = :pk",
                       ExpressionAttributeValues={":pk": "AREA"})
    state.areas = [a for a in resp.get("Items", []) if a.get("status") == "published"]


def plan_expired(posts: list[dict], today: date) -> list[dict]:
    """Pure: published posts whose event_end has passed."""
    out = []
    for p in posts:
        if p.get("status") != "published":
            continue
        end = p.get("event_end")
        if end:
            try:
                if date.fromisoformat(end) < today:
                    out.append(p)
            except ValueError:
                continue
    return out


def stage_archive_expired(state: RunState, table) -> None:
    unstamped = [p for p in _published_posts(state) if "event_end" not in p]
    if unstamped:
        state.notes.append(
            f"{len(unstamped)} published posts lack event dates (backfill not run?) — not archivable.")
    now = _now_iso()
    for p in plan_expired(state.posts, state.today):
        table.update_item(
            Key={"pk": "POST", "sk": p["sk"]},
            UpdateExpression="SET #s = :s, updated_at = :u",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={":s": "archived", ":u": now},
        )
        p["status"] = "archived"
        title = p.get("translations", {}).get("da", {}).get("title", "?")
        state.archived.append({"id": p.get("id", "?"), "title": title,
                               "event_end": p.get("event_end")})


def stage_crawl(state: RunState, table, time_left=lambda: 300.0) -> None:
    targets = [(s.domain, s.url) for s in reg.crawlable(state.sources)
               if s.tier in (1, 2, 4) and s.url]
    state.crawl_results = crawl(targets, time_left=time_left)

    ok_by_domain = {}
    for r in state.crawl_results:
        if "time budget" in (r.error or ""):
            continue  # not the source's fault — don't count against health
        ok_by_domain[r.domain] = ok_by_domain.get(r.domain, False) or r.ok

    updated = []
    for s in state.sources:
        if s.domain in ok_by_domain:
            new = reg.apply_fetch_outcome(s, ok_by_domain[s.domain])
            if new.status == "retired" and s.status != "retired":
                state.retired_sources.append(
                    f"{new.domain} ({new.consecutive_failures} consecutive failed runs)")
            reg.save_source(table, new)
            updated.append(new)
        else:
            updated.append(s)
    state.sources = updated


def stage_discover_sources(state: RunState, table, provider, bedrock, time_left=lambda: 120.0) -> None:
    state.search_used = provider.name
    if provider.name == "none":
        state.notes.append("Search disabled/unavailable — source discovery skipped this run.")
        return

    published = _published_posts(state)
    counts: dict[str, int] = {}
    for p in published:
        counts[p.get("category", "?")] = counts.get(p.get("category", "?"), 0) + 1
    gaps = sorted(("natur", "kultur", "mad", "surf", "born"), key=lambda c: counts.get(c, 0))

    from search import build_queries
    hits = []
    for q in build_queries(state.season, list(gaps)):
        hits.extend(provider.search(q))
        state.searches_run += 1

    known = reg.known_domains(state.sources)
    fresh: dict[str, str] = {}
    for h in hits:
        d = urlparse(h.url).netloc.removeprefix("www.")
        if d and d not in known and d not in fresh and not d.endswith(
                (".facebook.com", "facebook.com", "instagram.com", "booking.com", "tripadvisor.com")):
            fresh[d] = f"https://{d}/"
        if len(fresh) >= MAX_NEW_DOMAINS_JUDGED:
            break
    if not fresh:
        return

    pages = crawl(list(fresh.items()), time_left=time_left)
    reachable = [p for p in pages if p.ok and p.text]
    for p in pages:
        if not p.ok:
            state.notes.append(f"Discovery candidate {p.domain} unreachable ({p.error}) — not judged.")
    if not reachable:
        return

    registry_block = "\n".join(f"- {s.domain} ({s.name}, tier {s.tier}, {s.status})"
                               for s in state.sources)
    cand_block = "\n\n".join(f"### {p.domain}\nURL: {p.url}\n{p.text[:3000]}" for p in reachable)
    prompt = load_prompt("source_judge.md", current_date=state.today.isoformat(),
                         registry=registry_block, candidates=cand_block)
    result = call_structured(bedrock, state.model_id, prompt, SourceJudgeResult,
                             tool_name="record_verdicts")

    added = 0
    for v in result.verdicts:
        if not v.relevant:
            continue
        if v.confidence != "high":
            state.suggested_sources.append(v)
            continue
        ok, reason = reg.can_add_source(state.sources, added)
        if not ok:
            state.suggested_sources.append(v)
            state.notes.append(f"Not auto-adding {v.domain}: {reason}")
            continue
        src = Source(domain=v.domain, name=v.suggested_name or v.domain,
                     url=fresh.get(v.domain, f"https://{v.domain}/"), tier=v.tier,
                     type=v.type, notes=v.reasoning, status="probation",
                     discovered_by="search", added_at=_now_iso())
        reg.save_source(table, src)
        state.sources.append(src)
        state.new_sources.append(src)
        added += 1
        page = next((p for p in reachable if p.domain == v.domain), None)
        if page:
            state.crawl_results.append(page)  # new source contributes content this run


def stage_extract(state: RunState, bedrock) -> None:
    pages = [r for r in state.crawl_results if r.ok and r.text]
    existing = _existing_posts_block(state)
    for i in range(0, len(pages), EXTRACT_PAGES_PER_CALL):
        batch = pages[i:i + EXTRACT_PAGES_PER_CALL]
        block = "\n\n".join(f"### PAGE url={p.url} domain={p.domain}\n{p.text}" for p in batch)
        prompt = load_prompt("extract.md", current_date=state.today.isoformat(),
                             season=state.season, existing_posts=existing, pages=block)
        result = call_structured(bedrock, state.model_id, prompt, ExtractResult,
                                 tool_name="record_candidates", max_tokens=16384)
        state.candidates.extend(result.candidates)
        if len(state.candidates) >= MAX_CANDIDATES:
            state.notes.append(f"Candidate cap ({MAX_CANDIDATES}) reached — remaining pages not extracted.")
            state.candidates = state.candidates[:MAX_CANDIDATES]
            break


def filter_candidates(candidates: list[CandidateEvent], published: list[dict], today: date
                      ) -> tuple[list[CandidateEvent], dict]:
    """Pure code filter: expired, too-far-future, duplicates (title-sim or URL)."""
    rejections: dict[str, int] = {}
    existing_titles = [_norm_title(p.get("translations", {}).get("da", {}).get("title", ""))
                       for p in published]
    existing_urls = {p.get("url", "") for p in published}
    kept: list[CandidateEvent] = []
    seen_titles: list[str] = []

    def _reject(key: str) -> None:
        rejections[key] = rejections.get(key, 0) + 1

    for c in candidates:
        if c.event_end:
            try:
                if date.fromisoformat(c.event_end) < today:
                    _reject("expired")
                    continue
            except ValueError:
                _reject("invalid_dates")
                continue
        if c.event_start and not c.evergreen:
            try:
                if date.fromisoformat(c.event_start) > today + timedelta(days=TOO_FAR_FUTURE_DAYS):
                    _reject("too_far_future")
                    continue
            except ValueError:
                _reject("invalid_dates")
                continue
        norm = _norm_title(c.title)
        if c.source_url in existing_urls or any(
                difflib.SequenceMatcher(None, norm, t).ratio() > DUPLICATE_RATIO
                for t in existing_titles + seen_titles):
            _reject("duplicate")
            continue
        seen_titles.append(norm)
        kept.append(c)
    return kept, rejections


def stage_filter(state: RunState) -> None:
    kept, rejections = filter_candidates(state.candidates, _published_posts(state), state.today)
    for k, v in rejections.items():
        state.reject(k, v)
    state.candidates = kept


def stage_judge(state: RunState, bedrock) -> None:
    if not state.candidates:
        return
    closed = "; ".join(reg.closed_names(state.sources)) or "(none)"
    cand_block = "\n".join(
        f"- title={c.title!r} dates={c.event_start}..{c.event_end} evergreen={c.evergreen} "
        f"location={c.location!r} category={c.category} url={c.source_url} details={c.details!r}"
        for c in state.candidates)
    prompt = load_prompt("judge.md", current_date=state.today.isoformat(), season=state.season,
                         closed_list=closed, existing_posts=_existing_posts_block(state),
                         candidates=cand_block)
    result = call_structured(bedrock, state.model_id, prompt, JudgeResult,
                             tool_name="record_judgments", max_tokens=16384)
    state.judgments = result.judgments
    for j in result.judgments:
        if not j.accept:
            state.reject(j.rejection_key or "not_relevant")


def accepted_candidates(state: RunState) -> list[tuple[CandidateEvent, Judgment]]:
    """Accepted candidates paired with judgments, best first, capped."""
    by_title = {_norm_title(c.title): c for c in state.candidates}
    pairs = []
    for j in sorted(state.judgments, key=lambda j: -j.score):
        if not j.accept:
            continue
        c = by_title.get(_norm_title(j.title))
        if c:
            pairs.append((c, j))
    dropped = len(pairs) - MAX_PUBLISH_PER_RUN
    if dropped > 0:
        pairs = pairs[:MAX_PUBLISH_PER_RUN]
    return pairs


def stage_write_publish(state: RunState, table, bedrock, url_checker=validate_url) -> None:
    pairs = accepted_candidates(state)
    if len(pairs) < sum(1 for j in state.judgments if j.accept):
        state.notes.append(f"Publish cap ({MAX_PUBLISH_PER_RUN}) applied — lowest-scored accepted items dropped.")
    if not pairs:
        return

    now = _now_iso()
    rank = 0
    for i in range(0, len(pairs), WRITE_POSTS_PER_CALL):
        batch = pairs[i:i + WRITE_POSTS_PER_CALL]
        block = "\n".join(
            f"- title={c.title!r} category={c.category} dates={c.event_start}..{c.event_end} "
            f"evergreen={c.evergreen} location={c.location!r} url={c.source_url} "
            f"score={j.score} details={c.details!r}"
            for c, j in batch)
        prompt = load_prompt("write.md", current_date=state.today.isoformat(),
                             season=state.season, accepted=block)
        result = call_structured(bedrock, state.model_id, prompt, WriteResult,
                                 tool_name="record_posts", max_tokens=32768)

        for copy in result.posts:
            if not url_checker(copy.url):
                state.reject("dead_url")
                state.notes.append(f"Not published (dead URL): {copy.translations.da.title}")
                continue
            rank += 1
            post_id = str(uuid.uuid4())
            table.put_item(Item={
                "pk": "POST", "sk": f"POST#{post_id}", "id": post_id,
                "category": copy.category, "tag_key": copy.tag_key, "url": copy.url,
                "emoji": copy.emoji, "sort_order": rank, "status": "published",
                "relevance_score": 0, "source_urls": [copy.url],
                "event_start": copy.event_start, "event_end": copy.event_end,
                "run_id": state.run_id,
                "translations": copy.translations.model_dump(),
                "created_at": now, "updated_at": now,
            })
            domain = urlparse(copy.url).netloc.removeprefix("www.")
            state.published.append({"id": post_id, "title": copy.translations.da.title,
                                    "category": copy.category, "date": copy.translations.da.date,
                                    "domain": domain})


def stage_source_lifecycle(state: RunState, table) -> None:
    productive = {p["domain"] for p in state.published if p.get("domain")}
    for i, s in enumerate(state.sources):
        new = reg.promote_if_productive(s, productive)
        if new.status != s.status:
            reg.save_source(table, new)
            state.sources[i] = new
            state.promoted_sources.append(new.domain)


# ---------- omraadet ----------

def stage_area_audit(state: RunState, table, bedrock, time_left=lambda: 240.0) -> None:
    if not state.areas:
        state.notes.append("No published area cards found.")
        return
    targets = []
    for a in state.areas:
        domain = urlparse(a.get("url", "")).netloc.removeprefix("www.") or a.get("id", "?")
        targets.append((domain, a.get("url", "")))
    results = {r.url: r for r in crawl(targets, time_left=time_left)}

    blocks = []
    for a in state.areas:
        r = results.get(a.get("url", ""))
        fetched = r.text if (r and r.ok) else f"FETCH FAILED: {r.error if r else 'no url'}"
        da = a.get("translations", {}).get("da", {})
        blocks.append(f"### area_id={a['id']}\nname={da.get('name')} dist={da.get('dist')} "
                      f"desc={da.get('desc')}\nurl={a.get('url')}\nFETCHED:\n{fetched[:2500]}")
    recent = "\n".join(f"- {p.get('translations', {}).get('da', {}).get('title', '')}"
                       for p in _published_posts(state)[:40])

    prompt = load_prompt("area_audit.md", current_date=state.today.isoformat(),
                         season=state.season, cards="\n\n".join(blocks), recent_posts=recent)
    result = call_structured(bedrock, state.model_id, prompt, AreaAuditResult,
                             tool_name="record_audits", max_tokens=16384)

    now = _now_iso()
    by_id = {a["id"]: a for a in state.areas}
    for audit in result.audits:
        area = by_id.get(audit.area_id)
        if area is None:
            continue
        if audit.verdict in ("minor_update", "major_update") and audit.translations:
            langs = set(audit.translations.keys())
            if langs != {"da", "en", "de"}:
                state.notes.append(f"Area {audit.area_id}: update skipped, incomplete languages {langs}.")
                continue
            parts = ["translations = :t", "updated_at = :u"]
            vals = {":t": audit.translations, ":u": now}
            if audit.url:
                parts.append("#u = :url")
            expr_names = {"#u": "url"} if audit.url else None
            if audit.url:
                vals[":url"] = audit.url
            kwargs = dict(Key={"pk": "AREA", "sk": f"AREA#{audit.area_id}"},
                          UpdateExpression="SET " + ", ".join(parts),
                          ExpressionAttributeValues=vals)
            if expr_names:
                kwargs["ExpressionAttributeNames"] = expr_names
            table.update_item(**kwargs)
            name = area.get("translations", {}).get("da", {}).get("name", "?")
            state.updated_areas.append({"id": audit.area_id, "name": name,
                                        "verdict": audit.verdict, "reason": audit.reasoning})
        elif audit.verdict == "broken_link":
            name = area.get("translations", {}).get("da", {}).get("name", "?")
            state.notes.append(f"BROKEN LINK on area card '{name}': {area.get('url')} — "
                               f"{audit.reasoning}" + (f" Suggested: {audit.url}" if audit.url else ""))
    state.area_recommendations = result.new_card_recommendations


def events_next_14d(posts: list[dict], today: date) -> int:
    """Published events starting within 14 days or ongoing today."""
    horizon = today + timedelta(days=14)
    n = 0
    for p in posts:
        if p.get("status") != "published":
            continue
        start, end = p.get("event_start"), p.get("event_end")
        try:
            s = date.fromisoformat(start) if start else None
            e = date.fromisoformat(end) if end else None
        except ValueError:
            continue
        if s and today <= s <= horizon:
            n += 1
        elif s and e and s <= today <= e:
            n += 1
    return n
