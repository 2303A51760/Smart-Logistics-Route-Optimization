"""create delivery_points table

Revision ID: 008_create_delivery_points_table
Revises: 007_create_ai_recommendations_table
Create Date: 2026-11-01 19:45:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '008_create_delivery_points_table'
down_revision: Union[str, None] = '007_create_ai_recommendations_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'delivery_points',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('order_id', sa.String(length=100), nullable=False),
        sa.Column('customer_name', sa.String(length=150), nullable=False),
        sa.Column('address', sa.String(length=255), nullable=False),
        sa.Column('lat', sa.Float(), nullable=False),
        sa.Column('lng', sa.Float(), nullable=False),
        sa.Column('demand_weight_kg', sa.Float(), nullable=False, server_default='10.0'),
        sa.Column('time_window_start', sa.DateTime(), nullable=True),
        sa.Column('time_window_end', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='PENDING'),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('route_id', sa.String(length=36), sa.ForeignKey('routes.id', ondelete='SET NULL'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('order_id', name='uq_delivery_points_order_id'),
    )
    op.create_index(op.f('ix_delivery_points_order_id'), 'delivery_points', ['order_id'], unique=True)
    op.create_index(op.f('ix_delivery_points_route_id'), 'delivery_points', ['route_id'], unique=False)
    op.create_index(op.f('ix_delivery_points_status'), 'delivery_points', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_delivery_points_status'), table_name='delivery_points')
    op.drop_index(op.f('ix_delivery_points_route_id'), table_name='delivery_points')
    op.drop_index(op.f('ix_delivery_points_order_id'), table_name='delivery_points')
    op.drop_table('delivery_points')

