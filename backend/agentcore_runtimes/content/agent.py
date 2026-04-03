"""
Aalumvej26 Content Agent — AgentCore Runtime

Stateless agent that discovers and writes content for the vacation rental site.
Two pipelines: oplevelser (events/activities) and omraadet (area reference cards).
Prompts composed from Bedrock Prompt Manager: BASE_SYSTEM + pipeline-specific prompt.
"""
import json
import logging
import os
from datetime import datetime, timezone

import boto3
from bedrock_agentcore import BedrockAgentCoreApp
from botocore.config import Config as BotocoreConfig
from strands import Agent
from strands.models import BedrockModel
from strands.agent.conversation_manager.sliding_window_conversation_manager import SlidingWindowConversationManager
from strands.hooks.events import AfterToolCallEvent, BeforeModelCallEvent
from strands.hooks.registry import HookRegistry

from config import ConfigService
from prompt_service import PromptService
from tools.web_search import search, reset as reset_search
from tools.web_fetch import fetch_content, reset as reset_fetch
from tools.content_db import (
    list_published_posts, list_published_areas, create_post,
    archive_post, update_area, save_run_summary,
)
from tools.url_validator import validate_url
from tools.source_registry import get_sources

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

TOOL_CALL_SOFT_LIMIT = 20


class RunStatsHook:
    """Tracks tool call stats for the run summary fallback."""

    def __init__(self, pipeline: str):
        self.pipeline = pipeline
        self.tool_call_count = 0
        self.published = 0
        self.archived = 0
        self.searches = 0
        self.fetches = 0
        self.summary_written = False
        self._soft_warned = False

    def register_hooks(self, registry: HookRegistry):
        registry.add_callback(AfterToolCallEvent, self._on_after_tool_call)
        registry.add_callback(BeforeModelCallEvent, self._on_before_model_call)

    def _on_after_tool_call(self, event: AfterToolCallEvent):
        self.tool_call_count += 1
        tool_name = event.tool_use.get("name", "unknown") if hasattr(event, "tool_use") else "unknown"
        logger.info(f"Tool call #{self.tool_call_count}: {tool_name}")

        if tool_name == "create_post":
            self.published += 1
        elif tool_name == "archive_post":
            self.archived += 1
        elif tool_name == "search":
            self.searches += 1
        elif tool_name == "fetch_content":
            self.fetches += 1
        elif tool_name == "save_run_summary":
            self.summary_written = True

    def _on_before_model_call(self, event: BeforeModelCallEvent):
        if self.tool_call_count >= TOOL_CALL_SOFT_LIMIT and not self._soft_warned:
            self._soft_warned = True
            logger.info(f"Soft limit reached ({self.tool_call_count} tool calls).")

    def write_fallback_summary(self):
        if self.summary_written:
            return
        logger.info("Writing fallback run summary.")
        try:
            table_name = os.environ.get("TABLE_NAME", "aalumvej26-prod")
            region = os.environ.get("AWS_REGION", "eu-west-1")
            table = boto3.resource("dynamodb", region_name=region).Table(table_name)
            now = datetime.now(timezone.utc).isoformat()
            table.put_item(Item={
                "pk": "PIPELINE_RUN",
                "sk": f"{self.pipeline}#{now}",
                "pipeline": self.pipeline,
                "timestamp": now,
                "sources_searched": self.searches + self.fetches,
                "sources_failed": [],
                "candidates_found": 0,
                "published": self.published,
                "archived": self.archived,
                "rejections": {},
                "events_next_14d": 0,
                "notes": (
                    f"Fallback summary — agent ended before calling save_run_summary. "
                    f"Tool calls: {self.tool_call_count}, searches: {self.searches}, "
                    f"fetches: {self.fetches}."
                ),
            })
            logger.info(f"Fallback run summary written: pipeline={self.pipeline}")
        except Exception as e:
            logger.error(f"Fallback summary write failed: {e}")

    def invoke_notifier(self):
        notifier_arn = os.environ.get("NOTIFIER_FUNCTION_ARN", "")
        if not notifier_arn:
            return
        try:
            boto3.client("lambda").invoke(
                FunctionName=notifier_arn,
                InvocationType="Event",
                Payload=json.dumps({"pipeline": self.pipeline}),
            )
            logger.info(f"Notifier invoked: pipeline={self.pipeline}")
        except Exception as e:
            logger.warning(f"Failed to invoke notifier: {e}")


app = BedrockAgentCoreApp()

config = ConfigService()
config.validate()

prompt_service = PromptService(region=config.aws_region)

bedrock_model = BedrockModel(
    model_id=config.get_model_id(),
    streaming=True,
    max_tokens=65536,
    boto_client_config=BotocoreConfig(
        read_timeout=300,
        retries={"max_attempts": 3, "mode": "adaptive"},
    ),
)

TOOLS = [
    search, fetch_content, list_published_posts, list_published_areas,
    create_post, archive_post, update_area, validate_url, save_run_summary,
    get_sources,
]


@app.entrypoint
async def invoke(payload, context):
    pipeline = payload.get("pipeline", "oplevelser")
    context_vars = payload.get("context_vars", {})
    logger.info(f"Content agent invoked: pipeline={pipeline}")

    reset_search()
    reset_fetch()

    system_prompt = prompt_service.build_system_prompt(
        pipeline=pipeline,
        context_vars=context_vars,
    )

    stats = RunStatsHook(pipeline)

    agent = Agent(
        name=config.agent_name,
        model=bedrock_model,
        system_prompt=system_prompt,
        tools=TOOLS,
        hooks=[stats],
        conversation_manager=SlidingWindowConversationManager(window_size=10),
    )

    user_message = (
        "Execute the content pipeline now. Be concise — no verbose reasoning. "
        "Search, evaluate internally, then publish. "
        "IMPORTANT: Call create_post ONE AT A TIME — never batch multiple create_post "
        "calls in a single response. After each create_post, wait for confirmation "
        "before the next. Call save_run_summary as your last action."
    )

    try:
        stream = agent.stream_async(user_message)
        async for event in stream:
            yield event
        logger.info(f"Agent completed: pipeline={pipeline}, tools={stats.tool_call_count}")
    except Exception as e:
        logger.error(f"Agent failed: {type(e).__name__}: {e}", exc_info=True)
        yield {"type": "error", "message": f"Content agent failed: {str(e)}"}
    finally:
        stats.write_fallback_summary()
        stats.invoke_notifier()


if __name__ == "__main__":
    logger.info(f"Starting {config.agent_name}")
    logger.info(f"  Model: {config.get_model_id()}")
    logger.info(f"  Region: {config.aws_region}")
    app.run()
