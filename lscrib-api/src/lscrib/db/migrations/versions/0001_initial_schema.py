"""initial schema

Baseline del esquema para 0.1.0: tablas `job`, `segment` y `settings` (singleton).
Autogenerada y revisada a mano. Las BD creadas antes con `create_all` se marcan
(stamp) en esta revisión al arrancar, sin recrear tablas — ver `lscrib.db.migrate`.

Revision ID: 0001
Revises:
Create Date: 2026-07-09
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
import sqlmodel


revision: str = '0001'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table('job',
    sa.Column('id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('original_filename', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('file_hash', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('media_path', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('duration_sec', sa.Integer(), nullable=True),
    sa.Column('media_type', sa.Enum('AUDIO', 'VIDEO', name='mediatype'), nullable=False),
    sa.Column('language', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('model', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('prompt', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('status', sa.Enum('UPLOADED', 'QUEUED', 'NORMALIZING', 'TRANSCRIBING', 'COMPLETED', 'FAILED', 'CANCELED', name='jobstatus'), nullable=False),
    sa.Column('progress', sa.Float(), nullable=False),
    sa.Column('position', sa.Integer(), nullable=False),
    sa.Column('error', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('completed_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('job', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_job_file_hash'), ['file_hash'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_position'), ['position'], unique=False)

    op.create_table('settings',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('default_model', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('default_language', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('max_file_mb', sa.Integer(), nullable=False),
    sa.Column('theme', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('segment',
    sa.Column('id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('job_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('index', sa.Integer(), nullable=False),
    sa.Column('start_ms', sa.Integer(), nullable=False),
    sa.Column('end_ms', sa.Integer(), nullable=False),
    sa.Column('text', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('words', sa.JSON(), nullable=True),
    sa.ForeignKeyConstraint(['job_id'], ['job.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('segment', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_segment_job_id'), ['job_id'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('segment', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_segment_job_id'))

    op.drop_table('segment')
    op.drop_table('settings')
    with op.batch_alter_table('job', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_job_position'))
        batch_op.drop_index(batch_op.f('ix_job_file_hash'))

    op.drop_table('job')
