# -*- coding: utf-8 -*-
"""File 模型"""
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship

from .database import Base


class File(Base):
    __tablename__ = "files"
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    path = Column(String, nullable=False)
    relative_path = Column(String, default="")
    language = Column(String, default="")
    size = Column(Integer, default=0)
    line_count = Column(Integer, default=0)

    project = relationship("Project", back_populates="files")
    functions = relationship("Function", back_populates="file", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "path": self.path,
            "relative_path": self.relative_path,
            "language": self.language,
            "size": self.size,
            "line_count": self.line_count,
        }