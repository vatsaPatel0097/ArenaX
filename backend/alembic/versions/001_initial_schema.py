"""Initial database schema for models, battles, votes, and elo_ratings

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-09-19 10:25:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create models table
    op.create_table(
        'models',
        sa.Column('id', sa.String(length=255), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('model_id', sa.String(length=255), nullable=False),
        sa.Column('display_name', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_models_provider'), 'models', ['provider'], unique=False)

    # 2. Create battles table
    op.create_table(
        'battles',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('prompt', sa.Text(), nullable=False),
        sa.Column('model_a_id', sa.String(length=255), nullable=False),
        sa.Column('model_b_id', sa.String(length=255), nullable=False),
        sa.Column('response_a', sa.Text(), nullable=True),
        sa.Column('response_b', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['model_a_id'], ['models.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['model_b_id'], ['models.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_battles_created_at'), 'battles', ['created_at'], unique=False)

    # 3. Create votes table
    op.create_table(
        'votes',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('battle_id', sa.String(length=36), nullable=False),
        sa.Column(
            'result',
            sa.Enum('model_a', 'model_b', 'tie', 'both_bad', name='vote_result_enum'),
            nullable=False
        ),
        sa.Column('voted_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['battle_id'], ['battles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('battle_id')
    )
    op.create_index(op.f('ix_votes_battle_id'), 'votes', ['battle_id'], unique=True)

    # 4. Create elo_ratings table
    op.create_table(
        'elo_ratings',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('model_id', sa.String(length=255), nullable=False),
        sa.Column('rating', sa.Float(), nullable=False, server_default=sa.text('1000.0')),
        sa.Column('games_played', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('wins', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('losses', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('ties', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['model_id'], ['models.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('model_id')
    )
    op.create_index(op.f('ix_elo_ratings_rating'), 'elo_ratings', ['rating'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_elo_ratings_rating'), table_name='elo_ratings')
    op.drop_table('elo_ratings')
    op.drop_index(op.f('ix_votes_battle_id'), table_name='votes')
    op.drop_table('votes')
    # Drop enum type in postgres if needed
    op.execute("DROP TYPE IF EXISTS vote_result_enum")
    op.drop_index(op.f('ix_battles_created_at'), table_name='battles')
    op.drop_table('battles')
    op.drop_index(op.f('ix_models_provider'), table_name='models')
    op.drop_table('models')
