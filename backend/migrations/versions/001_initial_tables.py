"""initial tables

Revision ID: 001
Revises:
Create Date: 2026-02-16
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, JSON, UUID
from pgvector.sqlalchemy import Vector

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "configs",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), server_default="", nullable=False),
        sa.Column("template_source", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "axes",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("config_id", UUID(as_uuid=True), sa.ForeignKey("configs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), server_default="", nullable=False),
        sa.Column("position", sa.Integer(), server_default="0", nullable=False),
        sa.Column("challenger_threshold", sa.Float(), server_default="0.75", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "axes_categories",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("axis_id", UUID(as_uuid=True), sa.ForeignKey("axes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), server_default="", nullable=False),
        sa.Column("position", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "classification_results",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("config_id", UUID(as_uuid=True), sa.ForeignKey("configs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("input_text", sa.Text(), nullable=False),
        sa.Column("results", JSONB(), nullable=False),
        sa.Column("overall_confidence", sa.Float(), nullable=False),
        sa.Column("was_challenged", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("challenger_response", JSONB(), nullable=True),
        sa.Column("model_used", sa.String(50), nullable=False),
        sa.Column("tokens_used", sa.Integer(), server_default="0", nullable=False),
        sa.Column("processing_time_ms", sa.Integer(), server_default="0", nullable=False),
        sa.Column("vote_details", JSONB(), nullable=True),
        sa.Column("embedding", Vector(1536), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_classif_config_created", "classification_results", ["config_id", "created_at"])
    op.create_index("ix_classif_confidence", "classification_results", ["overall_confidence"])

    op.create_table(
        "user_feedbacks",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("classification_id", UUID(as_uuid=True), sa.ForeignKey("classification_results.id", ondelete="CASCADE"), nullable=False),
        sa.Column("axis_id", UUID(as_uuid=True), sa.ForeignKey("axes.id"), nullable=False),
        sa.Column("corrected_category_id", UUID(as_uuid=True), sa.ForeignKey("axes_categories.id"), nullable=True),
        sa.Column("original_category_id", UUID(as_uuid=True), sa.ForeignKey("axes_categories.id"), nullable=True),
        sa.Column("reasoning_feedback", sa.Text(), nullable=True),
        sa.Column("feedback_type", sa.String(20), nullable=False),
        sa.Column("review_status", sa.String(20), server_default=sa.text("'corrected'"), nullable=False),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_feedback_classification", "user_feedbacks", ["classification_id"])

    op.create_table(
        "evaluation_results",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("config_id", UUID(as_uuid=True), sa.ForeignKey("configs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("eval_type", sa.String(20), nullable=False),
        sa.Column("results", JSONB(), nullable=False),
        sa.Column("confusion_matrix", JSONB(), nullable=True),
        sa.Column("accuracy_per_axis", JSONB(), nullable=True),
        sa.Column("overall_accuracy", sa.Float(), nullable=True),
        sa.Column("recommendations", JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_eval_config_created", "evaluation_results", ["config_id", "created_at"])

    op.create_table(
        "learned_rules",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("config_id", UUID(as_uuid=True), sa.ForeignKey("configs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("axis_id", UUID(as_uuid=True), sa.ForeignKey("axes.id", ondelete="SET NULL"), nullable=True),
        sa.Column("rule_text", sa.Text(), nullable=False),
        sa.Column("source_feedback_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("validated_by_user", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("active", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "prompt_versions",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("config_id", UUID(as_uuid=True), sa.ForeignKey("configs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("change_type", sa.String(50), nullable=False),
        sa.Column("change_description", sa.Text(), nullable=False),
        sa.Column("prompt_snapshot", JSON(), nullable=False),
        sa.Column("learned_rules_snapshot", JSON(), server_default="[]", nullable=False),
        sa.Column("challenger_thresholds_snapshot", JSON(), server_default="{}", nullable=False),
        sa.Column("accuracy_at_creation", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "chat_messages",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("config_id", UUID(as_uuid=True), sa.ForeignKey("configs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("intent", sa.String(30), nullable=True),
        sa.Column("metadata", JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("chat_messages")
    op.drop_table("prompt_versions")
    op.drop_table("learned_rules")
    op.drop_table("evaluation_results")
    op.drop_table("user_feedbacks")
    op.drop_table("classification_results")
    op.drop_table("axes_categories")
    op.drop_table("axes")
    op.drop_table("configs")
