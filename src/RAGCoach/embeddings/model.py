from sentence_transformers import SentenceTransformer

class EmbeddingModel:
    def __init__(self, model_name: str = "intfloat/e5-base"):
        self.model = SentenceTransformer(model_name)

    def encode(self, texts: list[str]) -> list[list[float]]:
        embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=True
        )
        return embeddings.tolist()

    @property
    def dim(self) -> int:
        return self.model.get_sentence_embedding_dimension()
