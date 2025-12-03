from ..ports.llm_gateway import LLMGateway


class GradeAnswerUseCase:
    """Stateless grading: builds a fresh prompt each call, no history kept."""

    def __init__(self, llm: LLMGateway):
        self.llm = llm

    async def __call__(
        self,
        question: str,
        student_answer: str,
        lecture_snippet: str | None = None,
    ) -> str:
        context_part = (
            f"Контекст лекции: {lecture_snippet}\n\n" if lecture_snippet else "Контекст лекции отсутствует.\n\n"
        )
        prompt = (
            "Ты экзаменатор. Оцени ответ студента.\n"
            f"Вопрос: {question}\n"
            f"Ответ студента: {student_answer}\n"
            f"{context_part}"
            "Дай число от 1 до 10 и коротко обоснуй. Если оценка <4 — напиши, что нужна пересдача."
        )
        return await self.llm.generate(prompt)
