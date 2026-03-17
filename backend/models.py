# ============================================================
# BLOCO 5.4 — Modelos SQLAlchemy (mapeiam as tabelas do Supabase)
# Arquivo: backend/models.py
# ============================================================

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Numeric, Boolean, Text,
    DateTime, ForeignKey, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .database import Base


class GlucoseEvent(Base):
    __tablename__ = "glucose_events"
    __table_args__ = (
        UniqueConstraint("user_id", "measured_at", name="glucose_events_user_time_unique"),
    )

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id        = Column(UUID(as_uuid=True), nullable=False)
    source         = Column(String, nullable=False, default="manual")
    device_id      = Column(Text, nullable=True)
    value_mg_dl    = Column(Numeric(5, 1), nullable=False)
    trend          = Column(String, nullable=False, default="unknown")
    context        = Column(String, nullable=False, default="random")
    hypo_flag      = Column(Boolean, nullable=True)   # computed no Postgres
    hyper_flag     = Column(Boolean, nullable=True)   # computed no Postgres
    notes          = Column(Text, nullable=True)
    measured_at    = Column(DateTime(timezone=True), nullable=False)
    recorded_at    = Column(DateTime(timezone=True), default=datetime.utcnow)
    created_by     = Column(String, nullable=False, default="user")
    correlation_id = Column(UUID(as_uuid=True), nullable=True)


class Meal(Base):
    __tablename__ = "meals"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id         = Column(UUID(as_uuid=True), nullable=False)
    name            = Column(Text, nullable=True)
    meal_type       = Column(String, nullable=False, default="other")
    total_carbs_g   = Column(Numeric(6, 1), nullable=True)
    total_protein_g = Column(Numeric(6, 1), nullable=True)
    total_fat_g     = Column(Numeric(6, 1), nullable=True)
    estimated       = Column(Boolean, nullable=False, default=True)
    notes           = Column(Text, nullable=True)
    eaten_at        = Column(DateTime(timezone=True), nullable=False)
    recorded_at     = Column(DateTime(timezone=True), default=datetime.utcnow)

    items = relationship(
        "MealItem",
        back_populates="meal",
        cascade="all, delete-orphan",
        lazy="selectin",  # carrega itens automaticamente em async
    )


class MealItem(Base):
    __tablename__ = "meal_items"

    id        = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    meal_id   = Column(UUID(as_uuid=True), ForeignKey("meals.id"), nullable=False)
    name      = Column(Text, nullable=False)
    carbs_g   = Column(Numeric(6, 1), nullable=True)
    protein_g = Column(Numeric(6, 1), nullable=True)
    fat_g     = Column(Numeric(6, 1), nullable=True)
    portion   = Column(Text, nullable=True)

    meal = relationship("Meal", back_populates="items")


class MealGlucoseLink(Base):
    __tablename__ = "meal_glucose_links"

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    meal_id          = Column(UUID(as_uuid=True), ForeignKey("meals.id"), nullable=False)
    glucose_event_id = Column(UUID(as_uuid=True), ForeignKey("glucose_events.id"), nullable=False)
    relation         = Column(String, nullable=False)
