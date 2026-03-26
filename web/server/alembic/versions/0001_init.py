"""init"""
from __future__ import annotations
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "notes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("content_md", sa.Text(), nullable=False),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_table(
        "posts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=200), nullable=False, unique=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("content_md", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="draft"),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("cover_image_file_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_table(
        "file_objects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("owner_scope", sa.String(length=20), nullable=False),
        sa.Column("kind", sa.String(length=50), nullable=False),
        sa.Column("bucket", sa.String(length=100), nullable=False),
        sa.Column("object_key", sa.String(length=512), nullable=False),
        sa.Column("mime", sa.String(length=200), nullable=False),
        sa.Column("size", sa.BigInteger(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_table(
        "import_assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("visibility", sa.String(length=20), nullable=False),
        sa.Column("source_file_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rendered_file_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("asset_file_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("content_md", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

def downgrade():
    op.drop_table("import_assets")
    op.drop_table("file_objects")
    op.drop_table("posts")
    op.drop_table("notes")
