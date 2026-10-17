"""UNWIRED. The live flow never calls this module. See REPO-FINDINGS.md item 2.

Optional Claude integration (explanations, categorization, natural-language rules).
"""
from typing import Any

from app.config import settings


def explain_decision(decision: dict[str, Any]) -> str:
    # TODO: anthropic.Anthropic(api_key=settings.anthropic_api_key).messages.create(model=settings.anthropic_model, ...)
    raise NotImplementedError


def parse_rule(text: str) -> dict[str, Any]:
    # TODO: natural language -> structured rule config via structured output
    raise NotImplementedError
