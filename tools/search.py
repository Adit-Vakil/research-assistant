"""Web search tool — thin async wrapper around Tavily."""
import asyncio
from typing import TypedDict
from tavily import TavilyClient
from config import TAVILY_API_KEY


class SearchResult(TypedDict):
    title: str
    url: str
    content: str
    score: float


_client = TavilyClient(api_key=TAVILY_API_KEY) if TAVILY_API_KEY else None


async def web_search(
    query: str,
    max_results: int = 5,
    search_depth: str = "basic",  # "basic" or "advanced"
) -> list[SearchResult]:
    """Run a Tavily search asynchronously. Returns list of result dicts."""
    if _client is None:
        raise RuntimeError("TAVILY_API_KEY missing in .env")

    raw = await asyncio.to_thread(
        _client.search,
        query=query,
        max_results=max_results,
        search_depth=search_depth,
    )

    return [
        {
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "content": r.get("content", ""),
            "score": r.get("score", 0.0),
        }
        for r in raw.get("results", [])
    ]


def format_results(results: list[SearchResult]) -> str:
    """Format results as a single string for feeding to an LLM."""
    if not results:
        return "(no results)"
    lines = []
    for i, r in enumerate(results, 1):
        lines.append(f"[{i}] {r['title']}\nURL: {r['url']}\n{r['content']}\n")
    return "\n".join(lines)