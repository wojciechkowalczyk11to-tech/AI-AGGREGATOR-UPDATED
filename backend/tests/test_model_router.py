from __future__ import annotations

from app.db.models import UserRole
from app.services.model_router import DifficultyLevel, ModelRouter


def test_easy_prompt_classified() -> None:
    router = ModelRouter()
    assert router.classify_difficulty("Cześć, dzięki za pomoc") == DifficultyLevel.EASY


def test_hard_prompt_classified() -> None:
    router = ModelRouter()
    assert (
        router.classify_difficulty("Proszę przeanalizuj i zaprojektuj architekturę mikroserwisów")
        == DifficultyLevel.HARD
    )


def test_medium_default() -> None:
    router = ModelRouter()
    prompt = " ".join(["token"] * 80)
    assert router.classify_difficulty(prompt) == DifficultyLevel.MEDIUM


def test_select_profile_auto_easy() -> None:
    router = ModelRouter()
    profile = router.select_profile(DifficultyLevel.EASY, "auto", UserRole.DEMO.value, 1.0)
    assert profile == "eco"


def test_select_profile_auto_hard() -> None:
    router = ModelRouter()
    profile = router.select_profile(DifficultyLevel.HARD, "auto", UserRole.FULL_ACCESS.value, 2.0)
    assert profile == "deep"


def test_demo_cannot_deep() -> None:
    router = ModelRouter()
    profile = router.select_profile(DifficultyLevel.HARD, "deep", UserRole.DEMO.value, 5.0)
    assert profile == "smart"


def test_smart_credits_calculation() -> None:
    router = ModelRouter()
    assert router.calculate_smart_credits(200, 200) == 1
    assert router.calculate_smart_credits(1000, 800) == 2
    assert router.calculate_smart_credits(3000, 1000) == 4
