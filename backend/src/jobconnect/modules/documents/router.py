from __future__ import annotations

from typing import Literal, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, Query, UploadFile

from jobconnect.modules.api.shared import CurrentUser, Paginated, ParseStatus, require_active
from jobconnect.modules.documents import service
from jobconnect.modules.documents.schemas import (
    DocumentDetail,
    DocumentDownloadUrlResponse,
    DocumentUploadResponse,
    ParseJobDetail,
)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post(
    "",
    response_model=DocumentUploadResponse,
    status_code=201,
    description=(
        "Upload a CV or JD via multipart/form-data. Required form field: `file`. "
        "Required form field: `document_type` (candidate_resume|job_post). "
        "Optional form fields: `resume_id`, `job_id`. "
        "Accepted MIME types: application/pdf, application/msword, "
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document. "
        "Max file size: 10 MiB."
    ),
)
def create_document(
    document_type: Literal["candidate_resume", "job_post"] = Form(...),
    file: UploadFile = File(...),
    resume_id: Optional[int] = Form(default=None),
    job_id: Optional[int] = Form(default=None),
    user: CurrentUser = Depends(require_active),
    background_tasks: BackgroundTasks = None,
) -> DocumentUploadResponse:
    return service.create_document(document_type, file, resume_id, job_id, user, background_tasks)


@router.get("", response_model=Paginated)
def list_documents(
    document_type: Optional[Literal["candidate_resume", "job_post"]] = None,
    parse_status: Optional[ParseStatus] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: CurrentUser = Depends(require_active),
):
    return service.list_documents(document_type, parse_status, limit, offset, user)


@router.get("/{document_id}", response_model=DocumentDetail)
def get_document(document_id: int, user: CurrentUser = Depends(require_active)):
    return service.get_document(document_id, user)


@router.get("/{document_id}/download-url", response_model=DocumentDownloadUrlResponse)
def get_download_url(document_id: int, user: CurrentUser = Depends(require_active)) -> DocumentDownloadUrlResponse:
    return service.get_download_url(document_id, user)


@router.get("/{document_id}/parse-jobs/{parse_job_id}")
def get_parse_job(document_id: int, parse_job_id: int, user: CurrentUser = Depends(require_active)):
    return service.get_parse_job(document_id, parse_job_id, user)


@router.post("/{document_id}/parse-jobs", response_model=ParseJobDetail, status_code=201)
def create_parse_job(
    document_id: int,
    user: CurrentUser = Depends(require_active),
    background_tasks: BackgroundTasks = None,
):
    return service.create_parse_job(document_id, user, background_tasks)
