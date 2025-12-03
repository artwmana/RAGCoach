from .infrastructure.llm.ollama_gateway import OllamaLLMGateway
from .application.use_cases.evaluate_with_rag import EvaluateWithRagUseCase
from .application.use_cases.grade_answer import GradeAnswerUseCase


def build_rag_evaluator():
    llm = OllamaLLMGateway()
    return EvaluateWithRagUseCase(llm)


def build_grader():
    llm = OllamaLLMGateway()
    return GradeAnswerUseCase(llm)
