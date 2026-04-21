from typing import Optional, List, Dict
from fastapi import HTTPException, status
from repositories.cv_repo import CVRepository
from models.candidateResume import CandidateResume
import logging
import os
import tempfile

logger = logging.getLogger(__name__)

class CVService:

    # ============================
    # Basic CRUD Operations
    # ============================

    @staticmethod
    async def create_cv(user_id: int, title: str, location: Optional[str],
                        experience: Optional[str], skills: list, summary: Optional[str],
                        full_text: Optional[str], pdf_url: Optional[str], is_main: bool):
        """Create CV manually without parsing/embedding"""
        return await CVRepository.create(
            user_id, title, location, experience, skills,
            summary, full_text, pdf_url, is_main
        )

    @staticmethod
    async def get_cv(cv_id: int):
        """Get single CV by ID"""
        cv = await CVRepository.get_by_id(cv_id)
        if not cv:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CV not found")
        return cv

    @staticmethod
    async def get_user_cvs(user_id: int) -> List[CandidateResume]:
        """Get all CVs for a user"""
        return await CVRepository.get_by_user(user_id)

    @staticmethod
    async def get_main_cv(user_id: int):
        """Get main/primary CV for a user"""
        cvs = await CVRepository.get_by_user(user_id)
        main_cv = next((cv for cv in cvs if cv.is_main), None)
        if not main_cv:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Main CV not found")
        return main_cv

    @staticmethod
    async def update_cv(cv_id: int, **kwargs) -> CandidateResume:
        """Update CV by ID"""
        cv = await CVRepository.update(cv_id, **kwargs)
        if not cv:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CV not found")
        return cv

    @staticmethod
    async def delete_cv(cv_id: int) -> bool:
        """Delete CV by ID"""
        ok = await CVRepository.delete(cv_id)
        if not ok:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CV not found")
        return True

    # ============================
    # Upload & Parsing Operations
    # ============================

    @staticmethod
    async def upload_cv_from_pdf(user_id: int, pdf_path: str, 
                                 pdf_url: Optional[str] = None, 
                                 is_main: bool = False) -> CandidateResume:
        """
        Upload CV from PDF file.
        Automatically parses and generates embeddings.
        
        Args:
            user_id: User ID
            pdf_path: Path to PDF file
            pdf_url: Optional URL to stored PDF
            is_main: Whether this is the main CV
            
        Returns:
            CandidateResume object
        """
        try:
            return await CVRepository.upload_cv_from_pdf(user_id, pdf_path, pdf_url, is_main)
        except Exception as e:
            logger.error(f"Failed to upload CV from PDF: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                              detail=f"Failed to upload CV: {str(e)}")

    @staticmethod
    async def upload_cv_from_text(user_id: int, full_text: str,
                                  title: Optional[str] = None,
                                  pdf_url: Optional[str] = None,
                                  is_main: bool = False) -> CandidateResume:
        """
        Upload CV from plain text.
        Automatically parses and generates embeddings.
        
        Args:
            user_id: User ID
            full_text: Full text content of CV
            title: Optional CV title
            pdf_url: Optional URL to stored PDF
            is_main: Whether this is the main CV
            
        Returns:
            CandidateResume object
        """
        try:
            return await CVRepository.upload_cv_from_text(user_id, full_text, title, pdf_url, is_main)
        except Exception as e:
            logger.error(f"Failed to upload CV from text: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                              detail=f"Failed to upload CV: {str(e)}")

    @staticmethod
    async def upload_file(user_id: int, file, is_main: bool = False):
        """
        Upload CV from file (PDF or text).
        Wrapper for handling file uploads from API.
        """
        tmp_path = None
        try:
            # Determine file type and call appropriate method
            filename = file.filename.lower()
            
            if filename.endswith('.pdf'):
                # For PDF: save temporarily and process
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                    content = await file.read()
                    tmp.write(content)
                    tmp.flush()
                    tmp_path = tmp.name
                
                cv = await CVService.upload_cv_from_pdf(user_id, tmp_path, is_main=is_main)
                return cv
            else:
                # For text files
                content = await file.read()
                text = content.decode('utf-8')
                return await CVService.upload_cv_from_text(user_id, text, title=file.filename, is_main=is_main)
        except Exception as e:
            logger.error(f"Failed to upload file: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                              detail=f"Failed to upload file: {str(e)}")
        finally:
            # Clean up temporary file
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except Exception as e:
                    logger.warning(f"Failed to delete temp file {tmp_path}: {e}")

    # ============================
    # Matching Operations
    # ============================

    @staticmethod
    def find_matching_jobs(cv_id: int, top_k: int = 5) -> List[Dict]:
        """
        Find top-K matching jobs for a CV.
        Uses vector similarity matching.
        
        Args:
            cv_id: CV ID
            top_k: Number of top matches to return (default: 5)
            
        Returns:
            List of matching jobs with scores
        """
        return CVRepository.find_matching_jobs(cv_id, top_k)

    @staticmethod
    def calculate_cv_jd_match(cv_id: int, job_id: int) -> Dict:
        """
        Calculate detailed match score between a CV and a Job.
        
        Args:
            cv_id: CV ID
            job_id: Job ID
            
        Returns:
            Match result with detailed scores
        """
        return CVRepository.calculate_cv_jd_match(cv_id, job_id)