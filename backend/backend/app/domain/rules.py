"""Rule contract: every rule is a pure function of (state, event) -> Decision."""
from dataclasses import dataclass, field
from typing import Any, Protocol

from app.domain.events import Event


@dataclass
class State:
    """Snapshot of everything a rule may look at (balances, history, settings)."""
    balances: dict[str, Any] = field(default_factory=dict)
    # TODO: add fields as the challenge requires


@dataclass(frozen=True)
class Decision:
    action: str  # e.g. "allow", "block", "convert", "notify"
    reason: str  # human-readable — show this to judges/users
    data: dict[str, Any] = field(default_factory=dict)


class Rule(Protocol):
    name: str

    def evaluate(self, state: State, event: Event) -> Decision | None:
        """Return a Decision if the rule applies, else None."""
        ...
