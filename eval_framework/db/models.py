"""SQLAlchemy ORM models."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Float, ForeignKey, Integer, String, Text, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class EvalRun(Base):
    __tablename__ = "eval_runs"

    run_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    agent_name: Mapped[str] = mapped_column(String(128), index=True)
    agent_version: Mapped[str] = mapped_column(String(32))
    test_item_id: Mapped[str] = mapped_column(String(64), index=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    duration_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(
        String(32), default="completed"
    )  # completed | timeout | error
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # One-to-one with trace and one-to-many with results
    trace: Mapped[Optional["TraceRecord"]] = relationship(
        back_populates="run", uselist=False, cascade="all, delete-orphan"
    )
    results: Mapped[list["EvalResult"]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )


class TraceRecord(Base):
    __tablename__ = "trace_records"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    run_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("eval_runs.run_id"), unique=True
    )
    steps_json: Mapped[str] = mapped_column(Text)  # JSON array
    final_output: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    run: Mapped["EvalRun"] = relationship(back_populates="trace")


class EvalResult(Base):
    __tablename__ = "eval_results"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    run_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("eval_runs.run_id"), index=True
    )
    test_item_id: Mapped[str] = mapped_column(String(64))
    dimension: Mapped[str] = mapped_column(String(8))
    l1_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    judge_score: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    judge_reasoning: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    status: Mapped[str] = mapped_column(String(32), default="completed")

    run: Mapped["EvalRun"] = relationship(back_populates="results")


class AgentScoreSummary(Base):
    """Precomputed agent score per dimension for fast dashboard queries."""

    __tablename__ = "agent_score_summaries"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    agent_name: Mapped[str] = mapped_column(String(128), index=True)
    agent_version: Mapped[str] = mapped_column(String(32))
    dimension: Mapped[str] = mapped_column(String(8))
    avg_score: Mapped[float] = mapped_column(Float)
    run_count: Mapped[int] = mapped_column(Integer)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
