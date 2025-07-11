from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class SubmissionTypeEnum(str, Enum):
    individual = "individual"
    corporate = "corporate"


class SubmissionStatusEnum(str, Enum):
    not_uploaded = "not_uploaded"
    needs_reupload = "needs_reupload"
    approved = "approved"


class SessionBase(BaseModel):
    submitter_name: str
    submitter_email: str
    submission_type: SubmissionTypeEnum
    description: Optional[str] = None


class SessionCreate(SessionBase):
    pass


class SessionUpdate(BaseModel):
    status: Optional[SubmissionStatusEnum] = None
    description: Optional[str] = None


class SessionResponse(SessionBase):
    id: str
    status: SubmissionStatusEnum
    google_drive_folder_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    uploaded_files: List[dict] = []

    class Config:
        from_attributes = True


class SessionListResponse(BaseModel):
    sessions: List[SessionResponse]
