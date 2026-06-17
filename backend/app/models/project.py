# -*- coding: utf-8 -*-
"""Project 模型"""
from sqlalchemy import Column, String, DateTime, Integer
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from .database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Project(Base):
    __tablename__ = "projects"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    path = Column(String, nullable=False)
    languages = Column(String, default="python")
    status = Column(String, default="pending")  # pending | scanning | done | error
    progress = Column(Integer, default=0)
    total = Column(Integer, default=0)
    current_file = Column(String, default="")
    started_at = Column(DateTime, default=_utcnow)
    finished_at = Column(DateTime, nullable=True)
    error = Column(String, default="")

    files = relationship("File", back_populates="project", cascade="all, delete-orphan")
    functions = relationship("Function", back_populates="project", cascade="all, delete-orphan")
    scores = relationship("Score", back_populates="project", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "scan_id": self.id,
            "project_name": self.name,
            "path": self.path,
            "languages": (self.languages or "").split(",") if self.languages else [],
            "status": self.status,
            "progress": self.progress,
            "total": self.total,
            "current_file": self.current_file,
            "started_at": self.started_at.isoformat() if self.started_at else "",
            "finished_at": self.finished_at.isoformat() if self.finished_at else "",
            "error": self.error,
        }