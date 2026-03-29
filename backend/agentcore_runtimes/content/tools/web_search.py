"""Web search tool for content discovery."""
from strands import tool


@tool
def web_search(query: str, max_results: int = 8) -> dict:
    """Search the web for information about events, activities, and attractions near Agger, Thy.

    Args:
        query: Search query string (2-5 words work best, try Danish first)
        max_results: Maximum number of results to return (default 8)

    Returns:
        Search results with titles, snippets, and URLs
    """
    import boto3
    import json

    client = boto3.client("bedrock-agent-runtime")
    response = client.retrieve(
        knowledgeBaseId="web-search",
        retrievalQuery={"text": query},
        retrievalConfiguration={
            "vectorSearchConfiguration": {"numberOfResults": max_results}
        },
    )

    results = []
    for r in response.get("retrievalResults", []):
        results.append({
            "title": r.get("metadata", {}).get("title", ""),
            "snippet": r.get("content", {}).get("text", "")[:300],
            "url": r.get("location", {}).get("webLocation", {}).get("url", ""),
        })

    return {"query": query, "results": results, "count": len(results)}
