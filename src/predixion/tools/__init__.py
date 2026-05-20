from predixion.tools.base import Tool, ToolRegistry
from predixion.tools.fetch_url import FetchUrlTool
from predixion.tools.github_search import GithubSearchTool
from predixion.tools.web_search import WebSearchTool


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
