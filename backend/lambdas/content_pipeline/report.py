"""Run report: email + PIPELINE_RUN row, built from actual in-memory run state.

No snapshots, no diffing, no cross-run correlation — the report describes the
run that just happened, by construction.
"""
from __future__ import annotations

from datetime import datetime, timezone

from stages import RunState, events_next_14d

SEP = "━" * 40


def format_email(state: RunState) -> tuple[str, str]:
    lines = [
        SEP,
        f"AALUMVEJ26 — {state.pipeline.title()} Pipeline",
        f"{datetime.now(timezone.utc).isoformat()[:16].replace('T', ' ')} UTC · run {state.run_id}",
        SEP, "",
    ]

    if state.error:
        lines += [f"⚠ RUN FAILED: {state.error}",
                  "Results below are partial — the run stopped at the error.", ""]

    if state.published:
        lines.append(f"PUBLISHED ({len(state.published)})")
        lines += [f"  [{p['category']}] {p['title']} — {p['date']}" for p in state.published]
        lines.append("")
    if state.archived:
        lines.append(f"ARCHIVED ({len(state.archived)})")
        lines += [f"  {a['title']} (ended {a['event_end']})" for a in state.archived]
        lines.append("")
    if state.updated_areas:
        lines.append(f"UPDATED AREAS ({len(state.updated_areas)})")
        lines += [f"  {u['name']} — {u['verdict']}: {u['reason']}" for u in state.updated_areas]
        lines.append("")
    if not (state.published or state.archived or state.updated_areas or state.error):
        lines += ["No content changes.", ""]

    if state.new_sources:
        lines.append(f"NEW SOURCES ({len(state.new_sources)}, on probation)")
        lines += [f"  tier {s.tier} · {s.domain} — {s.notes}" for s in state.new_sources]
        lines.append("")
    if state.suggested_sources:
        lines.append(f"SUGGESTED SOURCES ({len(state.suggested_sources)}, not added — your call)")
        lines += [f"  tier {v.tier} · {v.domain} ({v.confidence}) — {v.reasoning}"
                  for v in state.suggested_sources]
        lines.append("")
    if state.retired_sources:
        lines.append(f"RETIRED SOURCES ({len(state.retired_sources)})")
        lines += [f"  {s}" for s in state.retired_sources]
        lines.append("")
    if state.promoted_sources:
        lines.append(f"PROMOTED TO ACTIVE: {', '.join(state.promoted_sources)}")
        lines.append("")
    if state.area_recommendations:
        lines.append("NEW AREA CARD RECOMMENDATIONS")
        lines += [f"  {r}" for r in state.area_recommendations]
        lines.append("")

    failed = sorted({r.domain for r in state.crawl_results if not r.ok})
    lines.append("CRAWL STATS")
    lines.append(f"  Pages fetched:     {sum(1 for r in state.crawl_results if r.ok)}"
                 f" ok / {len(state.crawl_results)} attempted")
    lines.append(f"  Failed domains:    {len(failed)}"
                 + (f" ({', '.join(failed)})" if failed else ""))
    lines.append(f"  Searches run:      {state.searches_run} (provider: {state.search_used})")
    lines.append(f"  Candidates found:  {state.candidates_found}")
    if state.rejections:
        parts = [f"{v} {k}" for k, v in sorted(state.rejections.items()) if v]
        lines.append(f"  Rejected:          {sum(state.rejections.values())} ({', '.join(parts)})")
    lines.append("")

    published_now = [p for p in state.posts if p.get("status") == "published"]
    lines.append("CONTENT STATUS")
    lines.append(f"  Published posts:   {len(published_now) + len(state.published)}")
    lines.append(f"  Areas:             {len(state.areas)}")
    lines.append(f"  Events next 14d:   {events_next_14d(state.posts, state.today)}")
    lines.append("")

    if state.notes:
        lines.append("NOTES")
        lines += [f"  {n}" for n in state.notes]
        lines.append("")

    lines.append(SEP)

    parts = []
    if state.published:
        parts.append(f"{len(state.published)} new")
    if state.archived:
        parts.append(f"{len(state.archived)} archived")
    if state.updated_areas:
        parts.append(f"{len(state.updated_areas)} areas updated")
    if state.new_sources:
        parts.append(f"{len(state.new_sources)} new sources")
    if not parts:
        parts.append("no changes")
    prefix = "FAILED — " if state.error else ""
    subject = f"[aalumvej26] {state.pipeline}: {prefix}{', '.join(parts)}"
    return subject, "\n".join(lines)


def save_run_row(state: RunState, table) -> None:
    now = datetime.now(timezone.utc).isoformat()
    table.put_item(Item={
        "pk": "PIPELINE_RUN",
        "sk": f"{state.pipeline}#{now}",
        "pipeline": state.pipeline,
        "run_id": state.run_id,
        "timestamp": now,
        "sources_searched": len(state.crawl_results),
        "sources_failed": sorted({r.domain for r in state.crawl_results if not r.ok}),
        "candidates_found": state.candidates_found,
        "published": len(state.published),
        "archived": len(state.archived),
        "rejections": state.rejections,
        "events_next_14d": events_next_14d(state.posts, state.today),
        "new_sources": [s.domain for s in state.new_sources],
        "retired_sources": state.retired_sources,
        "error": state.error or "",
        "notes": "\n".join(state.notes),
    })
