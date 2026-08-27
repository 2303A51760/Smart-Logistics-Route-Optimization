"""create maintenance and notifications tables

Revision ID: 005_create_maintenance_and_notifications_tables
Revises: 004_create_driver_locations_table
Create Date: 2026-08-26 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '005_create_maintenance_and_notifications_tables'
down_revision: Union[str, None] = '004_create_driver_locations_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create vehicle_maintenance table
    op.create_table(
        'vehicle_maintenance',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('vehicle_id', sa.String(length=36), sa.ForeignKey('vehicles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('maintenance_type', sa.String(length=50), nullable=False, server_default='GENERAL_INSPECTION'),
        sa.Column('maintenance_date', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('mileage', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('next_maintenance_mileage', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('cost', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='COMPLETED'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_vehicle_maintenance_vehicle_id'), 'vehicle_maintenance', ['vehicle_id'], unique=False)
    op.create_index(op.f('ix_vehicle_maintenance_maintenance_date'), 'vehicle_maintenance', ['maintenance_date'], unique=False)

    # 2. Create notifications table
    op.create_table(
        'notifications',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('recipient_user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('recipient_role', sa.String(length=30), nullable=True),
        sa.Column('driver_id', sa.String(length=36), sa.ForeignKey('drivers.id', ondelete='SET NULL'), nullable=True),
        sa.Column('vehicle_id', sa.String(length=36), nullable=True),
        sa.Column('route_id', sa.String(length=36), nullable=True),
        sa.Column('order_id', sa.String(length=36), nullable=True),
        sa.Column('title', sa.String(length=150), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('alert_type', sa.String(length=50), nullable=False, server_default='SYSTEM_ALERT'),
        sa.Column('severity', sa.String(length=20), nullable=False, server_default='INFO'),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notifications_recipient_user_id'), 'notifications', ['recipient_user_id'], unique=False)
    op.create_index(op.f('ix_notifications_recipient_role'), 'notifications', ['recipient_role'], unique=False)
    op.create_index(op.f('ix_notifications_driver_id'), 'notifications', ['driver_id'], unique=False)
    op.create_index(op.f('ix_notifications_vehicle_id'), 'notifications', ['vehicle_id'], unique=False)
    op.create_index(op.f('ix_notifications_alert_type'), 'notifications', ['alert_type'], unique=False)
    op.create_index(op.f('ix_notifications_is_read'), 'notifications', ['is_read'], unique=False)
    op.create_index(op.f('ix_notifications_created_at'), 'notifications', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_notifications_created_at'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_is_read'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_alert_type'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_vehicle_id'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_driver_id'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_recipient_role'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_recipient_user_id'), table_name='notifications')
    op.drop_table('notifications')

    op.drop_index(op.f('ix_vehicle_maintenance_maintenance_date'), table_name='vehicle_maintenance')
    op.drop_index(op.f('ix_vehicle_maintenance_vehicle_id'), table_name='vehicle_maintenance')
    op.drop_table('vehicle_maintenance')
