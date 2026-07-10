"""Tests de la máquina de estados del Job. Evita estados imposibles."""

import pytest

from lscrib.domain.models import (
    ALLOWED_TRANSITIONS,
    JobStatus,
    can_transition,
)

S = JobStatus


def test_every_status_is_in_the_transition_table():
    """Ningún estado sin definir (si no, can_transition lanzaría KeyError)."""
    assert set(ALLOWED_TRANSITIONS) == set(JobStatus)


def test_happy_path():
    assert can_transition(S.UPLOADED, S.QUEUED)
    assert can_transition(S.QUEUED, S.NORMALIZING)
    assert can_transition(S.NORMALIZING, S.TRANSCRIBING)
    assert can_transition(S.TRANSCRIBING, S.COMPLETED)


def test_uploaded_only_goes_to_queued():
    assert ALLOWED_TRANSITIONS[S.UPLOADED] == {S.QUEUED}


def test_completed_is_terminal():
    assert ALLOWED_TRANSITIONS[S.COMPLETED] == set()
    for dst in JobStatus:
        assert not can_transition(S.COMPLETED, dst)


@pytest.mark.parametrize("src", [S.QUEUED, S.NORMALIZING, S.TRANSCRIBING])
def test_cancelable_states_reach_canceled(src):
    """Cancelar permitido en queued/normalizing/transcribing."""
    assert can_transition(src, S.CANCELED)


def test_uploaded_is_not_cancelable():
    assert not can_transition(S.UPLOADED, S.CANCELED)


@pytest.mark.parametrize("src", [S.NORMALIZING, S.TRANSCRIBING])
def test_failure_states_can_fail(src):
    assert can_transition(src, S.FAILED)


def test_retry_and_requeue():
    assert can_transition(S.FAILED, S.QUEUED)     # reintentar
    assert can_transition(S.CANCELED, S.QUEUED)   # reencolar


def test_cannot_skip_normalizing():
    assert not can_transition(S.QUEUED, S.TRANSCRIBING)
    assert not can_transition(S.QUEUED, S.COMPLETED)
