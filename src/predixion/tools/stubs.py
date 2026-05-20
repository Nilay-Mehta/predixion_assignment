from typing import Literal

from pydantic import BaseModel, Field, HttpUrl

from predixion.tools.base import Tool


class WebSearchArgs(BaseModel):
    query: str
    max_results: int = Field(default=5, le=10)


class FetchUrlArgs(BaseModel):
    url: HttpUrl


class GithubSearchArgs(BaseModel):
    query: str
    max_results: int = Field(default=5, le=10)
    sort: Literal["stars", "updated", "best_match"] = "stars"


class StubWebSearch(Tool):
    name = "web_search"
    description = (
        "Search the web for a query. Returns titles, URLs, snippets, and "
        "extracted page content."
    )
    args_schema = WebSearchArgs

    def run(self, args: BaseModel) -> BaseModel:
        raise NotImplementedError("phase 2")


class StubFetchUrl(Tool):
    name = "fetch_url"
    description = (
        "Fetch and clean the main text content of a specific URL. Use when a "
        "search snippet is too shallow."
    )
    args_schema = FetchUrlArgs

    def run(self, args: BaseModel) -> BaseModel:
        raise NotImplementedError("phase 2")


class StubGithubSearch(Tool):
    name = "github_search"
    description = (
        "Search GitHub repositories. Returns structured repo data: stars, "
        "language, license, last updated, topics. Use for open-source comparisons."
    )
    args_schema = GithubSearchArgs

    def run(self, args: BaseModel) -> BaseModel:
        raise NotImplementedError("phase 2")


__all__ = [
    "FetchUrlArgs",
    "GithubSearchArgs",
    "StubFetchUrl",
    "StubGithubSearch",
    "StubWebSearch",
    "WebSearchArgs",
]
