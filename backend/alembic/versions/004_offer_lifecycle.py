"""Add Offer Lifecycle models: phases and service tasks

Revision ID: 004
Revises: 003
Create Date: 2024-01-15 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create offer_lifecycle_phases table
    op.create_table(
        'offer_lifecycle_phases',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('phase', sa.String(20), nullable=False),
        sa.Column('status', sa.String(20), nullable=True),
        sa.Column('order', sa.Integer(), nullable=False),
        sa.Column('approval_required', sa.Boolean(), nullable=True, default=True),
        sa.Column('approved_by', sa.String(length=255), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('approval_notes', sa.Text(), nullable=True),
        sa.Column('sequence_overridden', sa.Boolean(), nullable=True, default=False),
        sa.Column('override_reason', sa.Text(), nullable=True),
        sa.Column('overridden_by', sa.String(length=255), nullable=True),
        sa.Column('overridden_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('target_start_date', sa.Date(), nullable=True),
        sa.Column('target_end_date', sa.Date(), nullable=True),
        sa.Column('actual_start_date', sa.Date(), nullable=True),
        sa.Column('actual_end_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'phase', name='uq_project_phase')
    )
    op.create_index(op.f('ix_offer_lifecycle_phases_id'), 'offer_lifecycle_phases', ['id'], unique=False)

    # Create service_tasks table
    op.create_table(
        'service_tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('phase_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('definition', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('subcategory', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(20), nullable=True),
        sa.Column('source', sa.String(20), nullable=True),
        sa.Column('target_start_date', sa.Date(), nullable=True),
        sa.Column('target_complete_date', sa.Date(), nullable=True),
        sa.Column('days_required', sa.Integer(), nullable=True),
        sa.Column('actual_start_date', sa.Date(), nullable=True),
        sa.Column('actual_complete_date', sa.Date(), nullable=True),
        sa.Column('owner', sa.String(length=255), nullable=True),
        sa.Column('team', sa.String(length=100), nullable=True),
        sa.Column('linked_epic_id', sa.Integer(), nullable=True),
        sa.Column('linked_story_id', sa.Integer(), nullable=True),
        sa.Column('order', sa.Integer(), nullable=True, default=0),
        sa.Column('is_required', sa.Boolean(), nullable=True, default=True),
        sa.Column('ai_confidence', sa.Float(), nullable=True),
        sa.Column('ai_reasoning', sa.Text(), nullable=True),
        sa.Column('template_id', sa.String(length=50), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('completion_notes', sa.Text(), nullable=True),
        sa.Column('artifacts_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['phase_id'], ['offer_lifecycle_phases.id']),
        sa.ForeignKeyConstraint(['linked_epic_id'], ['epics.id']),
        sa.ForeignKeyConstraint(['linked_story_id'], ['stories.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_service_tasks_id'), 'service_tasks', ['id'], unique=False)
    op.create_index(op.f('ix_service_tasks_phase_id'), 'service_tasks', ['phase_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_service_tasks_phase_id'), table_name='service_tasks')
    op.drop_index(op.f('ix_service_tasks_id'), table_name='service_tasks')
    op.drop_table('service_tasks')
    op.drop_index(op.f('ix_offer_lifecycle_phases_id'), table_name='offer_lifecycle_phases')
    op.drop_table('offer_lifecycle_phases')
