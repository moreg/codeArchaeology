# -*- coding: utf-8 -*-
"""Score 模型"""
from sqlalchemy import Column, String, Integer, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship

from .database import Base


class Score(Base):
    __tablename__ = "scores"
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    total_score = Column(Float, default=0.0)
    rating = Column(String, default="")
    rating_color = Column(String, default="")
    dimensions = Column(JSON, default={})
    hot_spots = Column(JSON, default=[])

    project = relationship("Project", back_populates="scores")

    def to_dict(self):
        return {
            "total_score": self.total_score,
            "rating": self.rating,
            "rating_color": self.rating_color,
            "dimensions": self.dimensions or {},
            "hot_spots": self.hot_spots or [],
        }