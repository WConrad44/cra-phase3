from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source: Mapped[str] = mapped_column(String(40), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    product_json: Mapped[str] = mapped_column(Text, nullable=False)
    reporter_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    member_states_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    vulnerability_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[str | None] = mapped_column(String(20), nullable=True)
    fix_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    state: Mapped[str] = mapped_column(String(20), nullable=False, default="received")
    resolution: Mapped[str | None] = mapped_column(String(40), nullable=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    aware_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    triage_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
