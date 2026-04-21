from typing import Optional, List, Dict
from fastapi import HTTPException, status
from repositories.job_repo import JobRepository
from models.jobPost import JobPost
import logging
import os
import tempfile

logger = logging.getLogger(__name__)

class JobService:

    # ============================
    # Basic CRUD Operations
    # ============================

    @staticmethod
    async def create_job(recruiter_id: int, title: str, role: str, location: str,
                        job_type: str, experience_level: str, skills: list,
                        salary_min: Optional[float], salary_max: Optional[float],
                        full_text: Optional[str], pdf_url: Optional[str]) -> JobPost:
        """Create Job manually without parsing/embedding"""
        return await JobRepository.create(recruiter_id, title, role, location, job_type,
                                         experience_level, skills, salary_min, salary_max, full_text, pdf_url)

    @staticmethod
    async def get_job(job_id: int) -> JobPost:
        """Get single job by ID"""
        job = await JobRepository.get_by_id(job_id)
        if not job:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
        return job

    @staticmethod
    async def get_all_jobs() -> List[JobPost]:
        """Get all jobs"""
        return await JobRepository.get_all()

    @staticmethod
    async def get_recruiter_jobs(recruiter_id: int) -> List[JobPost]:
        """Get all jobs posted by a recruiter"""
        return await JobRepository.get_by_recruiter(recruiter_id)

    @staticmethod
    async def update_job(job_id: int, **kwargs) -> JobPost:
        """Update job by ID"""
        job = await JobRepository.update(job_id, **kwargs)
        if not job:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
        return job

    @staticmethod
    async def delete_job(job_id: int) -> bool:
        """Delete job by ID"""
        result = await JobRepository.delete(job_id)
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
        return True

    # ============================
    # Upload & Parsing Operations
    # ============================

    @staticmethod
    async def upload_job_from_text(
        recruiter_id: int,
        full_text: str,
        title: Optional[str] = None,
        role: Optional[str] = None,
        location: Optional[str] = None,
        job_type: Optional[str] = None,
        experience_level: Optional[str] = None,
        salary_min: Optional[float] = None,
        salary_max: Optional[float] = None,
        pdf_url: Optional[str] = None
    ) -> JobPost:
        """
        Upload Job from full text description.
        Automatically parses and generates embeddings.
        
        Args:
            recruiter_id: Recruiter ID
            full_text: Full job description text
            title: Optional job title (parsed if not provided)
            role: Optional role
            location: Optional location
            job_type: Optional job type
            experience_level: Optional experience level
            salary_min: Optional minimum salary
            salary_max: Optional maximum salary
            pdf_url: Optional URL to PDF
            
        Returns:
            JobPost object
        """
        try:
            return await JobRepository.upload_job_from_text(
                recruiter_id, full_text, title, role, location,
                job_type, experience_level, salary_min, salary_max, pdf_url
            )
        except Exception as e:
            logger.error(f"Failed to upload job from text: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                              detail=f"Failed to upload job: {str(e)}")

    @staticmethod
    async def upload_job_from_pdf(
        recruiter_id: int,
        pdf_path: str,
        title: Optional[str] = None,
        role: Optional[str] = None,
        location: Optional[str] = None,
        job_type: Optional[str] = None,
        experience_level: Optional[str] = None,
        salary_min: Optional[float] = None,
        salary_max: Optional[float] = None,
        pdf_url: Optional[str] = None
    ) -> JobPost:
        """
        Upload Job from PDF file.
        Automatically parses and generates embeddings.
        
        Args:
            recruiter_id: Recruiter ID
            pdf_path: Path to PDF file
            Other args: Same as upload_job_from_text
            
        Returns:
            JobPost object
        """
        try:
            return await JobRepository.upload_job_from_pdf(
                recruiter_id, pdf_path, title, role, location,
                job_type, experience_level, salary_min, salary_max, pdf_url
            )
        except Exception as e:
            logger.error(f"Failed to upload job from PDF: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                              detail=f"Failed to upload job: {str(e)}")

    @staticmethod
    async def upload_file(recruiter_id: int, file, 
                         title: Optional[str] = None,
                         role: Optional[str] = None,
                         location: Optional[str] = None,
                         job_type: Optional[str] = None,
                         experience_level: Optional[str] = None,
                         salary_min: Optional[float] = None,
                         salary_max: Optional[float] = None):
        """
        Upload Job from file (PDF or text).
        Wrapper for handling file uploads from API.
        """
        tmp_path = None
        try:
            filename = file.filename.lower()
            if filename.endswith('.pdf'):
                # For PDF: save temporarily and process
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                    content = await file.read()
                    tmp.write(content)
                    tmp.flush()
                    tmp_path = tmp.name
                
                job = await JobService.upload_job_from_pdf(
                    recruiter_id, tmp_path, title, role, location,
                    job_type, experience_level, salary_min, salary_max
                )
                return job
            else:
                # For text files
                content = await file.read()
                text = content.decode('utf-8')
                return await JobService.upload_job_from_text(
                    recruiter_id, text, title, role, location,
                    job_type, experience_level, salary_min, salary_max
                )
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
    def find_matching_cvs(job_id: int, top_k: int = 5) -> List[Dict]:
        """
        Find top-K matching CVs for a Job.
        Uses vector similarity matching.
        
        Args:
            job_id: Job ID
            top_k: Number of top matches to return (default: 5)
            
        Returns:
            List of matching CVs with scores and user info
        """
        return JobRepository.find_matching_cvs(job_id, top_k)

    @staticmethod
    def calculate_jd_cv_match(job_id: int, cv_id: int) -> Dict:
        """
        Calculate detailed match score between a Job and a CV.
        
        Args:
            job_id: Job ID
            cv_id: CV ID
            
        Returns:
            Match result with detailed scores
        """
        return JobRepository.calculate_jd_cv_match(job_id, cv_id)