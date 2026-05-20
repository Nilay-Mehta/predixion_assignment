from bot.tools.base import Tool, ToolRegistry
from bot.tools.fetch_url import FetchUrlTool
from bot.tools.github_search import GithubSearchTool
from bot.tools.web_search import WebSearchTool


def default_registry() -> ToolRegistry:
    return ToolRegistry([WebSearchTool(), FetchUrlTool(), GithubSearchTool()])


__all__ = [
    "FetchUrlTool",
    "GithubSearchTool",
    "Tool",
    "ToolRegistry",
    "WebSearchTool",
    "default_registry",
]
