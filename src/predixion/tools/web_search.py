from urllib.parse import urlparse

from pydantic import BaseModel, Field, HttpUrl
from tavily import TavilyClient

from predixion.config import settings
from predixion.tools.base import Tool
from predixion.utils.retry import network_retry


class WebSearchArgs(BaseModel):
    query: str
    max_results: int = Field(default=5, le=10)


class SearchResult(BaseModel):
    title: str
    url: HttpUrl
    snippet: str
    content: str | None = None
    score: float | None = None
    domain: str


class SearchOutput(BaseModel):
    query: str
    results: list[SearchResult]
    raw_count: int
    filtered_count: int


class WebSearchTool(Tool):
    name = "web_search"
    description = (
        "Search the web for a query. Returns titles, URLs, snippets, and "
        "extracted page content."
    )
    args_schema = WebSearchArgs

    def __init__(self) -> None:
        if not settings.tavily_api_key:
            msg = "TAVILY_API_KEY is required for WebSearchTool"
            raise ValueError(msg)
        self.client = TavilyClient(api_key=settings.tavily_api_key)

    @network_retry
    def run(self, args: BaseModel) -> SearchOutput:
        parsed = WebSearchArgs.model_validate(args)
        response = self.client.search(
            query=parsed.query,
            search_depth=settings.search_depth,
            max_results=parsed.max_results,
            include_raw_content=True,
        )
        raw_results = response.get("results", [])
        results = [_to_search_result(item) for item in raw_results]
        filtered = [
            result
            for result in results
            if not (
                (result.score is not None and result.score < 0.3)
                or (not result.snippet and not result.content)
            )
        ]
        return SearchOutput(
            query=parsed.query,
            results=filtered,
            raw_count=len(raw_results),
            filtered_count=len(filtered),
        )


def _to_search_result(item: dict) -> SearchResult:
    url = item["url"]
    content = item.get("raw_content") or item.get("content")
    snippet = item.get("content") or ""
    if not snippet and content:
        snippet = content[:200]
    return SearchResult(
        title=item.get("title") or url,
        url=url,
        snippet=snippet[:200],
        content=content,
        score=item.get("score"),
        domain=urlparse(url).netloc,
    )


__all__ = ["SearchOutput", "SearchResult", "WebSearchArgs", "WebSearchTool"]
