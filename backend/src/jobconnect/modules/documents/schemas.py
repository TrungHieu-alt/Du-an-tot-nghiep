from __future__ import annotations

from typing import Literal, Optional

from pydantic import Field

from jobconnect.modules.api.shared import APIModel, ParseStatus


class ParseJobDetail(APIModel):
    parse_job_id: int
    document_id: int
    target_entity_type: Literal["candidate_resume", "job_post"]
    resume_id: Optional[int] = None
    job_id: Optional[int] = None
    status: ParseStatus
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    created_at: str
    updated_at: str


class DocumentDetail(APIModel):
    document_id: int
    owner_user_id: int
    document_type: Literal["candidate_resume", "job_post"]
    object_key: Optional[str] = None
    file_url: Optional[str] = None
    original_filename: str
    mime_type: str
    file_size_bytes: int = Field(ge=0)
    resume_id: Optional[int] = None
    job_id: Optional[int] = None
    created_at: str
    parse_jobs: list[ParseJobDetail] = Field(default_factory=list)


class DocumentUploadResponse(APIModel):
    document: DocumentDetail
    parse_job: ParseJobDetail


class DocumentDownloadUrlResponse(APIModel):
    download_url: str
    expires_at: str
