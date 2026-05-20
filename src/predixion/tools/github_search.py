from datetime import datetime
from typing import Literal

import httpx
from pydantic import BaseModel, Field, HttpUrl

from predixion.config import settings
from predixion.tools.base import Tool
from predixion.utils.retry import network_retry


class GithubSearchArgs(BaseModel):
    query: str
    max_results: int = Field(default=5, le=10)
    sort: Literal["stars", "updated", "best_match"] = "stars"


class GithubRepo(BaseModel):
    full_name: str
    url: HttpUrl
    description: str | None
    stars: int
    language: str | None
    license: str | None
    last_updated: datetime
    topics: list[str] = Field(default_factory=list)


class GithubSearchOutput(BaseModel):
    query: str
    repos: list[GithubRepo]
    rate_limit_remaining: int


class GithubSearchTool(Tool):
    name = "github_search"
    description = (
        "Search GitHub repositories. Returns structured repo data: stars, "
        "language, license, last updated, topics. Use for open-source comparisons."
    )
    args_schema = GithubSearchArgs

    @network_retry
    def run(self, args: BaseModel) -> GithubSearchOutput:
        parsed = GithubSearchArgs.model_validate(args)
        headers = {"Accept": "application/vnd.github+json"}
        if settings.github_token:
            headers["Authorization"] = f"Bearer {settings.github_token}"

        params: dict[str, str | int] = {
            "q": parsed.query,
            "per_page": parsed.max_results,
        }
        if parsed.sort != "best_match":
            params["sort"] = parsed.sort

        with httpx.Client(timeout=8, headers=headers) as client:
            response = client.get("https://api.github.com/search/repositories", params=params)
            if (
                response.status_code == 403
                and response.headers.get("X-RateLimit-Remaining") == "0"
            ):
                raise RuntimeError(
                    "GitHub rate limit hit (60/hr unauthenticated). Set GITHUB_TOKEN "
                    "in .env for 5000/hr."
                )
            response.raise_for_status()

        payload = response.json()
        repos = [_to_repo(item) for item in payload.get("items", [])]
        return GithubSearchOutput(
            query=parsed.query,
            repos=repos,
            rate_limit_remaining=int(response.headers.get("X-RateLimit-Remaining", 0)),
        )


def _to_repo(item: dict) -> GithubRepo:
    return GithubRepo(
        full_name=item["full_name"],
        url=item["html_url"],
        description=item.get("description"),
        stars=item["stargazers_count"],
        language=item.get("language"),
        license=(item.get("license") or {}).get("spdx_id"),
        last_updated=datetime.fromisoformat(item["updated_at"].replace("Z", "+00:00")),
        topics=item.get("topics", []),
    )


__all__ = ["GithubRepo", "GithubSearchArgs", "GithubSearchOutput", "GithubSearchTool"]
