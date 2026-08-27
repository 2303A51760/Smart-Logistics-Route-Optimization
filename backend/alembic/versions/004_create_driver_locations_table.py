"""create driver locations table

Revision ID: 004_create_driver_locations_table
Revises: 003_create_route_execution_tables
Create Date: 2026-08-25 15:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '004_create_driver_locations_table'
down_revision: Union[str, None] = '003_create_route_execution_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'driver_locations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('driver_id', sa.String(length=36), sa.ForeignKey('drivers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('accuracy', sa.Float(), nullable=True),
        sa.Column('speed', sa.Float(), nullable=True),
        sa.Column('heading', sa.Float(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_driver_locations_driver_id'), 'driver_locations', ['driver_id'], unique=False)
    op.create_index(op.f('ix_driver_locations_timestamp'), 'driver_locations', ['timestamp'], unique=False)
    op.create_index('ix_driver_locations_driver_timestamp', 'driver_locations', ['driver_id', 'timestamp'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_driver_locations_driver_timestamp', table_name='driver_locations')
    op.drop_index(op.f('ix_driver_locations_timestamp'), table_name='driver_locations')
    op.drop_index(op.f('ix_driver_locations_driver_id'), table_name='driver_locations')
    op.drop_table('driver_locations')
