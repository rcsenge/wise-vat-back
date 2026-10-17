"""Runs a set of rules against an event."""
from app.domain.events import Event
from app.domain.rules import Decision, Rule, State


def evaluate_all(rules: list[Rule], state: State, event: Event) -> list[Decision]:
    # TODO: run each rule, collect decisions, resolve conflicts/priorities
    raise NotImplementedError
