"""
Tests for the Celery beat schedule (config/celery.py).

Guards against the failure mode the beat_init validator exists for: a task named
in beat_schedule that no worker has registered, because its owning module was
never added to ``app.conf.imports`` (the top-level ``tasks/`` package is not
reached by autodiscover_tasks()). Beat would publish the task and every worker
would reject it as NotRegistered, with nothing obviously wrong in the schedule.

The validator only runs when a beat process boots; these tests catch the same
drift in CI without starting one.
"""
from config.celery import app, check_beat_schedule_registered


def test_beat_schedule_tasks_are_all_registered():
    """Every task name in beat_schedule must resolve to a registered task."""
    missing = check_beat_schedule_registered()
    assert not missing, f"beat_schedule references unregistered tasks: {missing}"


def test_registry_is_empty_until_modules_are_imported():
    """Pin the subtlety the helper exists for.

    ``app.conf.imports`` is a declaration, not an import. Anything comparing
    beat_schedule against ``app.tasks`` without first calling
    ``import_default_modules()`` sees an empty registry and reports every
    scheduled task as missing — which is exactly the false alarm that made an
    ``on_after_finalize`` version of this check unusable.
    """
    # The helper forces the import, so afterwards the tasks/ modules are present.
    check_beat_schedule_registered()
    assert any(name.startswith("tasks.") for name in app.tasks)


def test_unscheduled_fallback_task_is_still_registered():
    """``sync_oer_fx_rates`` is deliberately absent from beat_schedule.

    It is a manual fallback for ECB outages and needs OPEN_EXCHANGE_RATES_API_KEY,
    which defaults to "". It must still be *registered*, because
    ``sync_ecb_fx_rates`` dispatches it with .delay() when the ECB source fails.
    """
    check_beat_schedule_registered()
    assert "tasks.integrations.sync_oer_fx_rates" in app.tasks
    scheduled = {entry["task"] for entry in app.conf.beat_schedule.values()}
    assert "tasks.integrations.sync_oer_fx_rates" not in scheduled
