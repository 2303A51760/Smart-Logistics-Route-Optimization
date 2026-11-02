"""create ai_recommendations table

Revision ID: 007_create_ai_recommendations_table
Revises: 006_create_audit_logs_table
Create Date: 2026-08-27 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '007_create_ai_recommendations_table'
down_revision: Union[str, None] = '006_create_audit_logs_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'ai_recommendations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('recommendation_type', sa.String(length=50), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.String(length=50), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('recommendation', sa.Text(), nullable=False),
        sa.Column('reasons', sa.JSON(), nullable=True),
        sa.Column('factors', sa.JSON(), nullable=True),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('model_version', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.String(length=36), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ai_recommendations_id'), 'ai_recommendations', ['id'], unique=False)
    op.create_index(op.f('ix_ai_recommendations_recommendation_type'), 'ai_recommendations', ['recommendation_type'], unique=False)
    op.create_index(op.f('ix_ai_recommendations_entity_type'), 'ai_recommendations', ['entity_type'], unique=False)
    op.create_index(op.f('ix_ai_recommendations_entity_id'), 'ai_recommendations', ['entity_id'], unique=False)
    op.create_index(op.f('ix_ai_recommendations_status'), 'ai_recommendations', ['status'], unique=False)
    op.create_index(op.f('ix_ai_recommendations_created_at'), 'ai_recommendations', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_ai_recommendations_created_at'), table_name='ai_recommendations')
    op.drop_index(op.f('ix_ai_recommendations_status'), table_name='ai_recommendations')
    op.drop_index(op.f('ix_ai_recommendations_entity_id'), table_name='ai_recommendations')
    op.drop_index(op.f('ix_ai_recommendations_entity_type'), table_name='ai_recommendations')
    op.drop_index(op.f('ix_ai_recommendations_recommendation_type'), table_name='ai_recommendations')
    op.drop_index(op.f('ix_ai_recommendations_id'), table_name='ai_recommendations')
    op.drop_table('ai_recommendations')
