"""Modèle CNN ResNet18 — Reconnaissance de patterns graphiques"""

import torch


def get_device() -> torch.device:
    return torch.device("mps" if torch.backends.mps.is_available() else "cpu")


class PatternRecognitionModel:
    """CNN ResNet18 pour détecter les patterns dans les graphiques de prix."""

    def __init__(self):
        self.device = get_device()
        self.model = None

    def load(self):
        """Charge le ResNet18 pré-entraîné et fine-tuné."""
        # TODO: Charger le modèle fine-tuné
        raise NotImplementedError

    def predict(self, chart_image) -> dict:
        """Détecte le pattern graphique (head & shoulders, triangle, etc.)."""
        raise NotImplementedError
