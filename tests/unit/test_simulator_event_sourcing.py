"""Comprehensive unit tests for the Simulator <-> event sourcing integration.

These tests exercise *every* condition, failure mode, concurrency scenario,
and event emission path in the consolidated Simulator implementation.

Coverage areas:
- ``__init__``: provider, max_stages, event_store, locks, sequence counter.
- ``execute_simulation`` validation: empty name raises before any side effect.
- Successful run with event store: all 6 event types emitted in correct order
  with correct versions and sequence numbers.
- Successful run without event store: no events emitted, backward compatible.
- Stage failure path: StageFailed emitted, simulation continues.
- Critical failure path: stage loop breaks, remaining stages skipped.
- Simulation-level failure: SimulationFailed emitted, result marked failed.
- Event emission failure isolation: event store errors never break simulation.
- LLM content generation edge cases: unavailable provider, empty response,
  truncation retry, LLM raises.
- Active simulation tracking: thread-safe via ``_active_lock``, cleared in
  ``finally`` on success, failure, and critical break.
- ``cancel_simulation``: active and unknown-id branches (CANCELLED status
  preserved — bug fix verified).
- ``_next_sequence``: monotonic, thread-safe.
- ``_emit_event``: no-op when no store, catches and logs errors.
- ``_get_next_version``: returns 1 for new aggregate, increments for existing.
- Concurrency: parallel simulations produce disjoint result ids, leave no
  active simulations behind, and don't cross-contaminate events.

Owner: Test Suite Hardening
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from ciicerone.core.event_sourcing import (
    EventStore,
    SimulationStarted,
    StageStarted,
    StageCompleted,
    StageFailed,
    SimulationCompleted,
    SimulationFailed,
)
from ciicerone.core.models import (
    SimulationResult,
    SimulationStage,
    SimulationStatus,
    ThreatScenario,
    ThreatType,
)
from ciicerone.core.simulator import Simulator


# ---------------------------------------------------------------------------
# Test doubles
# ---------------------------------------------------------------------------


class StubLLMResponse:
    """Minimal stand-in for ``LLMResponse`` used by the simulator."""

    def __init__(self, content: str, finish_reason: Optional[str] = None) -> None:
        self.content = content
        self.finish_reason = finish_reason
        self.is_real_ai = False
        self.provider = "stub"
        self.model = "stub-model"


class StubLLMProvider:
    """Controllable LLM provider for the simulator."""

    def __init__(self, *, available: bool = True,
                 responses: Optional[List[StubLLMResponse]] = None,
                 fail_on_call: Optional[int] = None,
                 failure: Optional[Exception] = None) -> None:
        self._available = available
        self._responses = list(responses) if responses else [
            StubLLMResponse(f"stage content #{i}") for i in range(64)
        ]
        self._fail_on_call = fail_on_call
        self._failure = failure or RuntimeError("LLM exploded")
        self.call_count = 0
        self.calls: List[Dict[str, Any]] = []

    def is_available(self) -> bool:
        return self._available

    async def generate_content(self, prompt: str, max_tokens: int = 1000,
                               temperature: float = 0.7, **kwargs) -> StubLLMResponse:
        self.call_count += 1
        self.calls.append({
            "prompt": prompt, "max_tokens": max_tokens,
            "temperature": temperature, "kwargs": kwargs,
        })
        if self._fail_on_call is not None and self.call_count == self._fail_on_call:
            raise self._failure
        if len(self._responses) == 1:
            return self._responses[0]
        return self._responses.pop(0)


class RecordingEventStore(EventStore):
    """In-memory EventStore that records all appended events for assertions.

    Extends the real ``EventStore`` (pool=None → in-memory mode) so that
    optimistic concurrency control and version tracking are exercised
    exactly as in production.
    """

    def __init__(self) -> None:
        super().__init__(pool=None)
        self.appended: List[Any] = []
        self._append_should_fail: bool = False
        self._fail_on_append_num: Optional[int] = None
        self._append_count: int = 0

    async def append(self, event: Any) -> int:
        self._append_count += 1
        if self._fail_on_append_num is not None and self._append_count == self._fail_on_append_num:
            raise RuntimeError("Injected append failure")
        seq = await super().append(event)
        self.appended.append(event)
        return seq

    def event_types(self) -> List[str]:
        return [e.event_type for e in self.appended]


def _scenario(name: str = "Test Scenario",
              threat_type: ThreatType = ThreatType.PHISHING,
              scenario_id: str = "scn-1") -> ThreatScenario:
    return ThreatScenario(
        name=name,
        threat_type=threat_type,
        description="desc",
        severity="medium",
        target_systems=["email"],
        attack_vectors=["social_engineering"],
        metadata={},
        scenario_id=scenario_id,
    )


@pytest.fixture
def fast_sleep():
    """Patch ``asyncio.sleep`` in the simulator module so stage delays don't
    slow the suite."""
    with patch("ciicerone.core.simulator.asyncio.sleep", new=AsyncMock()):
        yield


# ---------------------------------------------------------------------------
# __init__ & __repr__
# ---------------------------------------------------------------------------


class TestSimulatorInit:
    """Constructor, locks, sequence counter, and repr."""

    def test_uses_provided_provider(self):
        provider = StubLLMProvider()
        sim = Simulator(llm_provider=provider, max_stages=4)
        assert sim.llm_provider is provider
        assert sim.max_stages == 4
        assert sim._active_simulations == {}

    def test_default_max_stages_is_ten(self):
        sim = Simulator(llm_provider=StubLLMProvider())
        assert sim.max_stages == 10

    def test_event_store_stored_when_provided(self):
        store = RecordingEventStore()
        sim = Simulator(llm_provider=StubLLMProvider(), event_store=store)
        assert sim.event_store is store

    def test_event_store_defaults_to_none(self):
        sim = Simulator(llm_provider=StubLLMProvider())
        assert sim.event_store is None

    def test_has_active_lock(self):
        sim = Simulator(llm_provider=StubLLMProvider())
        assert hasattr(sim, "_active_lock")
        assert isinstance(sim._active_lock, asyncio.Lock)

    def test_has_sequence_lock_and_counter(self):
        sim = Simulator(llm_provider=StubLLMProvider())
        assert hasattr(sim, "_sequence_lock")
        assert isinstance(sim._sequence_lock, asyncio.Lock)
        assert sim._sequence_counter == 0

    def test_repr_includes_provider_class_and_active_count(self):
        sim = Simulator(llm_provider=StubLLMProvider())
        assert "StubLLMProvider" in repr(sim)
        assert "active=0" in repr(sim)


# ---------------------------------------------------------------------------
# _next_sequence
# ---------------------------------------------------------------------------


class TestNextSequence:
    """``_next_sequence`` must be monotonic and thread-safe."""

    @pytest.mark.asyncio
    async def test_returns_monotonically_increasing(self):
        sim = Simulator(llm_provider=StubLLMProvider())
        seqs = [await sim._next_sequence() for _ in range(5)]
        assert seqs == [1, 2, 3, 4, 5]

    @pytest.mark.asyncio
    async def test_concurrent_calls_produce_unique_values(self):
        sim = Simulator(llm_provider=StubLLMProvider())
        seqs = await asyncio.gather(*[sim._next_sequence() for _ in range(20)])
        assert len(set(seqs)) == 20  # all unique


# ---------------------------------------------------------------------------
# _emit_event
# ---------------------------------------------------------------------------


class TestEmitEvent:
    """``_emit_event`` is a no-op without a store and catches errors."""

    @pytest.mark.asyncio
    async def test_noop_when_no_store(self):
        sim = Simulator(llm_provider=StubLLMProvider())
        # Must not raise.
        await sim._emit_event(MagicMock())

    @pytest.mark.asyncio
    async def test_appends_to_store_when_configured(self):
        store = RecordingEventStore()
        sim = Simulator(llm_provider=StubLLMProvider(), event_store=store)
        # Use a real event with version=1 (first event for a new aggregate).
        agg_id = uuid4()
        event = SimulationStarted.create(
            aggregate_id=agg_id, scenario_id=uuid4(),
            max_stages=3, initiated_by="test",
            version=1, sequence_number=1,
        )
        await sim._emit_event(event)
        assert store.appended == [event]

    @pytest.mark.asyncio
    async def test_catches_and_logs_append_failure(self, caplog):
        store = RecordingEventStore()
        store._fail_on_append_num = 1
        sim = Simulator(llm_provider=StubLLMProvider(), event_store=store)
        with caplog.at_level(logging.ERROR, logger="ciicerone.core.simulator"):
            await sim._emit_event(MagicMock())
        assert any("Failed to emit event" in r.message for r in caplog.records)


# ---------------------------------------------------------------------------
# _get_next_version
# ---------------------------------------------------------------------------


class TestGetNextVersion:
    """``_get_next_version`` queries the store and increments."""

    @pytest.mark.asyncio
    async def test_returns_one_for_new_aggregate(self):
        store = RecordingEventStore()
        sim = Simulator(llm_provider=StubLLMProvider(), event_store=store)
        version = await sim._get_next_version(uuid4())
        assert version == 1

    @pytest.mark.asyncio
    async def test_returns_incremented_version_after_append(self):
        store = RecordingEventStore()
        sim = Simulator(llm_provider=StubLLMProvider(), event_store=store)
        agg_id = uuid4()
        v1 = await sim._get_next_version(agg_id)
        # Simulate an append by directly calling the store.
        event = SimulationStarted.create(
            aggregate_id=agg_id, scenario_id=uuid4(),
            max_stages=3, initiated_by="test",
            version=v1, sequence_number=1,
        )
        await store.append(event)
        v2 = await sim._get_next_version(agg_id)
        assert v2 == v1 + 1

    @pytest.mark.asyncio
    async def test_returns_one_when_no_store(self):
        sim = Simulator(llm_provider=StubLLMProvider())
        version = await sim._get_next_version(uuid4())
        assert version == 1


# ---------------------------------------------------------------------------
# execute_simulation — validation
# ---------------------------------------------------------------------------


class TestExecuteSimulationValidation:
    """Pre-condition validation must reject bad input before any side effect."""

    @pytest.mark.asyncio
    async def test_empty_name_raises_value_error(self):
        sim = Simulator(llm_provider=StubLLMProvider())
        with pytest.raises(ValueError):
            await sim.execute_simulation(ThreatScenario(name="  ", threat_type=ThreatType.PHISHING))

    @pytest.mark.asyncio
    async def test_invalid_scenario_does_not_register_active_simulation(self):
        sim = Simulator(llm_provider=StubLLMProvider())
        with pytest.raises(ValueError):
            await sim.execute_simulation(ThreatScenario(name="", threat_type=ThreatType.PHISHING))
        assert sim._active_simulations == {}

    @pytest.mark.asyncio
    async def test_invalid_scenario_does_not_emit_events(self):
        store = RecordingEventStore()
        sim = Simulator(llm_provider=StubLLMProvider(), event_store=store)
        with pytest.raises(ValueError):
            await sim.execute_simulation(ThreatScenario(name="", threat_type=ThreatType.PHISHING))
        assert store.appended == []


# ---------------------------------------------------------------------------
# execute_simulation — successful runs WITH event store
# ---------------------------------------------------------------------------


class TestSuccessfulRunWithEventStore:
    """Successful multi-stage run with event store: all 6 event types emitted."""

    @pytest.mark.asyncio
    async def test_all_six_event_types_emitted_in_order(self, fast_sleep):
        store = RecordingEventStore()
        sim = Simulator(llm_provider=StubLLMProvider(), max_stages=2, event_store=store)
        await sim.execute_simulation(_scenario())

        types = store.event_types()
        # 1 SimulationStarted + 2 × (StageStarted + StageCompleted) + 1 SimulationCompleted
        assert types == [
            "SimulationStarted",
            "StageStarted", "StageCompleted",
            "StageStarted", "StageCompleted",
            "SimulationCompleted",
        ]

    @pytest.mark.asyncio
    async def test_events_have_increasing_versions(self, fast_sleep):
        store = RecordingEventStore()
        sim = Simulator(llm_provider=StubLLMProvider(), max_stages=2, event_store=store)
        await sim.execute_simulation(_scenario())

        versions = [e.version for e in store.appended]
        assert versions == sorted(versions)  # monotonically increasing
        assert versions[0] == 1
        assert versions[-1] == len(versions)

    @pytest.mark.asyncio
    async def test_events_have_increasing_sequence_numbers(self, fast_sleep):
        store = RecordingEventStore()
        sim = Simulator(llm_provider=StubLLMProvider(), max_stages=2, event_store=store)
        await sim.execute_simulation(_scenario())

        seqs = [e.sequence_number for e in store.appended]
        assert seqs == sorted(seqs)
        assert len(set(seqs)) == len(seqs)  # all unique

    @pytest.mark.asyncio
    async def test_simulation_started_has_correct_max_stages(self, fast_sleep):
        store = RecordingEventStore()
        sim = Simulator(llm_provider=StubLLMProvider(), max_stages=3, event_store=store)
        await sim.execute_simulation(_scenario())

        started = [e for e in store.appended if e.event_type == "SimulationStarted"][0]
        assert started.event_data["max_stages"] == 3

    @pytest.mark.asyncio
    async def test_simulation_completed_has_correct_stage_counts(self, fast_sleep):
        store = RecordingEventStore()
        sim = Simulator(llm_provider=StubLLMProvider(), max_stages=2, event_store=store)
        await sim.execute_simulation(_scenario())

        completed = [e for e in store.appended if e.event_type == "SimulationCompleted"][0]
        assert completed.event_data["total_stages"] == 2
        assert completed.event_data["successful_stages"] == 2

    @pytest.mark.asyncio
    async def test_stage_completed_has_content_length(self, fast_sleep):
        store = RecordingEventStore()
        sim = Simulator(llm_provider=StubLLMProvider(), max_stages=1, event_store=store)
        await sim.execute_simulation(_scenario())

        stage_completed = [e for e in store.appended if e.event_type == "StageCompleted"][0]
        assert stage_completed.event_data["content_length"] > 0

    @pytest.mark.asyncio
    async def test_all_events_share_same_aggregate_id(self, fast_sleep):
        store = RecordingEventStore()
        sim = Simulator(llm_provider=StubLLMProvider(), max_stages=2, event_store=store)
        await sim.execute_simulation(_scenario())

        agg_ids = {e.aggregate_id for e in store.appended}
        assert len(agg_ids) == 1  # all events belong to one aggregate


# ---------------------------------------------------------------------------
# execute_simulation — successful runs WITHOUT event store
# ---------------------------------------------------------------------------


class TestSuccessfulRunWithoutEventStore:
    """Backward-compatible: no event store → no events, simulation works."""

    @pytest.mark.asyncio
    async def test_no_events_emitted_without_store(self, fast_sleep):
        sim = Simulator(llm_provider=StubLLMProvider(), max_stages=2)
        result = await sim.execute_simulation(_scenario())
        assert result.status == SimulationStatus.COMPLETED
        assert len(result.stages) == 2

    @pytest.mark.asyncio
    async def test_max_stages_truncates_stage_list(self, fast_sleep):
        sim = Simulator(llm_provider=StubLLMProvider(), max_stages=2)
        result = await sim.execute_simulation(_scenario())
        assert len(result.stages) == 2

    @pytest.mark.asyncio
    async def test_max_stages_zero_produces_no_stages(self, fast_sleep):
        sim = Simulator(llm_provider=StubLLMProvider(), max_stages=0)
        result = await sim.execute_simulation(_scenario())
        assert result.stages == []
        assert result.status == SimulationStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_max_stages_greater_than_config_runs_all_seven(self, fast_sleep):
        sim = Simulator(llm_provider=StubLLMProvider(), max_stages=99)
        result = await sim.execute_simulation(_scenario())
        assert len(result.stages) == 7


# ---------------------------------------------------------------------------
# execute_simulation — stage failure paths WITH event store
# ---------------------------------------------------------------------------


class TestStageFailurePathsWithEventStore:
    """Stage failures emit StageFailed events and the run continues."""

    @pytest.mark.asyncio
    async def test_stage_failed_event_emitted_on_stage_error(self, fast_sleep):
        store = RecordingEventStore()
        sim = Simulator(llm_provider=StubLLMProvider(), max_stages=3, event_store=store)
        original = sim._generate_stage_content
        call_count = {"n": 0}

        async def flaky_content(scenario, stage_type, description):
            call_count["n"] += 1
            if call_count["n"] == 2:
                raise RuntimeError("stage blew up")
            return await original(scenario, stage_type, description)

        with patch.object(sim, "_generate_stage_content", side_effect=flaky_content):
            result = await sim.execute_simulation(_scenario())

        failed_events = [e for e in store.appended if e.event_type == "StageFailed"]
        assert len(failed_events) == 1
        assert "stage blew up" in failed_events[0].event_data["error_message"]
        assert failed_events[0].event_data["error_type"] == "RuntimeError"
        assert result.status == SimulationStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_critical_error_emits_stage_failed_and_breaks_loop(self, fast_sleep):
        store = RecordingEventStore()
        sim = Simulator(llm_provider=StubLLMProvider(), max_stages=5, event_store=store)

        async def critical_content(scenario, stage_type, description):
            raise RuntimeError("CRITICAL failure detected")

        with patch.object(sim, "_generate_stage_content", side_effect=critical_content):
            result = await sim.execute_simulation(_scenario())

        # Only 1 stage attempted → 1 StageStarted + 1 StageFailed.
        stage_started = [e for e in store.appended if e.event_type == "StageStarted"]
        stage_failed = [e for e in store.appended if e.event_type == "StageFailed"]
        assert len(stage_started) == 1
        assert len(stage_failed) == 1
        assert len(result.stages) == 1
        # Simulation still completes (critical break is not a sim-level failure).
        assert result.status == SimulationStatus.COMPLETED
        # SimulationCompleted is still emitted.
        completed = [e for e in store.appended if e.event_type == "SimulationCompleted"]
        assert len(completed) == 1


# ---------------------------------------------------------------------------
# execute_simulation — simulation-level failure WITH event store
# ---------------------------------------------------------------------------


class TestSimulationLevelFailureWithEventStore:
    """When ``_execute_stages`` raises, SimulationFailed is emitted."""

    @pytest.mark.asyncio
    async def test_simulation_failed_event_emitted(self, fast_sleep):
        store = RecordingEventStore()
        sim = Simulator(llm_provider=StubLLMProvider(), max_stages=2, event_store=store)

        with patch.object(sim, "_execute_stages", new=AsyncMock(
                side_effect=RuntimeError("orchestrator died"))):
            result = await sim.execute_simulation(_scenario())

        assert result.status == SimulationStatus.FAILED
        failed_events = [e for e in store.appended if e.event_type == "SimulationFailed"]
        assert len(failed_events) == 1
        assert "orchestrator died" in failed_events[0].event_data["error_message"]

    @pytest.mark.asyncio
    async def test_simulation_completed_not_emitted_on_failure(self, fast_sleep):
        store = RecordingEventStore()
        sim = Simulator(llm_provider=StubLLMProvider(), max_stages=2, event_store=store)

        with patch.object(sim, "_execute_stages", new=AsyncMock(side_effect=RuntimeError("x"))):
            await sim.execute_simulation(_scenario())

        completed = [e for e in store.appended if e.event_type == "SimulationCompleted"]
        assert len(completed) == 0


# ---------------------------------------------------------------------------
# Event emission failure isolation
# ---------------------------------------------------------------------------


class TestEventEmissionFailureIsolation:
    """Event store errors must never break the simulation flow."""

    @pytest.mark.asyncio
    async def test_simulation_started_failure_does_not_break_simulation(self, fast_sleep):
        store = RecordingEventStore()
        store._fail_on_append_num = 1  # first append (SimulationStarted) fails
        sim = Simulator(llm_provider=StubLLMProvider(), max_stages=2, event_store=store)

        result = await sim.execute_simulation(_scenario())
        # Simulation still completes successfully.
        assert result.status == SimulationStatus.COMPLETED
        assert len(result.stages) == 2

    @pytest.mark.asyncio
    async def test_stage_started_failure_does_not_break_simulation(self, fast_sleep):
        store = RecordingEventStore()
        store._fail_on_append_num = 2  # second append (first StageStarted) fails
        sim = Simulator(llm_provider=StubLLMProvider(), max_stages=2, event_store=store)

        result = await sim.execute_simulation(_scenario())
        assert result.status == SimulationStatus.COMPLETED
        assert len(result.stages) == 2

    @pytest.mark.asyncio
    async def test_simulation_completed_failure_does_not_break_result(self, fast_sleep):
        store = RecordingEventStore()
        # Last append for 2 stages: 1 + 2*2 + 1 = 6
        store._fail_on_append_num = 6
        sim = Simulator(llm_provider=StubLLMProvider(), max_stages=2, event_store=store)

        result = await sim.execute_simulation(_scenario())
        assert result.status == SimulationStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_get_aggregate_version_failure_does_not_break_simulation(self, fast_sleep):
        store = RecordingEventStore()
        sim = Simulator(llm_provider=StubLLMProvider(), max_stages=1, event_store=store)

        with patch.object(store, "get_aggregate_version", new=AsyncMock(
                side_effect=RuntimeError("DB connection lost"))):
            result = await sim.execute_simulation(_scenario())

        # Simulation still completes — event emission failures are isolated.
        assert result.status == SimulationStatus.COMPLETED
        assert len(result.stages) == 1


# ---------------------------------------------------------------------------
# LLM content generation edge cases
# ---------------------------------------------------------------------------


class TestLLMContentGeneration:
    """Cover fallback and truncation-retry branches."""

    @pytest.mark.asyncio
    async def test_unavailable_provider_uses_fallback_content(self, fast_sleep):
        provider = StubLLMProvider(available=False)
        sim = Simulator(llm_provider=provider, max_stages=1)
        result = await sim.execute_simulation(_scenario())
        assert result.stages[0].success is True
        assert provider.call_count == 0
        assert result.stages[0].content

    @pytest.mark.asyncio
    async def test_empty_llm_response_uses_fallback(self, fast_sleep):
        provider = StubLLMProvider(responses=[StubLLMResponse("")])
        sim = Simulator(llm_provider=provider, max_stages=1)
        result = await sim.execute_simulation(_scenario())
        assert result.stages[0].success is True
        assert result.stages[0].content

    @pytest.mark.asyncio
    async def test_truncated_response_triggers_retry_with_more_tokens(self, fast_sleep):
        provider = StubLLMProvider(responses=[
            StubLLMResponse("partial...", finish_reason="length"),
            StubLLMResponse("full content that is complete", finish_reason="stop"),
        ])
        sim = Simulator(llm_provider=provider, max_stages=1)
        result = await sim.execute_simulation(_scenario())
        assert provider.call_count == 2
        first_max = provider.calls[0]["max_tokens"]
        retry_max = provider.calls[1]["max_tokens"]
        assert retry_max == int(first_max * 1.5)
        assert result.stages[0].content == "full content that is complete"

    @pytest.mark.asyncio
    async def test_llm_raises_uses_fallback_content(self, fast_sleep):
        provider = StubLLMProvider(fail_on_call=1, failure=RuntimeError("api 500"))
        sim = Simulator(llm_provider=provider, max_stages=1)
        result = await sim.execute_simulation(_scenario())
        assert result.stages[0].success is True
        assert result.stages[0].content


# ---------------------------------------------------------------------------
# Active simulation tracking (thread-safe via _active_lock)
# ---------------------------------------------------------------------------


class TestActiveSimulationTracking:
    """The ``_active_simulations`` dict is protected by ``_active_lock``."""

    @pytest.mark.asyncio
    async def test_active_cleared_after_successful_run(self, fast_sleep):
        sim = Simulator(llm_provider=StubLLMProvider(), max_stages=1)
        await sim.execute_simulation(_scenario())
        assert sim._active_simulations == {}

    @pytest.mark.asyncio
    async def test_active_cleared_after_failed_run(self, fast_sleep):
        sim = Simulator(llm_provider=StubLLMProvider(), max_stages=1)
        with patch.object(sim, "_execute_stages", new=AsyncMock(side_effect=RuntimeError("x"))):
            await sim.execute_simulation(_scenario())
        assert sim._active_simulations == {}

    @pytest.mark.asyncio
    async def test_active_cleared_after_critical_break(self, fast_sleep):
        sim = Simulator(llm_provider=StubLLMProvider(), max_stages=3)

        async def critical(scenario, stage_type, description):
            raise RuntimeError("CRITICAL")

        with patch.object(sim, "_generate_stage_content", side_effect=critical):
            await sim.execute_simulation(_scenario())
        assert sim._active_simulations == {}

    @pytest.mark.asyncio
    async def test_active_cleared_with_event_store(self, fast_sleep):
        store = RecordingEventStore()
        sim = Simulator(llm_provider=StubLLMProvider(), max_stages=2, event_store=store)
        await sim.execute_simulation(_scenario())
        assert sim._active_simulations == {}


# ---------------------------------------------------------------------------
# cancel_simulation
# ---------------------------------------------------------------------------


class TestCancelSimulation:
    """``cancel_simulation`` preserves CANCELLED status (bug fix)."""

    def test_unknown_id_returns_false(self):
        sim = Simulator(llm_provider=StubLLMProvider())
        assert sim.cancel_simulation("does-not-exist") is False

    def test_active_id_returns_true_and_removes_entry(self):
        sim = Simulator(llm_provider=StubLLMProvider())
        result = SimulationResult(status=SimulationStatus.RUNNING, scenario_id="scn-1")
        sim._active_simulations[result.result_id] = result

        assert sim.cancel_simulation(result.result_id) is True
        assert result.result_id not in sim._active_simulations

    def test_cancelled_status_is_preserved_not_overwritten_to_failed(self):
        """Bug fix: the old code called mark_completed(success=False) which
        overwrote CANCELLED with FAILED.  The consolidated version sets
        end_time and error_message directly without changing the status."""
        sim = Simulator(llm_provider=StubLLMProvider())
        result = SimulationResult(status=SimulationStatus.RUNNING, scenario_id="scn-1")
        sim._active_simulations[result.result_id] = result

        sim.cancel_simulation(result.result_id)
        assert result.status == SimulationStatus.CANCELLED
        assert result.error_message == "Simulation cancelled by user"
        assert result.end_time is not None


# ---------------------------------------------------------------------------
# Concurrency: parallel simulations
# ---------------------------------------------------------------------------


class TestConcurrentSimulations:
    """Parallel simulations must not cross-contaminate results or events."""

    @pytest.mark.asyncio
    async def test_parallel_runs_have_disjoint_result_ids(self, fast_sleep):
        sim = Simulator(llm_provider=StubLLMProvider(), max_stages=2)
        r1, r2 = await asyncio.gather(
            sim.execute_simulation(_scenario(name="A")),
            sim.execute_simulation(_scenario(name="B")),
        )
        assert r1.result_id != r2.result_id

    @pytest.mark.asyncio
    async def test_parallel_runs_leave_no_active_simulations(self, fast_sleep):
        sim = Simulator(llm_provider=StubLLMProvider(), max_stages=1)
        await asyncio.gather(
            *[sim.execute_simulation(_scenario(name=f"S{i}")) for i in range(10)]
        )
        assert sim._active_simulations == {}

    @pytest.mark.asyncio
    async def test_parallel_runs_with_event_store_have_separate_aggregates(self, fast_sleep):
        store = RecordingEventStore()
        sim = Simulator(llm_provider=StubLLMProvider(), max_stages=1, event_store=store)
        await asyncio.gather(
            *[sim.execute_simulation(_scenario(name=f"S{i}")) for i in range(3)]
        )
        # Each simulation creates its own aggregate_id.
        agg_ids = {e.aggregate_id for e in store.appended}
        assert len(agg_ids) == 3

    @pytest.mark.asyncio
    async def test_parallel_runs_all_complete_successfully(self, fast_sleep):
        sim = Simulator(llm_provider=StubLLMProvider(), max_stages=2)
        results = await asyncio.gather(
            *[sim.execute_simulation(_scenario(name=f"S{i}")) for i in range(5)]
        )
        assert all(r.status == SimulationStatus.COMPLETED for r in results)
        assert all(len(r.stages) == 2 for r in results)

    @pytest.mark.asyncio
    async def test_parallel_sequence_numbers_are_unique(self, fast_sleep):
        sim = Simulator(llm_provider=StubLLMProvider())
        seqs = await asyncio.gather(*[sim._next_sequence() for _ in range(50)])
        assert len(set(seqs)) == 50
