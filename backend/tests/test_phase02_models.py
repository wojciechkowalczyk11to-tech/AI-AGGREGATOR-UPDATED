from __future__ import annotations

from sqlalchemy import UniqueConstraint

from app.db.models import (
    AuditLog,
    ChatSession,
    InviteCode,
    Message,
    Payment,
    RagItem,
    ToolCounter,
    UsageLedger,
    User,
    UserMemory,
    UserRole,
)


def _column_names(model: type) -> set[str]:
    return {column.name for column in model.__table__.columns}


def _index_names(model: type) -> set[str]:
    return {index.name for index in model.__table__.indexes}


def _has_unique_constraint(model: type, name: str) -> bool:
    for constraint in model.__table__.constraints:
        if isinstance(constraint, UniqueConstraint) and constraint.name == name:
            return True
    return False


class TestUserModelSchema:
    def test_user_has_expected_columns(self) -> None:
        assert {"id", "telegram_id", "role", "settings", "created_at", "last_seen_at"}.issubset(_column_names(User))

    def test_user_has_telegram_id_index(self) -> None:
        assert "ix_users_telegram_id" in _index_names(User)

    def test_user_role_enum_values(self) -> None:
        assert UserRole.DEMO.value == "DEMO"
        assert UserRole.FULL_ACCESS.value == "FULL_ACCESS"

    def test_user_last_seen_at_has_onupdate(self) -> None:
        assert User.__table__.c.last_seen_at.onupdate is not None


class TestSessionModelSchema:
    def test_session_has_expected_columns(self) -> None:
        assert {"id", "user_id", "mode", "message_count", "last_active_at"}.issubset(_column_names(ChatSession))

    def test_session_has_user_index(self) -> None:
        assert "ix_sessions_user_id" in _index_names(ChatSession)

    def test_session_relationship_to_user_exists(self) -> None:
        assert ChatSession.user.property.back_populates == "sessions"


class TestMessageModelSchema:
    def test_message_has_expected_columns(self) -> None:
        assert {"id", "session_id", "role", "content", "metadata", "created_at"}.issubset(_column_names(Message))

    def test_message_has_composite_index(self) -> None:
        assert "ix_messages_session_id_created_at" in _index_names(Message)

    def test_message_relationship_to_session_exists(self) -> None:
        assert Message.session.property.back_populates == "messages"


class TestLedgerModelSchema:
    def test_ledger_has_expected_columns(self) -> None:
        assert {
            "id",
            "user_id",
            "session_id",
            "provider",
            "model",
            "tool_costs",
            "created_at",
        }.issubset(_column_names(UsageLedger))

    def test_ledger_has_composite_index(self) -> None:
        assert "ix_usage_ledger_user_id_created_at" in _index_names(UsageLedger)

    def test_ledger_relationships_exist(self) -> None:
        assert UsageLedger.user.property.back_populates == "usage_ledgers"
        assert UsageLedger.session.property.back_populates == "usage_ledgers"


class TestToolCounterModelSchema:
    def test_tool_counter_has_expected_columns(self) -> None:
        assert {"id", "user_id", "date", "grok_calls", "total_cost_usd"}.issubset(_column_names(ToolCounter))

    def test_tool_counter_has_unique_constraint(self) -> None:
        assert _has_unique_constraint(ToolCounter, "uq_tool_counters_user_id_date")

    def test_tool_counter_relationship_to_user_exists(self) -> None:
        assert ToolCounter.user.property.back_populates == "tool_counters"


class TestAuditLogModelSchema:
    def test_audit_log_has_expected_columns(self) -> None:
        assert {"id", "actor_telegram_id", "action", "details", "created_at"}.issubset(_column_names(AuditLog))

    def test_audit_log_has_created_at_index(self) -> None:
        assert "ix_audit_logs_created_at" in _index_names(AuditLog)

    def test_audit_log_has_action_index(self) -> None:
        assert "ix_audit_logs_action" in _index_names(AuditLog)


class TestInviteCodeModelSchema:
    def test_invite_code_has_expected_columns(self) -> None:
        assert {"id", "code_hash", "role", "expires_at", "uses_left", "created_at"}.issubset(_column_names(InviteCode))

    def test_invite_code_code_hash_is_unique(self) -> None:
        assert InviteCode.__table__.c.code_hash.unique is True

    def test_invite_code_role_default_is_demo(self) -> None:
        assert InviteCode.__table__.c.role.default.arg == UserRole.DEMO


class TestRagItemModelSchema:
    def test_rag_item_has_expected_columns(self) -> None:
        assert {"id", "user_id", "scope", "source_type", "status", "metadata"}.issubset(_column_names(RagItem))

    def test_rag_item_relationship_to_user_exists(self) -> None:
        assert RagItem.user.property.back_populates == "rag_items"

    def test_rag_item_defaults_exist(self) -> None:
        assert RagItem.__table__.c.scope.default.arg == "user"
        assert RagItem.__table__.c.status.default.arg == "pending"


class TestUserMemoryModelSchema:
    def test_user_memory_has_expected_columns(self) -> None:
        assert {"id", "user_id", "key", "value", "created_at", "updated_at"}.issubset(_column_names(UserMemory))

    def test_user_memory_has_unique_constraint(self) -> None:
        assert _has_unique_constraint(UserMemory, "uq_user_memories_user_id_key")

    def test_user_memory_relationship_to_user_exists(self) -> None:
        assert UserMemory.user.property.back_populates == "memories"


class TestPaymentModelSchema:
    def test_payment_has_expected_columns(self) -> None:
        assert {
            "id",
            "user_id",
            "plan",
            "stars_amount",
            "currency",
            "status",
            "created_at",
        }.issubset(_column_names(Payment))

    def test_payment_charge_id_is_unique(self) -> None:
        assert Payment.__table__.c.telegram_payment_charge_id.unique is True

    def test_payment_relationship_to_user_exists(self) -> None:
        assert Payment.user.property.back_populates == "payments"
