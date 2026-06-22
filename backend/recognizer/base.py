from abc import ABC, abstractmethod


class RecognizerBase(ABC):
    """
    Abstract interface for all stenography recognition engines.

    Stroke schema expected by recognize():
        [
            {
                "id": str,
                "points": [{"x": float, "y": float, "timestamp": int}]
            }
        ]

    Concrete implementations (PyTorch models, rule-based engines, etc.)
    will be added in Phase 2 under this module.
    """

    @abstractmethod
    def recognize(self, strokes: list[dict]) -> str:  # type: ignore[type-arg]
        """Convert a list of stroke dicts into English text."""
        ...

    @abstractmethod
    def is_ready(self) -> bool:
        """Return True if the model is loaded and ready to process strokes."""
        ...
