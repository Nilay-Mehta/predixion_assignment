from datetime import datetime, timezone

import httpx
import trafilatura
from pydantic import BaseModel, HttpUrl

from bot.config import settings
from bot.tools.base import Tool
from bot.utils.retry import network_retry

MAX_BODY_BYTES = 2 * 1024 * 1024
MAX_TEXT_CHARS = 10_000


class FetchUrlArgs(BaseModel):
    url: HttpUrl


class FetchOutput(BaseModel):
    url: HttpUrl
    title: str | None
    text: str
    fetched_at: datetime
    char_count: int
    truncated: bool


class FetchUrlTool(Tool):
    name = "fetch_url"
    description = (
        "Fetch and clean the main text content of a specific URL. Use when a "
        "search snippet is too shallow."
    )
    args_schema = FetchUrlArgs

    @network_retry
    def run(self, args: BaseModel) -> FetchOutput:
        parsed = FetchUrlArgs.model_validate(args)
        html = _fetch_limited(str(parsed.url))
        metadata = trafilatura.extract_metadata(html)
        extracted = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=False,
        )
        if not extracted or not extracted.strip():
            raise ValueError("fetched page has no extractable text")

        title = metadata.title if metadata else None
        text = extracted.strip()
        char_count = len(text)
        truncated = char_count > MAX_TEXT_CHARS
        if truncated:
            text = text[:MAX_TEXT_CHARS]

        # TODO Phase 4: run prompt-injection sniffing before synthesis.
        return FetchOutput(
            url=parsed.url,
            title=title,
            text=text,
            fetched_at=datetime.now(timezone.utc),
            char_count=char_count,
            truncated=truncated,
        )


def _fetch_limited(url: str) -> str:
    timeout = settings.tool_timeout_seconds
    with httpx.Client(
        timeout=timeout,
        follow_redirects=True,
        headers={"User-Agent": "botResearchAgent/0.1 (+https://github.com/...)"},
        limits=httpx.Limits(max_connections=5),
    ) as client:
        with client.stream("GET", url) as response:
            response.raise_for_status()
            chunks: list[bytes] = []
            total = 0
            for chunk in response.iter_bytes():
                total += len(chunk)
                if total > MAX_BODY_BYTES:
                    raise ValueError("fetched page exceeded 2MB body limit")
                chunks.append(chunk)
            return b"".join(chunks).decode(response.encoding or "utf-8", errors="replace")

__all__ = ["FetchOutput", "FetchUrlArgs", "FetchUrlTool"]
