from __future__ import annotations

from uuid import UUID, uuid4

from backend.core.config import settings

try:
    import psycopg
except ImportError:  # pragma: no cover - depends on runtime environment
    psycopg = None


def _to_driver_dsn(database_url: str) -> str:
    if database_url.startswith("postgresql+psycopg://"):
        return database_url.replace("postgresql+psycopg://", "postgresql://", 1)
    return database_url


class PostgresRoutingRepository:
    def __init__(self, dsn: str | None = None) -> None:
        if psycopg is None:
            raise RuntimeError("psycopg is required for PostgresRoutingRepository")
        self._dsn = _to_driver_dsn(dsn or settings.database_url)
        self._connect_timeout_seconds = 3

    def get_thread_override(self, channel: str, thread_id: str) -> str | None:
        query = """
            SELECT project_id::text
            FROM thread_project_overrides
            WHERE channel = %s AND thread_id = %s
            LIMIT 1
        """
        with psycopg.connect(self._dsn, connect_timeout=self._connect_timeout_seconds) as conn, conn.cursor() as cur:
            cur.execute(query, (channel, thread_id))
            row = cur.fetchone()
        return row[0] if row else None

    def get_active_projects_for_sender(self, channel: str, sender_key: str) -> list[str]:
        query = """
            SELECT project_id::text
            FROM project_contacts
            WHERE channel = %s AND sender_key = %s AND is_active = TRUE
            ORDER BY created_at DESC
        """
        with psycopg.connect(self._dsn, connect_timeout=self._connect_timeout_seconds) as conn, conn.cursor() as cur:
            cur.execute(query, (channel, sender_key))
            rows = cur.fetchall()
        return [row[0] for row in rows]

    def enqueue_unrouted_message(
        self,
        *,
        channel: str,
        sender_key: str,
        thread_id: str | None,
        raw_message: str,
        candidate_project_ids: list[str],
    ) -> None:
        query = """
            INSERT INTO unrouted_inbox
            (id, channel, sender_key, thread_id, raw_message, candidate_project_ids, status)
            VALUES (%s, %s, %s, %s, %s, %s::uuid[], 'needs_routing')
        """
        candidate_uuids = [UUID(project_id) for project_id in candidate_project_ids]
        with psycopg.connect(self._dsn, connect_timeout=self._connect_timeout_seconds) as conn, conn.cursor() as cur:
            cur.execute(
                query,
                (
                    uuid4(),
                    channel,
                    sender_key,
                    thread_id,
                    raw_message,
                    candidate_uuids,
                ),
            )
            conn.commit()

    def assign_unrouted_message(
        self,
        *,
        unrouted_id: str,
        project_id: str,
        pm_user_id: str,
    ) -> None:
        select_query = """
            SELECT channel, thread_id
            FROM unrouted_inbox
            WHERE id = %s::uuid AND status = 'needs_routing'
            LIMIT 1
        """
        update_query = """
            UPDATE unrouted_inbox
            SET status = 'routed', routed_project_id = %s::uuid, routed_at = now()
            WHERE id = %s::uuid
        """
        override_query = """
            INSERT INTO thread_project_overrides (id, channel, thread_id, project_id, set_by_pm_user_id)
            VALUES (%s, %s, %s, %s::uuid, %s)
            ON CONFLICT (channel, thread_id)
            DO UPDATE SET project_id = EXCLUDED.project_id, set_by_pm_user_id = EXCLUDED.set_by_pm_user_id
        """

        with psycopg.connect(self._dsn, connect_timeout=self._connect_timeout_seconds) as conn, conn.cursor() as cur:
            cur.execute(select_query, (unrouted_id,))
            row = cur.fetchone()
            if row is None:
                raise ValueError("unrouted message not found or already routed")

            channel, thread_id = row
            cur.execute(update_query, (project_id, unrouted_id))

            if thread_id:
                cur.execute(
                    override_query,
                    (uuid4(), channel, thread_id, project_id, pm_user_id),
                )
            conn.commit()
