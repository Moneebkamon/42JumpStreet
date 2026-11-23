"""Write audit entries for sensitive actions. Kept as its own module so every service logs the same way."""
from app.repositories import audit_repo


def record(actor: str, action: str, object_type: str, object_id: str | int, detail: str = "") -> None:
    audit_repo.log(actor, action, object_type, str(object_id), detail)


def recent(limit: int = 100, object_type: str | None = None, object_id: str | None = None) -> list[dict]:
    return audit_repo.list_recent(limit, object_type, object_id)
