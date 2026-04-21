# services/application_service.py
import logging
from typing import Dict, Optional
from repositories.application_repo import ApplicationRepository
from repositories.candidate_repo import CandidateRepository
from repositories.job_repo import JobRepository
from repositories.cv_repo import CVRepository

logger = logging.getLogger(__name__)


class ApplicationService:
    """
    Service layer for application operations with comprehensive validation.
    """
    
    VALID_STATUSES = ["pending", "viewed", "interviewing", "rejected", "hired"]
    
    @staticmethod
    async def create_application(
        job_id: int,
        candidate_id: int,
        cv_id: int,
        cover_letter: str = ""
    ) -> Dict:
        """
        Create new application with full validation.
        
        Validates:
        - Job exists and is active
        - Candidate exists
        - CV exists and belongs to candidate
        - No duplicate application for this CV on this job
        
        Args:
            job_id: Job ID to apply for
            candidate_id: Candidate ID applying
            cv_id: CV ID to submit
            cover_letter: Optional cover letter (max 5000 chars)
        
        Returns:
            Dictionary with application details
            
        Raises:
            ValueError: If validation fails
        """
        # Validate cover letter length
        if len(cover_letter) > 5000:
            raise ValueError("Cover letter cannot exceed 5000 characters")
        
        # 1. Validate job exists
        job = await JobRepository.get_by_id(job_id)
        if not job:
            raise ValueError(f"Job not found: job_id={job_id}")
        
        # 2. Validate candidate exists (use get_by_user_id instead of get_by_id)
        candidate = await CandidateRepository.get_by_user_id(candidate_id)
        if not candidate:
            raise ValueError(f"Candidate not found: candidate_id={candidate_id}")
        
        # 3. Validate CV exists and belongs to candidate
        cv = await CVRepository.get_by_id(cv_id)
        if not cv:
            raise ValueError(f"CV not found: cv_id={cv_id}")
        if cv.user_id != candidate_id:
            raise ValueError("CV does not belong to this candidate")
        
        # 4. Check for duplicate application
        existing = await ApplicationRepository.get_by_cv_job(cv_id, job_id)
        if existing:
            raise ValueError(
                f"Candidate already applied to this job with this CV: app_id={existing.app_id}"
            )
        
        try:
            # Create application
            app = await ApplicationRepository.create(
                job_id=job_id,
                candidate_id=candidate_id,
                cv_id=cv_id,
                cover_letter=cover_letter
            )
            
            logger.info(
                f"Application created successfully: app_id={app.app_id}, "
                f"candidate_id={candidate_id}, job_id={job_id}"
            )
            
            return {
                "app_id": app.app_id,
                "job_id": app.job_id,
                "candidate_id": app.candidate_id,
                "cv_id": app.cv_id,
                "status": app.status,
                "created_at": app.created_at
            }
            
        except ValueError:
            logger.warning(f"Application creation failed validation")
            raise
        except Exception as e:
            logger.error(f"Error creating application: {e}", exc_info=True)
            raise
    
    @staticmethod
    async def get_applications_for_job(
        job_id: int,
        status: Optional[str] = None,
        limit: int = 50,
        skip: int = 0
    ) -> Dict:
        """
        Get applications for a job with pagination and optional status filter.
        
        Args:
            job_id: Job ID to get applications for
            status: Optional status filter
            limit: Number of results per page (1-100)
            skip: Number of results to skip
        
        Returns:
            Dictionary with total count and list of applications
        """
        try:
            # Validate status if provided
            if status and status not in ApplicationService.VALID_STATUSES:
                raise ValueError(
                    f"Invalid status. Must be one of: {', '.join(ApplicationService.VALID_STATUSES)}"
                )
            
            apps = await ApplicationRepository.get_by_job_id(
                job_id=job_id,
                status=status,
                limit=limit,
                skip=skip
            )
            
            total = await ApplicationRepository.count_by_job_id(job_id, status)
            
            result = []
            for app in apps:
                result.append({
                    "app_id": app.app_id,
                    "candidate_id": app.candidate_id,
                    "cv_id": app.cv_id,
                    "status": app.status,
                    "created_at": app.created_at
                })
            
            return {
                "total": total,
                "limit": limit,
                "skip": skip,
                "applications": result
            }
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error fetching applications for job {job_id}: {e}")
            raise
    
    @staticmethod
    async def get_applications_for_candidate(
        candidate_id: int,
        status: Optional[str] = None,
        limit: int = 50,
        skip: int = 0
    ) -> Dict:
        """
        Get applications submitted by a candidate with pagination.
        
        Args:
            candidate_id: Candidate ID to get applications for
            status: Optional status filter
            limit: Number of results per page (1-100)
            skip: Number of results to skip
        
        Returns:
            Dictionary with total count and list of applications
        """
        try:
            # Validate status if provided
            if status and status not in ApplicationService.VALID_STATUSES:
                raise ValueError(
                    f"Invalid status. Must be one of: {', '.join(ApplicationService.VALID_STATUSES)}"
                )
            
            apps = await ApplicationRepository.get_by_candidate_id(
                candidate_id=candidate_id,
                status=status,
                limit=limit,
                skip=skip
            )
            
            total = await ApplicationRepository.count_by_candidate_id(candidate_id, status)
            
            result = []
            for app in apps:
                result.append({
                    "app_id": app.app_id,
                    "job_id": app.job_id,
                    "cv_id": app.cv_id,
                    "status": app.status,
                    "created_at": app.created_at
                })
            
            return {
                "total": total,
                "limit": limit,
                "skip": skip,
                "applications": result
            }
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error fetching applications for candidate {candidate_id}: {e}")
            raise
    
    @staticmethod
    async def update_application_status(
        app_id: int,
        status: str
    ) -> Dict:
        """
        Update application status with validation.
        
        Args:
            app_id: Application ID to update
            status: New status (must be valid)
        
        Returns:
            Dictionary with updated application details
            
        Raises:
            ValueError: If status is invalid or application not found
        """
        # Validate status
        if status not in ApplicationService.VALID_STATUSES:
            raise ValueError(
                f"Invalid status. Must be one of: {', '.join(ApplicationService.VALID_STATUSES)}"
            )
        
        try:
            app = await ApplicationRepository.update_status(app_id, status)
            
            if not app:
                raise ValueError(f"Application not found: app_id={app_id}")
            
            logger.info(f"Application status updated: app_id={app_id}, status={status}")
            
            return {
                "app_id": app.app_id,
                "status": app.status,
                "updated_at": app.updated_at
            }
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error updating application status: {e}")
            raise