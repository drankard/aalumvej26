"""Prompt service for aalumvej26 content agent.

Loads prompts from local .md files (packaged with the runtime) and composes
system prompts with injected context variables.
"""
import logging
import os
from datetime import datetime
from string import Template

from utils import current_season

logger = logging.getLogger(__name__)

PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")


class PromptService:
    def __init__(self, region: str = "eu-west-1") -> None:
        self.region = region

    def _load_prompt(self, filename: str) -> str:
        path = os.path.join(PROMPTS_DIR, filename)
        with open(path) as f:
            content = f.read()
        if not content.strip():
            raise ValueError(f"Empty prompt file: {path}")
        logger.info(f"Loaded prompt from {filename}")
        return content

    def build_system_prompt(
        self,
        pipeline: str,
        context_vars: dict | None = None,
        **_kwargs,
    ) -> str:
        base = self._load_prompt("BASE_SYSTEM.md")
        pipeline_file = (
            "PIPELINE_OPLEVELSER.md" if pipeline == "oplevelser"
            else "PIPELINE_OMRAADET.md"
        )
        pipeline_text = self._load_prompt(pipeline_file)

        combined = base + "\n\n" + pipeline_text

        vars_to_inject = {
            "current_date": datetime.now().isoformat()[:10],
            "season": current_season(),
        }
        if context_vars:
            vars_to_inject.update(context_vars)

        safe_vars = {
            k: str(v).replace("$", "$$") if v is not None else ""
            for k, v in vars_to_inject.items()
        }
        template = Template(combined)
        return template.safe_substitute(safe_vars)
