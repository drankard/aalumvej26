"""
Aalumvej26 Content Agent — AgentCore Runtime

Stateless agent that discovers and writes content for the vacation rental site.
Two pipelines: oplevelser (events/activities) and omraadet (area reference cards).
Prompts composed from Bedrock Prompt Manager: BASE_SYSTEM + pipeline-specific prompt.
Web search via DuckDuckGo (free, no API key).
"""
import logging
import os

from bedrock_agentcore import BedrockAgentCoreApp
from botocore.config import Config as BotocoreConfig
from strands import Agent
from strands.models import BedrockModel
from strands.hooks.events import AfterToolCallEvent, BeforeModelCallEvent
from strands.hooks.registry import HookRegistry

from config import ConfigService
from prompt_service import PromptService
from tools.web_search import search
from tools.web_fetch import fetch_content
from tools.content_db import list_published_posts, list_published_areas, create_post, archive_post, update_area, save_run_summary
from tools.url_validator import validate_url

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

TOOL_CALL_SOFT_LIMIT = 20
TOOL_CALL_HARD_LIMIT = 40


class BudgetHookProvider:
    """Tracks tool call count and nudges the agent to wrap up before hitting limits."""

    def __init__(self):
        self.tool_call_count = 0
        self.warned = False

    def register_hooks(self, registry: HookRegistry):
        registry.add_callback(AfterToolCallEvent, self._on_after_tool_call)
        registry.add_callback(BeforeModelCallEvent, self._on_before_model_call)

    def _on_after_tool_call(self, event: AfterToolCallEvent):
        self.tool_call_count += 1
        tool_name = event.tool_use.get("name", "unknown") if hasattr(event, "tool_use") else "unknown"
        logger.info(f"Tool call #{self.tool_call_count}: {tool_name}")

    def _on_before_model_call(self, event: BeforeModelCallEvent):
        if self.tool_call_count >= TOOL_CALL_HARD_LIMIT:
            logger.warning(f"Hard limit reached ({self.tool_call_count} tool calls). Injecting stop instruction.")
            event.agent.messages.append({
                "role": "user",
                "content": [{
                    "text": (
                        "URGENT: You have used all your tool call budget. "
                        "Call save_run_summary NOW with what you have, then stop. "
                        "Do NOT make any more search or fetch calls."
                    )
                }],
            })
        elif self.tool_call_count >= TOOL_CALL_SOFT_LIMIT and not self.warned:
            self.warned = True
            logger.info(f"Soft limit reached ({self.tool_call_count} tool calls). Nudging agent to wrap up.")
            event.agent.messages.append({
                "role": "user",
                "content": [{
                    "text": (
                        f"BUDGET WARNING: You have used {self.tool_call_count} of {TOOL_CALL_HARD_LIMIT} tool calls. "
                        "Stop searching now. Evaluate what you have, publish the best candidates, "
                        "and call save_run_summary. You have limited tool calls remaining."
                    )
                }],
            })


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
        retries={"max_attempts": 0},
    ),
)

TOOLS = [search, fetch_content, list_published_posts, list_published_areas, create_post, archive_post, update_area, validate_url, save_run_summary]


@app.entrypoint
async def invoke(payload, context):
    """
    AgentCore Runtime entrypoint.

    Payload:
        pipeline: "oplevelser" | "omraadet"
        context_vars: optional dict of runtime context variables
    """
    try:
        pipeline = payload.get("pipeline", "oplevelser")
        context_vars = payload.get("context_vars", {})

        logger.info(f"Content agent invoked: pipeline={pipeline}")

        system_prompt = prompt_service.build_system_prompt(
            pipeline=pipeline,
            base_prompt_arn=config.base_prompt_id,
            pipeline_prompt_arn=(
                config.oplevelser_prompt_id if pipeline == "oplevelser"
                else config.omraadet_prompt_id
            ),
            context_vars=context_vars,
        )

        budget_hook = BudgetHookProvider()

        agent = Agent(
            name=config.agent_name,
            model=bedrock_model,
            system_prompt=system_prompt,
            tools=TOOLS,
            hooks=[budget_hook],
        )

        user_message = (
            "Execute the content pipeline now. Be concise — do not output verbose "
            "reasoning or scoring tables. Search, evaluate internally, then publish. "
            "Call create_post for each item and save_run_summary as your last action."
        )

        stream = agent.stream_async(user_message)
        async for event in stream:
            yield event

        logger.info(f"Content agent run complete: pipeline={pipeline}, tool_calls={budget_hook.tool_call_count}")

    except Exception as e:
        logger.error(f"Content agent failed: {type(e).__name__}: {e}", exc_info=True)
        yield {"type": "error", "message": f"Content agent failed: {str(e)}"}


if __name__ == "__main__":
    logger.info(f"Starting {config.agent_name}")
    logger.info(f"  Model: {config.get_model_id()}")
    logger.info(f"  Region: {config.aws_region}")
    app.run()
