from ..ports.llm_gateway import LLMGateway


class EvaluateWithRagUseCase:
    def __init__(self, llm: LLMGateway):
        self.llm = llm

    async def __call__(self, prompt: str) -> str:
        return await self.llm.generate(prompt)
