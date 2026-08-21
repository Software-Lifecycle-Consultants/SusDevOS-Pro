"""
Tests for tasks/reports.py — FIX F4: the `report_failed` notification on
`generate_report` must not fire until the terminal retry attempt.

Previously `_notify_failed()` ran on every failed attempt, including ones
that would still be retried. A transient failure (e.g. an S3 timeout) on
attempt 1 told the user "Report generation failed" even though attempt 2
succeeded 60 seconds later — a false failure notice that could also prompt
the user to re-request a report already in flight. The `JobStatus = 4`
write is *not* deferred: "Failed" honestly describes the job's state
between attempts, only the notification is gated on
`self.request.retries >= self.max_retries`.
"""
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.django_db


def _make_job(entity, admin_user):
    from apps.reports.models import ReportJobs

    return ReportJobs.objects.create(
        EntityId=entity,
        RequestedBy=admin_user,
        ReportType="emissions_summary",
        Format="pdf",
    )


class TestGenerateReportFailureNotification:
    """`generate_report` is invoked via `generate_report.run(job_id)` with a
    manually pushed request context (`Task.push_request(retries=N)`) rather
    than `.delay()`/`.apply_async()`, and rather than `.apply()`.

    Reason: this repo's settings do not set CELERY_TASK_ALWAYS_EAGER and no
    broker is available in the test run. `push_request()` leaves
    `self.request.called_directly` at its default of True (it only overrides
    the kwargs given, e.g. `retries`), and that is exactly the flag Celery's
    `Task.retry()` checks to decide whether to actually enqueue a retry via
    the broker (`called_directly=False`, needs a live connection) or to just
    re-raise the original exception in place (`called_directly=True`, no
    broker needed). Since `generate_report` always calls
    `raise self.retry(exc=exc)` on failure, every failing call in this test
    class ends by re-raising the original exception — which is why each is
    wrapped in `pytest.raises`. This exercises the notification-decision
    logic (the actual thing under test) without needing Celery/Redis.
    """

    def test_notification_deferred_while_retries_remain(self, entity, admin_user):
        from tasks.reports import generate_report

        job = _make_job(entity, admin_user)
        boom = RuntimeError("transient S3 timeout")

        generate_report.push_request(retries=0)
        try:
            with patch("tasks.reports._render_report", side_effect=boom), \
                 patch("tasks.reports._notify_failed") as mock_notify_failed, \
                 patch("tasks.reports._notify_complete") as mock_notify_complete:
                with pytest.raises(RuntimeError):
                    generate_report.run(job.ReportJobId)
        finally:
            generate_report.pop_request()

        mock_notify_failed.assert_not_called()
        mock_notify_complete.assert_not_called()

        job.refresh_from_db()
        assert job.JobStatus == 4
        assert "transient S3 timeout" in job.ErrorMessage

    def test_notification_sent_on_terminal_attempt(self, entity, admin_user):
        from tasks.reports import generate_report

        job = _make_job(entity, admin_user)
        boom = RuntimeError("still broken")

        # max_retries=2 -> attempts are retries=0, 1, 2. retries == max_retries
        # is the third and final attempt: no retry follows, so this is the
        # only point the user should be told it failed.
        generate_report.push_request(retries=generate_report.max_retries)
        try:
            with patch("tasks.reports._render_report", side_effect=boom), \
                 patch("tasks.reports._notify_failed") as mock_notify_failed:
                with pytest.raises(RuntimeError):
                    generate_report.run(job.ReportJobId)
        finally:
            generate_report.pop_request()

        mock_notify_failed.assert_called_once()
        notified_job = mock_notify_failed.call_args.args[0]
        assert notified_job.ReportJobId == job.ReportJobId

        job.refresh_from_db()
        assert job.JobStatus == 4

    def test_happy_path_still_notifies_completion(self, entity, admin_user):
        from tasks.reports import generate_report

        job = _make_job(entity, admin_user)

        generate_report.push_request(retries=0)
        try:
            with patch("tasks.reports._render_report", return_value=("key.pdf", 123)), \
                 patch("tasks.reports._notify_complete") as mock_notify_complete, \
                 patch("tasks.reports._notify_failed") as mock_notify_failed:
                generate_report.run(job.ReportJobId)
        finally:
            generate_report.pop_request()

        mock_notify_complete.assert_called_once()
        mock_notify_failed.assert_not_called()

        job.refresh_from_db()
        assert job.JobStatus == 3
