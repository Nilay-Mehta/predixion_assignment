from abc import ABC, abstractmethod

from pydantic import BaseModel


class Tool(ABC):
    name: str
    description: str
    args_schema: type[BaseModel]

    @abstractmethod
    def run(self, args: BaseModel) -> BaseModel: ...


class ToolRegistry:
    def __init__(self, tools: list[Tool]) -> None:
        self._tools = {tool.name: tool for tool in tools}

    def get(self, name: str) -> Tool:
        return self._tools[name]

    def catalog(self) -> list[dict]:
        return [
            {"name": tool.name, "description": tool.description}
            for tool in self._tools.values()
        ]

    def names(self) -> list[str]:
        return list(self._tools.keys())


__all__ = ["Tool", "ToolRegistry"]
