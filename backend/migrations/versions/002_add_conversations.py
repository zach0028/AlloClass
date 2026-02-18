"""add conversations

Revision ID: 002
Revises: 001
Create Date: 2026-02-17
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "conversations",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("config_id", UUID(as_uuid=True), sa.ForeignKey("configs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_conversations_config_updated", "conversations", ["config_id", "updated_at"])

    op.add_column(
        "chat_messages",
        sa.Column("conversation_id", UUID(as_uuid=True), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=True),
    )
    op.create_index("ix_chat_messages_conversation", "chat_messages", ["conversation_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_chat_messages_conversation", table_name="chat_messages")
    op.drop_column("chat_messages", "conversation_id")
    op.drop_index("ix_conversations_config_updated", table_name="conversations")
    op.drop_table("conversations")
