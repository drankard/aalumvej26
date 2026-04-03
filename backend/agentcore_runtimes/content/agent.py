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

app = BedrockAgentCoreApp()

config = ConfigService()
config.validate()

prompt_service = PromptService(region=config.aws_region)

bedrock_model = BedrockModel(
    model_id=config.get_model_id(),
    streaming=True,
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

        agent = Agent(
            name=config.agent_name,
            model=bedrock_model,
            system_prompt=system_prompt,
            tools=TOOLS,
        )

        user_message = (
            "Execute the content pipeline now. Search for new content, evaluate it, "
            "and use the content_db tools to publish high-quality items. "
            "Return a structured JSON summary of your run."
        )

        stream = agent.stream_async(user_message)
        async for event in stream:
            yield event

        logger.info(f"Content agent run complete: pipeline={pipeline}")

    except Exception as e:
        logger.error(f"Content agent failed: {type(e).__name__}: {e}", exc_info=True)
        yield {"type": "error", "message": f"Content agent failed: {str(e)}"}


if __name__ == "__main__":
    logger.info(f"Starting {config.agent_name}")
    logger.info(f"  Model: {config.get_model_id()}")
    logger.info(f"  Region: {config.aws_region}")
    app.run()
