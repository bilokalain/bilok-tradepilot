"""Modèle Sentiment — FinBERT pour analyse NLP des news et discours"""

import torch


def get_device() -> torch.device:
    """Utilise Metal/MPS sur MacBook M3, sinon CPU."""
    return torch.device("mps" if torch.backends.mps.is_available() else "cpu")


class SentimentModel:
    """Analyse de sentiment avec FinBERT, optimisé pour Apple Silicon."""

    def __init__(self):
        self.device = get_device()
        self.model = None
        self.tokenizer = None

    def load(self):
        """Charge le modèle FinBERT sur le device approprié."""
        # TODO: Charger ProsusAI/finbert
        raise NotImplementedError

    def predict(self, texts: list[str]) -> list[dict]:
        """Prédit le sentiment (positive/negative/neutral) + score."""
        raise NotImplementedError
