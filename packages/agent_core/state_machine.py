from typing import Dict, List, Set

from packages.telephony.base import CallState, VALID_TRANSITIONS


class CallStateMachine:
    """
    Validates and manages call state transitions with structured error reporting.
    """

    def __init__(self, initial_state: CallState = CallState.IDLE) -> None:
        self._current_state = initial_state
        self._history: List[CallState] = [initial_state]

    @property
    def current_state(self) -> CallState:
        return self._current_state

    @property
    def history(self) -> List[CallState]:
        return list(self._history)

    def can_transition_to(self, new_state: CallState) -> bool:
        if new_state in (CallState.ERROR, CallState.ENDED):
            return True
        allowed = VALID_TRANSITIONS.get(self._current_state, [])
        return new_state in allowed

    def transition(self, new_state: CallState) -> CallState:
        if not self.can_transition_to(new_state):
            allowed = [s.value for s in VALID_TRANSITIONS.get(self._current_state, [])]
            raise ValueError(
                f"Invalid transition from {self._current_state.value} to {new_state.value}. Allowed: {allowed}"
            )

        self._current_state = new_state
        self._history.append(new_state)
        return self._current_state
