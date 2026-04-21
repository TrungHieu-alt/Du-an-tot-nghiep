# repositories/application_repo.py
from typing import Optional, List
from models.application import Application
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ApplicationRepository:
    """
    Repository for Application data access operations.
    Handles all database interactions for applications.
    """
    
    @staticmethod
    async def create(
        job_id: int, 
        candidate_id: int, 
        cv_id: int,
        match_id: Optional[int] = None,
        cover_letter: str = ""
    ) -> Application:
        """
        Create new application with duplicate prevention.
        
        Args:
            job_id: Job ID
            candidate_id: Candidate ID
            cv_id: CV ID
            match_id: Optional match ID
            cover_letter: Optional cover letter text
        
        Returns:
            Created Application document
            
        Raises:
            ValueError: If application already exists for this CV and job
        """
        # Check if already applied with this CV to this job
        existing = await Application.find_one(
            Application.cv_id == cv_id, 
            Application.job_id == job_id
        )
        if existing:
            raise ValueError(f"Application already exists: app_id={existing.app_id}")
        
        # Generate new app_id (auto-increment)
        last_app = await Application.find().sort([("app_id", -1)]).limit(1).to_list(1)
        app_id = (last_app[0].app_id + 1) if last_app else 1

        app = Application(
            app_id=app_id,
            job_id=job_id,
            candidate_id=candidate_id,
            cv_id=cv_id,
            match_id=match_id,
            cover_letter=cover_letter,
            status="pending"
        )
        await app.insert()
        logger.debug(f"Application created in DB: app_id={app_id}")
        return app

    @staticmethod
    async def get_by_id(app_id: int) -> Optional[Application]:
        """
        Get application by ID.
        
        Args:
            app_id: Application ID
        
        Returns:
            Application document or None if not found
        """
        return await Application.find_one(Application.app_id == app_id)

    @staticmethod
    async def get_by_job_id(
        job_id: int,
        status: Optional[str] = None,
        limit: Optional[int] = None,
        skip: int = 0
    ) -> List[Application]:
        """
        Get applications for a job with optional filtering and pagination.
        
        Args:
            job_id: Job ID
            status: Optional status filter
            limit: Optional result limit
            skip: Number of results to skip
        
        Returns:
            List of Application documents
        """
        if status:
            query = Application.find(
                Application.job_id == job_id,
                Application.status == status
            )
        else:
            query = Application.find(Application.job_id == job_id)
        
        query = query.sort([("created_at", -1)])
        
        if skip > 0:
            query = query.skip(skip)
        if limit:
            query = query.limit(limit)
            
        return await query.to_list(limit)

    @staticmethod
    async def get_by_candidate_id(
        candidate_id: int,
        status: Optional[str] = None,
        limit: Optional[int] = None,
        skip: int = 0
    ) -> List[Application]:
        """
        Get applications by a candidate with optional filtering and pagination.
        
        Args:
            candidate_id: Candidate ID
            status: Optional status filter
            limit: Optional result limit
            skip: Number of results to skip
        
        Returns:
            List of Application documents
        """
        if status:
            query = Application.find(
                Application.candidate_id == candidate_id,
                Application.status == status
            )
        else:
            query = Application.find(Application.candidate_id == candidate_id)
        
        query = query.sort([("created_at", -1)])
        
        if skip > 0:
            query = query.skip(skip)
        if limit:
            query = query.limit(limit)
            
        return await query.to_list(limit)
    
    @staticmethod
    async def get_by_cv_job(cv_id: int, job_id: int) -> Optional[Application]:
        """
        Check if application exists for a specific CV and job combination.
        
        Args:
            cv_id: CV ID
            job_id: Job ID
        
        Returns:
            Application document or None if not found
        """
        return await Application.find_one(
            Application.cv_id == cv_id,
            Application.job_id == job_id
        )
    
    @staticmethod
    async def count_by_job_id(job_id: int, status: Optional[str] = None) -> int:
        """
        Count applications for a job.
        
        Args:
            job_id: Job ID
            status: Optional status filter
        
        Returns:
            Number of matching applications
        """
        if status:
            return await Application.find(
                Application.job_id == job_id,
                Application.status == status
            ).count()
        return await Application.find(Application.job_id == job_id).count()
    
    @staticmethod
    async def count_by_candidate_id(candidate_id: int, status: Optional[str] = None) -> int:
        """
        Count applications by a candidate.
        
        Args:
            candidate_id: Candidate ID
            status: Optional status filter
        
        Returns:
            Number of matching applications
        """
        if status:
            return await Application.find(
                Application.candidate_id == candidate_id,
                Application.status == status
            ).count()
        return await Application.find(Application.candidate_id == candidate_id).count()

    @staticmethod
    async def update(app_id: int, **kwargs) -> Optional[Application]:
        """
        Update application with provided fields.
        Automatically updates the updated_at timestamp.
        
        Args:
            app_id: Application ID
            **kwargs: Fields to update
        
        Returns:
            Updated Application document or None if not found
        """
        app = await Application.find_one(Application.app_id == app_id)
        if app:
            kwargs["updated_at"] = datetime.utcnow()
            await app.update({"$set": kwargs})
            logger.debug(f"Application updated: app_id={app_id}")
            return await ApplicationRepository.get_by_id(app_id)
        return None
    
    @staticmethod
    async def update_status(app_id: int, status: str) -> Optional[Application]:
        """
        Update only the application status.
        
        Args:
            app_id: Application ID
            status: New status
        
        Returns:
            Updated Application document or None if not found
        """
        return await ApplicationRepository.update(app_id, status=status)

    @staticmethod
    async def delete(app_id: int) -> bool:
        """
        Delete an application by ID.
        
        Args:
            app_id: Application ID to delete
        
        Returns:
            True if deleted successfully, False if not found
        """
        app = await Application.find_one(Application.app_id == app_id)
        if app:
            await app.delete()
            logger.debug(f"Application deleted: app_id={app_id}")
            return True
        return False