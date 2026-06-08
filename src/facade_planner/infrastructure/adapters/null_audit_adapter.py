from typing import Any

from facade_planner.application.ports.audit_port import AuditPort


class NullAuditAdapter(AuditPort):
    """No-op audit adapter used until EPIC-010 is implemented."""

    def log_operation(self, job_id: str, operation_type: str, data: dict[str, Any]) -> None:
        pass

    def finalize(self, job_id: str) -> None:
        pass
