import pytest
from packages.agent_core.state_machine import CallStateMachine
from packages.telephony.base import CallState


def test_valid_state_progression():
    sm = CallStateMachine(CallState.IDLE)
    assert sm.current_state == CallState.IDLE

    sm.transition(CallState.DIALING)
    assert sm.current_state == CallState.DIALING

    sm.transition(CallState.RINGING)
    assert sm.current_state == CallState.RINGING

    sm.transition(CallState.CONNECTED)
    assert sm.current_state == CallState.CONNECTED

    sm.transition(CallState.LISTENING)
    assert sm.current_state == CallState.LISTENING

    sm.transition(CallState.THINKING)
    assert sm.current_state == CallState.THINKING

    sm.transition(CallState.SPEAKING)
    assert sm.current_state == CallState.SPEAKING

    # Return to listening
    sm.transition(CallState.LISTENING)
    assert sm.current_state == CallState.LISTENING

    # Terminate call
    sm.transition(CallState.ENDED)
    assert sm.current_state == CallState.ENDED


def test_invalid_state_transition():
    sm = CallStateMachine(CallState.IDLE)
    # Cannot jump directly from IDLE to SPEAKING
    with pytest.raises(ValueError):
        sm.transition(CallState.SPEAKING)
