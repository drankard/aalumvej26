"""Configuration for aalumvej26 content agent runtime."""
import os
import logging

import boto3
from cachetools import TTLCache

logger = logging.getLogger(__name__)

_ssm_cache: TTLCache = TTLCache(maxsize=20, ttl=300)


class ConfigService:
    def __init__(self) -> None:
        self.agent_name = os.environ.get("AGENT_NAME", "Aalumvej26 Content Agent")
        self.aws_region = os.environ.get("AWS_REGION", "eu-west-1")
        self.table_name = os.environ.get("TABLE_NAME", "aalumvej26-prod")

        self.model_id_param = os.environ.get("MODEL_ID_PARAM")
        self.model_id = os.environ.get("MODEL_ID")

        self.base_prompt_id = os.environ.get("BASE_PROMPT_ID")
        self.oplevelser_prompt_id = os.environ.get("OPLEVELSER_PROMPT_ID")
        self.omraadet_prompt_id = os.environ.get("OMRAADET_PROMPT_ID")

    def validate(self) -> None:
        if not self.model_id_param and not self.model_id:
            raise ValueError("Set MODEL_ID_PARAM or MODEL_ID")
        if not self.table_name:
            raise ValueError("TABLE_NAME is required")

    def get_model_id(self) -> str:
        if self.model_id:
            return self.model_id
        if self.model_id_param:
            if self.model_id_param in _ssm_cache:
                return _ssm_cache[self.model_id_param]
            ssm = boto3.client("ssm", region_name=self.aws_region)
            value = ssm.get_parameter(Name=self.model_id_param)["Parameter"]["Value"]
            _ssm_cache[self.model_id_param] = value
            return value
        raise ValueError("No model ID configured")
