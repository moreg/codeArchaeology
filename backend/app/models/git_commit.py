# -*- coding: utf-8 -*-
"""GitCommit 模型"""
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Text

from .database import Base


class GitCommit(Base):
    __tablename__ = "git_commits"
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    hash = Column(String, nullable=False, index=True)
    author = Column(String, default="")
    email = Column(String, default="")
    message = Column(Text, default="")
    committed_at = Column(String, default="")
    files_changed = Column(Integer, default=0)

    def to_dict(self):
        return {
            "commit_hash": self.hash[:7] if self.hash else "",
            "hash": self.hash,
            "author": self.author,
            "email": self.email,
            "message": self.message,
            "committed_at": self.committed_at,
            "files_changed": self.files_changed,
        }