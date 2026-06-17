# -*- coding: utf-8 -*-
"""Function 模型"""
from sqlalchemy import Column, String, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship

from .database import Base


class Function(Base):
    __tablename__ = "functions"
    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=True)
    name = Column(String, nullable=False, default="anonymous")
    file_path = Column(String, default="")
    start_line = Column(Integer, default=0)
    end_line = Column(Integer, default=0)
    line_count = Column(Integer, default=0)
    language = Column(String, default="python")
    class_name = Column(String, default="")
    complexity = Column(Integer, default=1)
    author = Column(String, default="")
    last_modified = Column(String, default="")
    last_commit_hash = Column(String, default="")
    test_coverage = Column(Integer, default=0)  # 0-100

    project = relationship("Project", back_populates="functions")
    file = relationship("File", back_populates="functions")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "level": "function",
            "file_path": self.file_path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "line_count": self.line_count,
            "language": self.language,
            "class_name": self.class_name,
            "complexity": self.complexity,
            "author": self.author,
            "last_modified": self.last_modified,
            "last_commit_hash": self.last_commit_hash,
            "test_coverage": self.test_coverage,
        }