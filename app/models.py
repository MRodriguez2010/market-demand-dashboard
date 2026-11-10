from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class Region(Base):
    __tablename__ = "regions"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    state = Column(String(50), nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    population = Column(Integer, default=0)
    median_income = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    demands = relationship("DemandSignal", back_populates="region")
    events = relationship("LocalEvent", back_populates="region")


class ServiceCategory(Base):
    __tablename__ = "service_categories"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    icon = Column(String(50), default="📊")
    description = Column(Text, default="")
    demands = relationship("DemandSignal", back_populates="category")


class DemandSignal(Base):
    __tablename__ = "demand_signals"
    id = Column(Integer, primary_key=True)
    region_id = Column(Integer, ForeignKey("regions.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("service_categories.id"), nullable=False)
    month = Column(String(7), nullable=False)  # YYYY-MM
    search_volume = Column(Integer, default=0)
    job_postings = Column(Integer, default=0)
    social_mentions = Column(Integer, default=0)
    demand_score = Column(Float, default=0)  # 0-100 composite
    growth_rate = Column(Float, default=0)  # % change MoM
    avg_budget = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    region = relationship("Region", back_populates="demands")
    category = relationship("ServiceCategory", back_populates="demands")


class LocalEvent(Base):
    __tablename__ = "local_events"
    id = Column(Integer, primary_key=True)
    region_id = Column(Integer, ForeignKey("regions.id"), nullable=False)
    title = Column(String(200), nullable=False)
    event_type = Column(String(50), nullable=False)  # conference, meetup, hiring_surge, funding
    date = Column(DateTime, nullable=False)
    impact_score = Column(Float, default=0)
    description = Column(Text, default="")
    region = relationship("Region", back_populates="events")


class MarketInsight(Base):
    __tablename__ = "market_insights"
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    insight_type = Column(String(50), nullable=False)  # opportunity, trend, warning
    description = Column(Text, nullable=False)
    relevance_score = Column(Float, default=0)
    region_name = Column(String(100), default="")
    category_name = Column(String(100), default="")
    created_at = Column(DateTime, default=datetime.utcnow)
