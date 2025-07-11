from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class FileBase(BaseModel):
    filename: str
    file_size: int
    mime_type: Optional[str] = None


class FileCreate(FileBase):
    session_id: str
    file_path: str


class FileResponse(FileBase):
    id: str
    session_id: str
    google_drive_file_id: Optional[str] = None
    uploaded_at: datetime

    class Config:
        from_attributes = True
