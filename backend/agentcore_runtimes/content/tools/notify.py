"""SNS notification tool for publishing pipeline run summaries."""
import os

import boto3
from strands import tool

_sns = None


def _get_sns():
    global _sns
    if _sns is None:
        region = os.environ.get("AWS_REGION", "eu-west-1")
        _sns = boto3.client("sns", region_name=region)
    return _sns


@tool
def publish_summary(pipeline: str, subject: str, body: str) -> dict:
    """Publish a pipeline run summary via SNS email notification.

    Call this as the very last step of every pipeline run.

    Args:
        pipeline: Pipeline name ("oplevelser" or "omraadet").
        subject: Short email subject line summarizing the run.
        body: Full summary in plain text — what was searched, archived, created, and any issues found.

    Returns:
        Confirmation with the SNS message ID.
    """
    topic_arn = os.environ.get("SNS_TOPIC_ARN", "")
    if not topic_arn:
        return {"status": "skipped", "reason": "SNS_TOPIC_ARN not set"}

    sns = _get_sns()
    resp = sns.publish(
        TopicArn=topic_arn,
        Subject=f"[aalumvej26] {subject}",
        Message=body,
    )
    return {"status": "sent", "message_id": resp["MessageId"]}
