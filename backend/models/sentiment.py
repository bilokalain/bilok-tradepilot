"""FinBERT — Analyse de sentiment financier NLP

Utilise ProsusAI/finbert, un modèle BERT fine-tuné sur des textes financiers.
Optimisé pour Apple Silicon (Metal/MPS).

Le modèle se télécharge automatiquement au premier usage (~440 MB).
Il est ensuite caché dans ~/.cache/huggingface.

Fallback : si le modèle ne peut pas être chargé (pas assez de RAM, pas de GPU),
on utilise l'analyse par mots-clés comme backup.
"""

import logging
from functools import lru_cache

import torch

logger = logging.getLogger("tradepilot.models.sentiment")


def get_device() -> torch.device:
    """Utilise Metal/MPS sur MacBook M3, sinon CPU."""
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


class FinBERTModel:
    """Analyse de sentiment avec FinBERT."""

    def __init__(self):
        self.device = get_device()
        self.model = None
        self.tokenizer = None
        self._loaded = False
        self._load_failed = False

    def load(self):
        """Charge le modèle FinBERT."""
        if self._loaded or self._load_failed:
            return

        try:
            from transformers import AutoTokenizer, AutoModelForSequenceClassification

            logger.info(f"[FinBERT] Chargement du modèle sur {self.device}...")
            self.tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
            self.model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")
            self.model.to(self.device)
            self.model.eval()
            self._loaded = True
            logger.info("[FinBERT] Modèle chargé avec succès")
        except Exception as e:
            logger.warning(f"[FinBERT] Impossible de charger le modèle: {e}")
            self._load_failed = True

    @property
    def is_available(self) -> bool:
        if not self._loaded and not self._load_failed:
            self.load()
        return self._loaded

    def predict(self, texts: list[str]) -> list[dict]:
        """Prédit le sentiment pour une liste de textes.

        Retourne pour chaque texte :
        - label : positive / negative / neutral
        - polarity : -1 à +1
        - confidence : 0 à 1
        """
        if not self.is_available:
            return [{"label": "neutral", "polarity": 0, "confidence": 0} for _ in texts]

        results = []
        # Traiter par batch de 16
        batch_size = 16
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            # Tronquer les textes trop longs
            batch = [t[:512] for t in batch]

            try:
                inputs = self.tokenizer(
                    batch, padding=True, truncation=True,
                    max_length=512, return_tensors="pt"
                )
                inputs = {k: v.to(self.device) for k, v in inputs.items()}

                with torch.no_grad():
                    outputs = self.model(**inputs)
                    probs = torch.nn.functional.softmax(outputs.logits, dim=-1)

                # FinBERT labels : positive (0), negative (1), neutral (2)
                for j in range(len(batch)):
                    pos = float(probs[j][0])
                    neg = float(probs[j][1])
                    neu = float(probs[j][2])

                    if pos > neg and pos > neu:
                        label = "positive"
                        polarity = pos - neg
                        confidence = pos
                    elif neg > pos and neg > neu:
                        label = "negative"
                        polarity = -(neg - pos)
                        confidence = neg
                    else:
                        label = "neutral"
                        polarity = pos - neg
                        confidence = neu

                    results.append({
                        "label": label,
                        "polarity": round(polarity, 4),
                        "confidence": round(confidence, 4),
                        "scores": {
                            "positive": round(pos, 4),
                            "negative": round(neg, 4),
                            "neutral": round(neu, 4),
                        },
                    })
            except Exception as e:
                logger.warning(f"[FinBERT] Erreur batch: {e}")
                for _ in batch:
                    results.append({"label": "neutral", "polarity": 0, "confidence": 0})

        return results

    def predict_one(self, text: str) -> dict:
        """Prédit le sentiment d'un seul texte."""
        results = self.predict([text])
        return results[0] if results else {"label": "neutral", "polarity": 0, "confidence": 0}


# Singleton — le modèle est lourd, on ne le charge qu'une fois
_finbert_instance = None


def get_finbert() -> FinBERTModel:
    global _finbert_instance
    if _finbert_instance is None:
        _finbert_instance = FinBERTModel()
    return _finbert_instance
