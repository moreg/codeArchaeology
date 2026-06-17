# -*- coding: utf-8 -*-
"""GitBlame 模型"""
from sqlalchemy import Column, String, Integer, ForeignKey, Text

from .database import Base


class GitBlame(Base):
    __tablename__ = "git_blames"
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    function_id = Column(String, nullable=True, index=True)
    file_path = Column(String, nullable=False)
    line_no = Column(Integer, default=0)
    author = Column(String, default="")
    commit_hash = Column(String, default="")
    line_content = Column(Text, default="")

    def to_dict(self):
        return {
            "file_path": self.file_path,
            "line_no": self.line_no,
            "author": self.author,
            "commit_hash": self.commit_hash,
            "line_content": self.line_content,
        }