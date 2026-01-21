"""Initial migration

Revision ID: 001
Revises:
Create Date: 2024-01-01

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Projects table
    op.create_table(
        'projects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('prd_content', sa.Text(), nullable=False),
        sa.Column('status', sa.Enum('draft', 'analyzing', 'ready', 'in_progress', 'completed', name='projectstatus'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_projects_id'), 'projects', ['id'], unique=False)

    # Team members table
    op.create_table(
        'team_members',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('role', sa.String(length=100), nullable=True),
        sa.Column('hours_per_sprint', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_team_members_id'), 'team_members', ['id'], unique=False)

    # Sprints table
    op.create_table(
        'sprints',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('goal', sa.String(length=500), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('capacity_hours', sa.Integer(), nullable=True),
        sa.Column('status', sa.Enum('planning', 'active', 'completed', name='sprintstatus'), nullable=True),
        sa.Column('order', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sprints_id'), 'sprints', ['id'], unique=False)

    # Epics table
    op.create_table(
        'epics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('priority', sa.Enum('low', 'medium', 'high', 'critical', name='priority'), nullable=True),
        sa.Column('order', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_epics_id'), 'epics', ['id'], unique=False)

    # Stories table
    op.create_table(
        'stories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('epic_id', sa.Integer(), nullable=False),
        sa.Column('sprint_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('acceptance_criteria', sa.Text(), nullable=True),
        sa.Column('story_points', sa.Integer(), nullable=True),
        sa.Column('estimated_hours', sa.Integer(), nullable=True),
        sa.Column('priority', sa.Enum('low', 'medium', 'high', 'critical', name='priority'), nullable=True),
        sa.Column('status', sa.Enum('backlog', 'ready', 'in_progress', 'in_review', 'done', name='storystatus'), nullable=True),
        sa.Column('order', sa.Integer(), nullable=True),
        sa.Column('assigned_to_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['epic_id'], ['epics.id'], ),
        sa.ForeignKeyConstraint(['sprint_id'], ['sprints.id'], ),
        sa.ForeignKeyConstraint(['assigned_to_id'], ['team_members.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_stories_id'), 'stories', ['id'], unique=False)

    # Tasks table
    op.create_table(
        'tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('story_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('estimated_hours', sa.Integer(), nullable=True),
        sa.Column('status', sa.Enum('todo', 'in_progress', 'done', name='taskstatus'), nullable=True),
        sa.Column('order', sa.Integer(), nullable=True),
        sa.Column('assigned_to_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['story_id'], ['stories.id'], ),
        sa.ForeignKeyConstraint(['assigned_to_id'], ['team_members.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tasks_id'), 'tasks', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_tasks_id'), table_name='tasks')
    op.drop_table('tasks')
    op.drop_index(op.f('ix_stories_id'), table_name='stories')
    op.drop_table('stories')
    op.drop_index(op.f('ix_epics_id'), table_name='epics')
    op.drop_table('epics')
    op.drop_index(op.f('ix_sprints_id'), table_name='sprints')
    op.drop_table('sprints')
    op.drop_index(op.f('ix_team_members_id'), table_name='team_members')
    op.drop_table('team_members')
    op.drop_index(op.f('ix_projects_id'), table_name='projects')
    op.drop_table('projects')

    op.execute("DROP TYPE IF EXISTS projectstatus")
    op.execute("DROP TYPE IF EXISTS sprintstatus")
    op.execute("DROP TYPE IF EXISTS priority")
    op.execute("DROP TYPE IF EXISTS storystatus")
    op.execute("DROP TYPE IF EXISTS taskstatus")
