"""UNWIRED. The live flow never calls this module. See REPO-FINDINGS.md item 2.

Optional Claude integration (explanations, categorization, natural-language rules).
"""
from typing import Any


def explain_decision(decision: dict[str, Any]) -> str:
    raise NotImplementedError


def parse_rule(text: str) -> dict[str, Any]:
    raise NotImplementedError
