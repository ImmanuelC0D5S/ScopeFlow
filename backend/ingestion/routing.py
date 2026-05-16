from dataclasses import dataclass
from typing import Protocol


def normalize_sender(channel: str, sender: str, workspace_id: str | None = None) -> str:
    normalized_channel = channel.strip().lower()
    normalized_sender = sender.strip().lower()

    if normalized_channel == "email":
        return normalized_sender

    if normalized_channel == "slack":
        if workspace_id:
            return f"{normalized_sender}@{workspace_id.strip().lower()}"
        return normalized_sender

    return normalized_sender


@dataclass
class RoutingDecision:
    status: str
    project_id: str | None
    candidate_project_ids: list[str]


class RoutingRepository(Protocol):
    def get_thread_override(self, channel: str, thread_id: str) -> str | None:
        ...

    def get_active_projects_for_sender(self, channel: str, sender_key: str) -> list[str]:
        ...

    def enqueue_unrouted_message(
        self,
        *,
        channel: str,
        sender_key: str,
        thread_id: str | None,
        raw_message: str,
        candidate_project_ids: list[str],
    ) -> None:
        ...


def resolve_project_for_message(
    *,
    repository: RoutingRepository,
    channel: str,
    sender: str,
    raw_message: str,
    thread_id: str | None = None,
    workspace_id: str | None = None,
) -> RoutingDecision:
    normalized_channel = channel.strip().lower()
    sender_key = normalize_sender(normalized_channel, sender, workspace_id)

    if thread_id:
        override_project_id = repository.get_thread_override(normalized_channel, thread_id)
        if override_project_id:
            return RoutingDecision(
                status="resolved",
                project_id=override_project_id,
                candidate_project_ids=[override_project_id],
            )

    project_ids = repository.get_active_projects_for_sender(normalized_channel, sender_key)

    if len(project_ids) == 1:
        return RoutingDecision(
            status="resolved",
            project_id=project_ids[0],
            candidate_project_ids=project_ids,
        )

    repository.enqueue_unrouted_message(
        channel=normalized_channel,
        sender_key=sender_key,
        thread_id=thread_id,
        raw_message=raw_message,
        candidate_project_ids=project_ids,
    )
    return RoutingDecision(
        status="needs_routing",
        project_id=None,
        candidate_project_ids=project_ids,
    )
