"""create core logistics tables

Revision ID: 002_create_core_logistics_tables
Revises: 001_create_users_table
Create Date: 2026-08-24 22:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002_create_core_logistics_tables'
down_revision: Union[str, None] = '001_create_users_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Drivers table
    op.create_table(
        'drivers',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('license_number', sa.String(length=50), nullable=False),
        sa.Column('phone', sa.String(length=30), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='AVAILABLE'),
        sa.Column('current_latitude', sa.Float(), nullable=True, server_default='40.7128'),
        sa.Column('current_longitude', sa.Float(), nullable=True, server_default='-74.0060'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_drivers_license_number'), 'drivers', ['license_number'], unique=True)

    # 2. Vehicles table
    op.create_table(
        'vehicles',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('driver_id', sa.String(length=36), sa.ForeignKey('drivers.id', ondelete='SET NULL'), nullable=True),
        sa.Column('vehicle_number', sa.String(length=50), nullable=False),
        sa.Column('vehicle_type', sa.String(length=50), nullable=False, server_default='VAN'),
        sa.Column('capacity', sa.Float(), nullable=False, server_default='1000.0'),
        sa.Column('fuel_type', sa.String(length=30), nullable=False, server_default='DIESEL'),
        sa.Column('mileage', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='AVAILABLE'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_vehicles_vehicle_number'), 'vehicles', ['vehicle_number'], unique=True)

    # 3. Warehouses table
    op.create_table(
        'warehouses',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('address', sa.String(length=255), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('capacity', sa.Float(), nullable=False, server_default='10000.0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_warehouses_name'), 'warehouses', ['name'], unique=False)

    # 4. Customers table
    op.create_table(
        'customers',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('phone', sa.String(length=30), nullable=False),
        sa.Column('email', sa.String(length=150), nullable=False),
        sa.Column('address', sa.String(length=255), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_customers_email'), 'customers', ['email'], unique=False)
    op.create_index(op.f('ix_customers_name'), 'customers', ['name'], unique=False)

    # 5. Orders table
    op.create_table(
        'orders',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('order_number', sa.String(length=100), nullable=False),
        sa.Column('customer_id', sa.String(length=36), sa.ForeignKey('customers.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('warehouse_id', sa.String(length=36), sa.ForeignKey('warehouses.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('pickup_latitude', sa.Float(), nullable=False),
        sa.Column('pickup_longitude', sa.Float(), nullable=False),
        sa.Column('delivery_latitude', sa.Float(), nullable=False),
        sa.Column('delivery_longitude', sa.Float(), nullable=False),
        sa.Column('package_weight', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('priority', sa.String(length=20), nullable=False, server_default='NORMAL'),
        sa.Column('delivery_window_start', sa.DateTime(), nullable=True),
        sa.Column('delivery_window_end', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='PENDING'),
        sa.Column('assigned_driver_id', sa.String(length=36), sa.ForeignKey('drivers.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_orders_order_number'), 'orders', ['order_number'], unique=True)
    op.create_index(op.f('ix_orders_status'), 'orders', ['status'], unique=False)


def downgrade() -> None:
    op.drop_table('orders')
    op.drop_table('customers')
    op.drop_table('warehouses')
    op.drop_table('vehicles')
    op.drop_table('drivers')
