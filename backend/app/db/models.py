from datetime import datetime, timezone
import enum
from typing import Optional
import uuid

from sqlalchemy import Boolean, DateTime, Enum as SQLEnum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class VoteResult(str, enum.Enum):
    """Enumeration of possible battle voting outcomes."""
    MODEL_A = "model_a"
    MODEL_B = "model_b"
    TIE = "tie"
    BOTH_BAD = "both_bad"


def utc_now() -> datetime:
    """Helper to return current timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


class Model(Base):
    """Database model for registered LLM models across providers."""
    __tablename__ = "models"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    model_id: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    # Relationships
    elo_rating: Mapped[Optional["EloRating"]] = relationship(
        "EloRating", back_populates="model", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Model(id='{self.id}', provider='{self.provider}', model_id='{self.model_id}')>"


class Battle(Base):
    """Database model for side-by-side LLM battle sessions."""
    __tablename__ = "battles"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    model_a_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("models.id", ondelete="RESTRICT"), nullable=False
    )
    model_b_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("models.id", ondelete="RESTRICT"), nullable=False
    )
    response_a: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    response_b: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    has_streamed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False, index=True
    )

    # Relationships
    model_a: Mapped["Model"] = relationship("Model", foreign_keys=[model_a_id])
    model_b: Mapped["Model"] = relationship("Model", foreign_keys=[model_b_id])
    vote: Mapped[Optional["Vote"]] = relationship(
        "Vote", back_populates="battle", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Battle(id='{self.id}', model_a='{self.model_a_id}', model_b='{self.model_b_id}')>"


class Vote(Base):
    """Database model for user votes cast on battle outcomes."""
    __tablename__ = "votes"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    battle_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("battles.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    result: Mapped[VoteResult] = mapped_column(
        SQLEnum(VoteResult, name="vote_result_enum", values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    voted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    # Relationships
    battle: Mapped["Battle"] = relationship("Battle", back_populates="vote")

    def __repr__(self) -> str:
        return f"<Vote(id='{self.id}', battle_id='{self.battle_id}', result='{self.result}')>"


class EloRating(Base):
    """Database model tracking current Elo scores and match statistics for each model."""
    __tablename__ = "elo_ratings"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    model_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("models.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    rating: Mapped[float] = mapped_column(Float, default=1000.0, nullable=False, index=True)
    games_played: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    wins: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    losses: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    ties: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    # Relationships
    model: Mapped["Model"] = relationship("Model", back_populates="elo_rating")

    def __repr__(self) -> str:
        return f"<EloRating(model_id='{self.model_id}', rating={self.rating}, games={self.games_played})>"
