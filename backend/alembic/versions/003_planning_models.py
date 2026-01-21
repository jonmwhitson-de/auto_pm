"""Add planning models: dependencies, decisions, assumptions, story estimates

Revision ID: 003
Revises: 002
Create Date: 2024-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = '003'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create dependencies table
    op.create_table(
        'dependencies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('source_type', sa.String(20), nullable=False),
        sa.Column('source_id', sa.Integer(), nullable=False),
        sa.Column('target_type', sa.String(20), nullable=False),
        sa.Column('target_id', sa.Integer(), nullable=False),
        sa.Column('dependency_type', sa.String(20), nullable=True),
        sa.Column('status', sa.String(20), nullable=True),
        sa.Column('inferred', sa.Boolean(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('inference_reason', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dependencies_id'), 'dependencies', ['id'], unique=False)

    # Create decisions table
    op.create_table(
        'decisions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('context', sa.Text(), nullable=True),
        sa.Column('decision', sa.Text(), nullable=False),
        sa.Column('rationale', sa.Text(), nullable=True),
        sa.Column('alternatives', sa.Text(), nullable=True),
        sa.Column('consequences', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), nullable=True),
        sa.Column('decision_maker', sa.String(length=255), nullable=True),
        sa.Column('decision_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('extracted_from', sa.String(length=50), nullable=True),
        sa.Column('extraction_confidence', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_decisions_id'), 'decisions', ['id'], unique=False)

    # Create assumptions table
    op.create_table(
        'assumptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('assumption', sa.Text(), nullable=False),
        sa.Column('context', sa.Text(), nullable=True),
        sa.Column('impact_if_wrong', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), nullable=True),
        sa.Column('risk_level', sa.String(20), nullable=True),
        sa.Column('validation_method', sa.Text(), nullable=True),
        sa.Column('validation_owner', sa.String(length=255), nullable=True),
        sa.Column('validation_deadline', sa.DateTime(timezone=True), nullable=True),
        sa.Column('validation_result', sa.Text(), nullable=True),
        sa.Column('validated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('extracted_from', sa.String(length=50), nullable=True),
        sa.Column('extraction_confidence', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_assumptions_id'), 'assumptions', ['id'], unique=False)

    # Create story_estimates table
    op.create_table(
        'story_estimates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('story_id', sa.Integer(), nullable=False),
        sa.Column('estimate_p10', sa.Float(), nullable=True),
        sa.Column('estimate_p50', sa.Float(), nullable=True),
        sa.Column('estimate_p90', sa.Float(), nullable=True),
        sa.Column('rice_reach', sa.Integer(), nullable=True),
        sa.Column('rice_impact', sa.Float(), nullable=True),
        sa.Column('rice_confidence', sa.Float(), nullable=True),
        sa.Column('rice_effort', sa.Float(), nullable=True),
        sa.Column('rice_score', sa.Float(), nullable=True),
        sa.Column('wsjf_business_value', sa.Integer(), nullable=True),
        sa.Column('wsjf_time_criticality', sa.Integer(), nullable=True),
        sa.Column('wsjf_risk_reduction', sa.Integer(), nullable=True),
        sa.Column('wsjf_job_size', sa.Integer(), nullable=True),
        sa.Column('wsjf_score', sa.Float(), nullable=True),
        sa.Column('cod_weekly', sa.Float(), nullable=True),
        sa.Column('cod_urgency_profile', sa.String(length=50), nullable=True),
        sa.Column('okr_alignment_score', sa.Float(), nullable=True),
        sa.Column('aligned_okrs', sa.Text(), nullable=True),
        sa.Column('ai_estimate_p10', sa.Float(), nullable=True),
        sa.Column('ai_estimate_p50', sa.Float(), nullable=True),
        sa.Column('ai_estimate_p90', sa.Float(), nullable=True),
        sa.Column('ai_confidence', sa.Float(), nullable=True),
        sa.Column('ai_reasoning', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['story_id'], ['stories.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('story_id')
    )
    op.create_index(op.f('ix_story_estimates_id'), 'story_estimates', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_story_estimates_id'), table_name='story_estimates')
    op.drop_table('story_estimates')
    op.drop_index(op.f('ix_assumptions_id'), table_name='assumptions')
    op.drop_table('assumptions')
    op.drop_index(op.f('ix_decisions_id'), table_name='decisions')
    op.drop_table('decisions')
    op.drop_index(op.f('ix_dependencies_id'), table_name='dependencies')
    op.drop_table('dependencies')
