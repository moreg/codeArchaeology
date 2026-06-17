# -*- coding: utf-8 -*-
"""CallRelation 模型"""
from sqlalchemy import Column, String, Integer, ForeignKey

from .database import Base


class CallRelation(Base):
    __tablename__ = "call_relations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    source = Column(String, nullable=False)
    target = Column(String, nullable=False)
    call_type = Column(String, default="direct")
    call_count = Column(Integer, default=1)

    def to_dict(self):
        return {
            "source": self.source,
            "target": self.target,
            "call_type": self.call_type,
            "call_count": self.call_count,
        }