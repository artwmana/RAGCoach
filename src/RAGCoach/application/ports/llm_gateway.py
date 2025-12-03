from abc import ABC, abstractmethod


class LLMGateway(ABC):
    @abstractmethod
    async def generate(self, prompt: str) -> str:
        pass
