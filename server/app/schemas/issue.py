from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class IssueBase(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None


class IssueCreate(IssueBase):
    pass


class IssueResponse(IssueBase):
    id: int
    image_url: str
    status: str
    caption: Optional[str] = None
    tags: Optional[List[str]] = None
    created_at: datetime

    class Config:
        from_attributes = True
