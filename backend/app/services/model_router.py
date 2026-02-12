from __future__ import annotations

from enum import Enum

from app.db.models import UserRole


class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class ModelRouter:
    HARD_INDICATORS: list[str] = [
        "architektur",
        "zaprojektuj",
        "zoptymalizuj",
        "porównaj",
        "przeanalizuj",
        "design",
        "architect",
        "optimize",
        "compare",
        "comprehensive",
        "deep dive",
        "complex",
        "refactor",
    ]
    EASY_INDICATORS: list[str] = [
        "cześć",
        "dzięki",
        "hej",
        "co to jest",
        "przetłumacz",
        "hello",
        "thanks",
        "hi",
        "what is",
        "translate",
    ]

    def classify_difficulty(self, prompt: str) -> DifficultyLevel:
        prompt_normalized = prompt.strip().lower()
        words = [word for word in prompt_normalized.split() if word]
        word_count = len(words)

        if any(indicator in prompt_normalized for indicator in self.HARD_INDICATORS):
            return DifficultyLevel.HARD
        if any(indicator in prompt_normalized for indicator in self.EASY_INDICATORS):
            return DifficultyLevel.EASY

        if word_count > 300:
            return DifficultyLevel.HARD
        if word_count < 30:
            return DifficultyLevel.EASY
        return DifficultyLevel.MEDIUM

    def select_profile(
        self,
        difficulty: DifficultyLevel,
        user_mode: str,
        user_role: str,
        budget_remaining: float,
    ) -> str:
        normalized_mode = user_mode.lower()
        if normalized_mode in {"eco", "smart", "deep"}:
            if normalized_mode == "deep" and user_role == UserRole.DEMO.value:
                return "smart"
            return normalized_mode

        if difficulty == DifficultyLevel.EASY:
            return "eco"

        if difficulty == DifficultyLevel.HARD:
            if user_role == UserRole.DEMO.value:
                return "smart"
            return "deep" if budget_remaining > 0 else "smart"

        return "smart" if budget_remaining > 0 else "eco"

    def calculate_smart_credits(self, input_tokens: int, output_tokens: int) -> int:
        total_tokens = max(input_tokens, 0) + max(output_tokens, 0)
        if total_tokens <= 500:
            return 1
        if total_tokens <= 2000:
            return 2
        return 4
