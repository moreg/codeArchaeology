# -*- coding: utf-8 -*-
"""AnalysisResult 模型"""
from sqlalchemy import Column, String, Integer, ForeignKey, Text, JSON

from .database import Base


class AnalysisResult(Base):
    __tablename__ = "analysis_results"
    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    node_id = Column(String, nullable=False, index=True)
    kind = Column(String, nullable=False)  # story | refactor
    result = Column(JSON, default={})

    def to_dict(self):
        return {
            "id": self.id,
            "node_id": self.node_id,
            "kind": self.kind,
            "result": self.result or {},
        }