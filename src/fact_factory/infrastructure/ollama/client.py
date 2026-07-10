from __future__ import annotations

import httpx
import numpy as np

from fact_factory.domain.exceptions import EmbeddingError


class OllamaEmbeddingClient:
    def __init__(self, base_url: str, model: str, timeout: float = 60.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout

    def embed(self, text: str) -> bytes:
        url = f"{self._base_url}/api/embeddings"
        try:
            response = httpx.post(
                url,
                json={"model": self._model, "prompt": text},
                timeout=self._timeout,
            )
        except httpx.RequestError as exc:
            raise EmbeddingError(
                f"Ollama is not reachable at {self._base_url}. "
                f"Ensure Ollama is running. Details: {exc}"
            ) from exc

        if response.status_code != 200:
            raise EmbeddingError(
                f"Ollama embedding request failed ({response.status_code}): "
                f"{response.text.strip()}"
            )

        payload = response.json()
        embedding = payload.get("embedding")
        if not embedding:
            raise EmbeddingError(
                f"Model '{self._model}' returned an empty embedding. "
                f"Run: ollama pull {self._model}"
            )

        vector = np.asarray(embedding, dtype=np.float32)
        return vector.tobytes()


def embedding_to_array(data: bytes) -> np.ndarray:
    return np.frombuffer(data, dtype=np.float32)


def cosine_similarity(left: bytes, right: bytes) -> float:
    left_vector = embedding_to_array(left)
    right_vector = embedding_to_array(right)
    denominator = np.linalg.norm(left_vector) * np.linalg.norm(right_vector)
    if denominator == 0:
        return 0.0
    return float(np.dot(left_vector, right_vector) / denominator)
