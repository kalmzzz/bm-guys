from __future__ import annotations
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from typing import Optional

from .db import Base


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    brand_name: Mapped[Optional[str]] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Action toggles
    enable_post: Mapped[bool] = mapped_column(Boolean, default=True)
    enable_reply: Mapped[bool] = mapped_column(Boolean, default=True)
    enable_like: Mapped[bool] = mapped_column(Boolean, default=False)
    enable_retweet: Mapped[bool] = mapped_column(Boolean, default=False)

    # Schedules in seconds
    post_interval_s: Mapped[int] = mapped_column(Integer, default=4 * 3600)
    reply_interval_s: Mapped[int] = mapped_column(Integer, default=120)
    like_interval_s: Mapped[int] = mapped_column(Integer, default=600)
    retweet_interval_s: Mapped[int] = mapped_column(Integer, default=10 * 3600)

    # CTA cadence
    cta_every_n_posts: Mapped[Optional[int]] = mapped_column(Integer, default=None)
    cta_every_n_replies: Mapped[Optional[int]] = mapped_column(Integer, default=None)

    # X credentials (per agent user context)
    x_consumer_key: Mapped[str] = mapped_column(String(255))
    x_consumer_secret: Mapped[str] = mapped_column(String(255))
    x_access_token: Mapped[str] = mapped_column(String(255))
    x_access_token_secret: Mapped[str] = mapped_column(String(255))
    x_bearer_token: Mapped[Optional[str]] = mapped_column(String(512))

    # Derived style
    style_profile: Mapped[Optional[Text]] = mapped_column(Text, default=None)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Last action timestamps for throttling
    last_post_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=None)
    last_reply_scan_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=None)
    last_like_scan_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=None)
    last_retweet_scan_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=None)

    # Relationships
    ctas: Mapped[list[CTA]] = relationship("CTA", back_populates="agent", cascade="all, delete-orphan")
    targets: Mapped[list[TargetUser]] = relationship("TargetUser", back_populates="agent", cascade="all, delete-orphan")
    keywords: Mapped[list[KeywordTrigger]] = relationship("KeywordTrigger", back_populates="agent", cascade="all, delete-orphan")
    sources: Mapped[list[SourceAccount]] = relationship("SourceAccount", back_populates="agent", cascade="all, delete-orphan")


class CTA(Base):
    __tablename__ = "ctas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    agent_id: Mapped[int] = mapped_column(ForeignKey("agents.id", ondelete="CASCADE"))
    url: Mapped[str] = mapped_column(String(2048))
    label: Mapped[Optional[str]] = mapped_column(String(255))
    for_replies: Mapped[bool] = mapped_column(Boolean, default=False)
    for_posts: Mapped[bool] = mapped_column(Boolean, default=True)

    agent: Mapped[Agent] = relationship("Agent", back_populates="ctas")


class TargetUser(Base):
    __tablename__ = "target_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    agent_id: Mapped[int] = mapped_column(ForeignKey("agents.id", ondelete="CASCADE"))
    handle: Mapped[str] = mapped_column(String(255))
    user_id: Mapped[Optional[str]] = mapped_column(String(64))
    last_seen_tweet_id: Mapped[Optional[str]] = mapped_column(String(64))

    agent: Mapped[Agent] = relationship("Agent", back_populates="targets")


class SourceAccount(Base):
    __tablename__ = "source_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    agent_id: Mapped[int] = mapped_column(ForeignKey("agents.id", ondelete="CASCADE"))
    handle: Mapped[str] = mapped_column(String(255))
    user_id: Mapped[Optional[str]] = mapped_column(String(64))
    last_rewritten_tweet_id: Mapped[Optional[str]] = mapped_column(String(64))

    agent: Mapped[Agent] = relationship("Agent", back_populates="sources")


class KeywordTrigger(Base):
    __tablename__ = "keyword_triggers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    agent_id: Mapped[int] = mapped_column(ForeignKey("agents.id", ondelete="CASCADE"))
    keyword: Mapped[str] = mapped_column(String(255))

    agent: Mapped[Agent] = relationship("Agent", back_populates="keywords")


class PostLog(Base):
    __tablename__ = "post_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    agent_id: Mapped[int] = mapped_column(ForeignKey("agents.id", ondelete="CASCADE"))
    action: Mapped[str] = mapped_column(String(32))  # tweet|reply|like|retweet
    reference_tweet_id: Mapped[Optional[str]] = mapped_column(String(64))
    posted_tweet_id: Mapped[Optional[str]] = mapped_column(String(64))
    included_cta: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)