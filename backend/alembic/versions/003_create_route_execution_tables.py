"""create route execution tables

Revision ID: 003_create_route_execution_tables
Revises: 002_create_core_logistics_tables
Create Date: 2026-08-25 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003_create_route_execution_tables'
down_revision: Union[str, None] = '002_create_core_logistics_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Routes table
    op.create_table(
        'routes',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=True),
        sa.Column('driver_id', sa.String(length=36), sa.ForeignKey('drivers.id', ondelete='SET NULL'), nullable=True),
        sa.Column('vehicle_id', sa.String(length=36), sa.ForeignKey('vehicles.id', ondelete='SET NULL'), nullable=True),
        sa.Column('warehouse_id', sa.String(length=36), sa.ForeignKey('warehouses.id', ondelete='SET NULL'), nullable=True),
        sa.Column('total_distance', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('estimated_duration', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('optimization_score', sa.Float(), nullable=False, server_default='100.0'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='PLANNED'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_routes_status'), 'routes', ['status'], unique=False)
    op.create_index(op.f('ix_routes_driver_id'), 'routes', ['driver_id'], unique=False)

    # 2. Route Stops table
    op.create_table(
        'route_stops',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('route_id', sa.String(length=36), sa.ForeignKey('routes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('order_id', sa.String(length=36), sa.ForeignKey('orders.id', ondelete='SET NULL'), nullable=True),
        sa.Column('sequence', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('estimated_arrival', sa.DateTime(), nullable=True),
        sa.Column('actual_arrival', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='PENDING'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_route_stops_route_id'), 'route_stops', ['route_id'], unique=False)
    op.create_index(op.f('ix_route_stops_order_id'), 'route_stops', ['order_id'], unique=False)

    # 3. Delivery Events table
    op.create_table(
        'delivery_events',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('order_id', sa.String(length=36), sa.ForeignKey('orders.id', ondelete='SET NULL'), nullable=True),
        sa.Column('driver_id', sa.String(length=36), sa.ForeignKey('drivers.id', ondelete='SET NULL'), nullable=True),
        sa.Column('route_id', sa.String(length=36), sa.ForeignKey('routes.id', ondelete='SET NULL'), nullable=True),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('event_metadata', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_delivery_events_route_id'), 'delivery_events', ['route_id'], unique=False)
    op.create_index(op.f('ix_delivery_events_order_id'), 'delivery_events', ['order_id'], unique=False)
    op.create_index(op.f('ix_delivery_events_driver_id'), 'delivery_events', ['driver_id'], unique=False)

    # 4. Optimization Jobs table
    op.create_table(
        'optimization_jobs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='PENDING'),
        sa.Column('parameters', sa.JSON(), nullable=True),
        sa.Column('result', sa.JSON(), nullable=True),
        sa.Column('optimization_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('total_distance_km', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('total_duration_min', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('optimization_jobs')
    op.drop_table('delivery_events')
    op.drop_table('route_stops')
    op.drop_table('routes')
