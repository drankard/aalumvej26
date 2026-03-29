"""Prompt service for aalumvej26 content agent.

Fetches prompts from Bedrock Prompt Manager and composes system prompts.
"""
import logging
from datetime import datetime
from string import Template

import boto3
from botocore.config import Config

logger = logging.getLogger(__name__)

_boto_config = Config(
    max_pool_connections=10,
    retries={"max_attempts": 3, "mode": "adaptive"},
)


def _current_season() -> str:
    month = datetime.now().month
    if month in (3, 4, 5):
        return "spring"
    if month in (6, 7, 8):
        return "summer"
    if month in (9, 10, 11):
        return "autumn"
    return "winter"


class PromptService:
    def __init__(self, region: str = "eu-west-1") -> None:
        self.region = region
        self.bedrock = boto3.client("bedrock-agent", region_name=region, config=_boto_config)

    def fetch_from_bedrock(self, prompt_arn: str) -> str:
        response = self.bedrock.get_prompt(promptIdentifier=prompt_arn)
        variants = response.get("variants", [])
        content = (
            variants[0]
            .get("templateConfiguration", {})
            .get("text", {})
            .get("text", "")
            if variants
            else ""
        )
        if not content:
            raise ValueError(f"Empty prompt content for {prompt_arn}")
        logger.info(f"Fetched prompt from Bedrock: {prompt_arn}")
        return content

    def build_system_prompt(
        self,
        pipeline: str,
        base_prompt_arn: str,
        pipeline_prompt_arn: str,
        context_vars: dict | None = None,
    ) -> str:
        base = self.fetch_from_bedrock(base_prompt_arn)
        pipeline_text = self.fetch_from_bedrock(pipeline_prompt_arn)

        combined = base + "\n\n" + pipeline_text

        vars_to_inject = {
            "current_date": datetime.now().isoformat()[:10],
            "season": _current_season(),
        }
        if context_vars:
            vars_to_inject.update(context_vars)

        safe_vars = {
            k: str(v).replace("$", "$$") if v is not None else ""
            for k, v in vars_to_inject.items()
        }
        template = Template(combined)
        return template.safe_substitute(safe_vars)
