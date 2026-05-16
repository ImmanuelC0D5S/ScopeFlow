from backend.ingestion.routing import resolve_project_for_message


class FakeRoutingRepository:
    def __init__(self) -> None:
        self.thread_overrides: dict[tuple[str, str], str] = {}
        self.contact_map: dict[tuple[str, str], list[str]] = {}
        self.unrouted: list[dict] = []

    def get_thread_override(self, channel: str, thread_id: str) -> str | None:
        return self.thread_overrides.get((channel, thread_id))

    def get_active_projects_for_sender(self, channel: str, sender_key: str) -> list[str]:
        return self.contact_map.get((channel, sender_key), [])

    def enqueue_unrouted_message(
        self,
        *,
        channel: str,
        sender_key: str,
        thread_id: str | None,
        raw_message: str,
        candidate_project_ids: list[str],
    ) -> None:
        self.unrouted.append(
            {
                "channel": channel,
                "sender_key": sender_key,
                "thread_id": thread_id,
                "raw_message": raw_message,
                "candidate_project_ids": candidate_project_ids,
            }
        )


def test_thread_override_wins() -> None:
    repository = FakeRoutingRepository()
    repository.thread_overrides[("email", "th-1")] = "proj-123"
    decision = resolve_project_for_message(
        repository=repository,
        channel="email",
        sender="client@example.com",
        thread_id="th-1",
        raw_message="Need timeline update.",
    )
    assert decision.status == "resolved"
    assert decision.project_id == "proj-123"


def test_single_match_resolves() -> None:
    repository = FakeRoutingRepository()
    repository.contact_map[("email", "client@example.com")] = ["proj-888"]
    decision = resolve_project_for_message(
        repository=repository,
        channel="email",
        sender="client@example.com",
        raw_message="Need timeline update.",
    )
    assert decision.status == "resolved"
    assert decision.project_id == "proj-888"


def test_multiple_matches_enqueue_unrouted() -> None:
    repository = FakeRoutingRepository()
    repository.contact_map[("email", "client@example.com")] = ["proj-1", "proj-2"]
    decision = resolve_project_for_message(
        repository=repository,
        channel="email",
        sender="client@example.com",
        raw_message="Need timeline update.",
    )
    assert decision.status == "needs_routing"
    assert decision.project_id is None
    assert len(repository.unrouted) == 1
