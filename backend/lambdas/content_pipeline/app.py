"""Content pipeline Lambda entrypoint.

One synchronous run per invocation: EventBridge → this function → email.
The report ALWAYS goes out (success, partial, or failure) and the run row is
always written; an unhandled error is re-raised after reporting so the Lambda
Errors metric and alarm still fire. No silent outcomes.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

import boto3

import report as report_mod
import stages as st
from search import get_provider

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Reserve this much time (ms) before the Lambda deadline for write+report.
RESERVE_MS = 90_000


def _season(month: int) -> str:
    return {3: "spring", 4: "spring", 5: "spring", 6: "summer", 7: "summer", 8: "summer",
            9: "autumn", 10: "autumn", 11: "autumn"}.get(month, "winter")


def _model_id(session) -> str:
    if os.environ.get("MODEL_ID"):
        return os.environ["MODEL_ID"]
    param = os.environ.get("MODEL_ID_PARAM", "/aalumvej26/ai/model-id")
    return session.client("ssm").get_parameter(Name=param)["Parameter"]["Value"]


def lambda_handler(event: dict, context) -> dict:
    pipeline = event.get("pipeline", "oplevelser")
    session = boto3.Session()
    table = session.resource("dynamodb").Table(os.environ.get("TABLE_NAME", "aalumvej26-prod"))
    bedrock = session.client("bedrock-runtime")
    now = datetime.now(timezone.utc)

    state = st.RunState(pipeline=pipeline, today=now.date(), season=_season(now.month),
                        model_id=_model_id(session))
    logger.info(f"Pipeline start: {pipeline} run_id={state.run_id} model={state.model_id}")

    def ms_left() -> float:
        try:
            return context.get_remaining_time_in_millis()
        except Exception:
            return 900_000.0

    def secs_for(share: float) -> float:
        return max(0.0, (ms_left() - RESERVE_MS) / 1000.0) * share

    def budget_ok(stage_name: str) -> bool:
        if ms_left() <= RESERVE_MS:
            state.notes.append(f"Time budget exhausted before {stage_name} — stage skipped.")
            return False
        return True

    try:
        st.stage_load(state, table)
        st.stage_archive_expired(state, table)

        if pipeline == "omraadet":
            if budget_ok("area audit"):
                st.stage_area_audit(state, table, bedrock,
                                    time_left=lambda: secs_for(0.5))
            provider = get_provider()
            if budget_ok("source discovery"):
                st.stage_discover_sources(state, table, provider, bedrock,
                                          time_left=lambda: secs_for(0.3))
        else:
            if budget_ok("crawl"):
                st.stage_crawl(state, table, time_left=lambda: secs_for(0.4))
            provider = get_provider()
            if budget_ok("source discovery"):
                st.stage_discover_sources(state, table, provider, bedrock,
                                          time_left=lambda: secs_for(0.3))
            if budget_ok("extract"):
                st.stage_extract(state, bedrock)
            st.stage_filter(state)
            if budget_ok("judge"):
                st.stage_judge(state, bedrock)
            if budget_ok("write+publish"):
                st.stage_write_publish(state, table, bedrock)
            st.stage_source_lifecycle(state, table)

    except Exception as e:
        logger.error(f"Pipeline failed: {type(e).__name__}: {e}", exc_info=True)
        state.error = f"{type(e).__name__}: {e}"
        _report(state, table, session)
        raise  # Errors metric + alarm must fire

    _report(state, table, session)
    logger.info(f"Pipeline done: {pipeline} published={len(state.published)} "
                f"archived={len(state.archived)} new_sources={len(state.new_sources)}")
    return {"pipeline": pipeline, "run_id": state.run_id,
            "published": len(state.published), "archived": len(state.archived)}


def _report(state: st.RunState, table, session) -> None:
    try:
        report_mod.save_run_row(state, table)
    except Exception as e:  # never let reporting kill the report
        logger.error(f"Failed to save run row: {e}")
    topic = os.environ.get("SNS_TOPIC_ARN", "")
    if not topic:
        logger.warning("SNS_TOPIC_ARN not set — no email sent")
        return
    try:
        subject, body = report_mod.format_email(state)
        session.client("sns").publish(TopicArn=topic, Subject=subject[:100], Message=body)
        logger.info(f"Report sent: {subject}")
    except Exception as e:
        logger.error(f"Failed to send report: {e}")
