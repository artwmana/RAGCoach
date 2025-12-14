import httpx
from ...application.ports.llm_gateway import LLMGateway
from ..settings import settings


class OllamaLLMGateway(LLMGateway):
    async def generate(self, prompt: str) -> str:
        payload = {
            "model": settings.ollama_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": settings.llm_temperature,
                "num_predict": settings.llm_max_tokens
            }
        }

        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{settings.ollama_url}/api/generate",
                json=payload,
                timeout=120
            )

        r.raise_for_status()
        return r.json()["response"]
