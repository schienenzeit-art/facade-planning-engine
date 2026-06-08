from abc import ABC, abstractmethod
from typing import Any


class AuditPort(ABC):
    @abstractmethod
    def log_operation(self, job_id: str, operation_type: str, data: dict[str, Any]) -> None: ...

    @abstractmethod
    def finalize(self, job_id: str) -> None: ...
