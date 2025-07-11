from sqlalchemy import Column, String, DateTime, Enum, Text
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class SubmissionType(str, enum.Enum):
    INDIVIDUAL = "individual"
    CORPORATE = "corporate"


class SubmissionStatus(str, enum.Enum):
    NOT_UPLOADED = "not_uploaded"
    NEEDS_REUPLOAD = "needs_reupload"
    APPROVED = "approved"


class SubmissionSession(Base):
    __tablename__ = "submission_sessions"

    id = Column(String, primary_key=True, index=True)
    submitter_name = Column(String, nullable=False)
    submitter_email = Column(String, nullable=False)
    submission_type = Column(Enum(SubmissionType), nullable=False)
    status = Column(Enum(SubmissionStatus), default=SubmissionStatus.NOT_UPLOADED)
    description = Column(Text, nullable=True)
    google_drive_folder_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
