# ==========================================
# 1. FIXED MODELS
# ==========================================

# models/matchResult.py
from beanie import Document
from datetime import datetime
from pymongo import IndexModel


class MatchResult(Document):
    match_id: int  # Changed from 'id' to 'match_id'
    cv_id: int
    job_id: int
    score: float
    metadata: dict = {}  # Store additional match info (field scores, reason, etc.)
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()

    class Settings:
        name = "match_results"
        indexes = [
            IndexModel([("cv_id", 1), ("job_id", 1)], unique=True),
            IndexModel([("job_id", 1), ("score", -1)]),  # For sorting by score
            IndexModel([("cv_id", 1), ("score", -1)]),
        ]


# models/application.py
from beanie import Document
from datetime import datetime
from typing import Literal


class Application(Document):
    app_id: int  # Changed from 'id' to 'app_id'
    job_id: int
    candidate_id: int
    cv_id: int
    match_id: int = None  # Link to match result
    status: Literal["pending", "viewed", "interviewing", "rejected", "hired"] = "pending"
    cover_letter: str = ""
    applied_at: datetime = datetime.utcnow()
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()

    class Settings:
        name = "applications"
        indexes = [
            IndexModel([("job_id", 1), ("status", 1)]),
            IndexModel([("candidate_id", 1), ("status", 1)]),
            IndexModel([("cv_id", 1), ("job_id", 1)], unique=True),  # Prevent duplicate applications
        ]


# ==========================================
# 2. FIXED REPOSITORIES
# ==========================================

# repositories/match_repo.py
from typing import Optional, List, Dict
from models.matchResult import MatchResult
from datetime import datetime


class MatchRepository:
    
    @staticmethod
    async def create_or_update(
        cv_id: int, 
        job_id: int, 
        score: float,
        metadata: Dict = None
    ) -> MatchResult:
        """Create or update match result"""
        existing = await MatchResult.find_one(
            (MatchResult.cv_id == cv_id) & (MatchResult.job_id == job_id)
        )
        
        if existing:
            update_data = {
                "score": score,
                "updated_at": datetime.utcnow()
            }
            if metadata:
                update_data["metadata"] = metadata
            
            await existing.update({"$set": update_data})
            return await MatchRepository.get_by_cv_job(cv_id, job_id)
        
        # Create new match
        last_match = await MatchResult.find().sort([("match_id", -1)]).limit(1).to_list(1)
        match_id = (last_match[0].match_id + 1) if last_match else 1
        
        match = MatchResult(
            match_id=match_id,
            cv_id=cv_id,
            job_id=job_id,
            score=score,
            metadata=metadata or {}
        )
        await match.insert()
        return match

    @staticmethod
    async def get_by_id(match_id: int) -> Optional[MatchResult]:
        """Get match by match_id"""
        return await MatchResult.find_one(MatchResult.match_id == match_id)

    @staticmethod
    async def get_by_cv_job(cv_id: int, job_id: int) -> Optional[MatchResult]:
        """Get match between specific CV and Job"""
        return await MatchResult.find_one(
            (MatchResult.cv_id == cv_id) & (MatchResult.job_id == job_id)
        )

    @staticmethod
    async def get_by_cv_id(
        cv_id: int, 
        min_score: float = 0.0,
        limit: int = None,
        skip: int = 0
    ) -> List[MatchResult]:
        """Get all matches for a CV, sorted by score"""
        query = MatchResult.find(
            (MatchResult.cv_id == cv_id) & (MatchResult.score >= min_score)
        ).sort([("score", -1)])
        
        if skip > 0:
            query = query.skip(skip)
        if limit:
            query = query.limit(limit)
            
        return await query.to_list(limit)

    @staticmethod
    async def get_by_job_id(
        job_id: int,
        min_score: float = 0.0,
        limit: int = None,
        skip: int = 0
    ) -> List[MatchResult]:
        """Get all matches for a Job, sorted by score"""
        query = MatchResult.find(
            (MatchResult.job_id == job_id) & (MatchResult.score >= min_score)
        ).sort([("score", -1)])
        
        if skip > 0:
            query = query.skip(skip)
        if limit:
            query = query.limit(limit)
            
        return await query.to_list(limit)
    
    @staticmethod
    async def count_by_job_id(job_id: int, min_score: float = 0.0) -> int:
        """Count matches for a job"""
        return await MatchResult.find(
            (MatchResult.job_id == job_id) & (MatchResult.score >= min_score)
        ).count()
    
    @staticmethod
    async def count_by_cv_id(cv_id: int, min_score: float = 0.0) -> int:
        """Count matches for a CV"""
        return await MatchResult.find(
            (MatchResult.cv_id == cv_id) & (MatchResult.score >= min_score)
        ).count()
    
    @staticmethod
    async def delete_by_cv_id(cv_id: int) -> int:
        """Delete all matches for a CV (cascade delete)"""
        result = await MatchResult.find(MatchResult.cv_id == cv_id).delete()
        return result.deleted_count if result else 0
    
    @staticmethod
    async def delete_by_job_id(job_id: int) -> int:
        """Delete all matches for a Job (cascade delete)"""
        result = await MatchResult.find(MatchResult.job_id == job_id).delete()
        return result.deleted_count if result else 0


# repositories/application_repo.py
from typing import Optional, List
from models.application import Application
from datetime import datetime


class ApplicationRepository:
    
    @staticmethod
    async def create(
        job_id: int, 
        candidate_id: int, 
        cv_id: int,
        match_id: int = None,
        cover_letter: str = ""
    ) -> Application:
        """Create new application"""
        # Check if already applied
        existing = await Application.find_one(
            (Application.cv_id == cv_id) & (Application.job_id == job_id)
        )
        if existing:
            raise ValueError(f"Application already exists: app_id={existing.app_id}")
        
        # Generate new app_id
        last_app = await Application.find().sort([("app_id", -1)]).limit(1).to_list(1)
        app_id = (last_app[0].app_id + 1) if last_app else 1

        app = Application(
            app_id=app_id,
            job_id=job_id,
            candidate_id=candidate_id,
            cv_id=cv_id,
            match_id=match_id,
            cover_letter=cover_letter,
            status="pending",
        )
        await app.insert()
        return app

    @staticmethod
    async def get_by_id(app_id: int) -> Optional[Application]:
        """Get application by app_id"""
        return await Application.find_one(Application.app_id == app_id)

    @staticmethod
    async def get_by_job_id(
        job_id: int,
        status: str = None,
        limit: int = None,
        skip: int = 0
    ) -> List[Application]:
        """Get applications for a job, optionally filtered by status"""
        if status:
            query = Application.find(
                (Application.job_id == job_id) & (Application.status == status)
            )
        else:
            query = Application.find(Application.job_id == job_id)
        
        query = query.sort([("applied_at", -1)])
        
        if skip > 0:
            query = query.skip(skip)
        if limit:
            query = query.limit(limit)
            
        return await query.to_list(limit)

    @staticmethod
    async def get_by_candidate_id(
        candidate_id: int,
        status: str = None,
        limit: int = None,
        skip: int = 0
    ) -> List[Application]:
        """Get applications by a candidate, optionally filtered by status"""
        if status:
            query = Application.find(
                (Application.candidate_id == candidate_id) & (Application.status == status)
            )
        else:
            query = Application.find(Application.candidate_id == candidate_id)
        
        query = query.sort([("applied_at", -1)])
        
        if skip > 0:
            query = query.skip(skip)
        if limit:
            query = query.limit(limit)
            
        return await query.to_list(limit)
    
    @staticmethod
    async def get_by_cv_job(cv_id: int, job_id: int) -> Optional[Application]:
        """Check if application exists for CV and Job"""
        return await Application.find_one(
            (Application.cv_id == cv_id) & (Application.job_id == job_id)
        )
    
    @staticmethod
    async def count_by_job_id(job_id: int, status: str = None) -> int:
        """Count applications for a job"""
        if status:
            return await Application.find(
                (Application.job_id == job_id) & (Application.status == status)
            ).count()
        return await Application.find(Application.job_id == job_id).count()
    
    @staticmethod
    async def count_by_candidate_id(candidate_id: int, status: str = None) -> int:
        """Count applications by a candidate"""
        if status:
            return await Application.find(
                (Application.candidate_id == candidate_id) & (Application.status == status)
            ).count()
        return await Application.find(Application.candidate_id == candidate_id).count()

    @staticmethod
    async def update(app_id: int, **kwargs) -> Optional[Application]:
        """Update application"""
        app = await Application.find_one(Application.app_id == app_id)
        if app:
            kwargs["updated_at"] = datetime.utcnow()
            await app.update({"$set": kwargs})
            return await ApplicationRepository.get_by_id(app_id)
        return None
    
    @staticmethod
    async def update_status(app_id: int, status: str) -> Optional[Application]:
        """Update application status"""
        return await ApplicationRepository.update(app_id, status=status)

    @staticmethod
    async def delete(app_id: int) -> bool:
        """Delete application"""
        app = await Application.find_one(Application.app_id == app_id)
        if app:
            await app.delete()
            return True
        return False


# ==========================================
# 3. MATCHING SERVICE (Business Logic Layer)
# ==========================================

# services/matching_service.py
import logging
from typing import List, Dict, Optional
from repositories.match_repo import MatchRepository
from repositories.cv_repo import CVRepository
from repositories.job_repo import JobRepository

logger = logging.getLogger(__name__)


class MatchingService:
    """
    Service layer for matching operations.
    Coordinates between repositories and RAG logic.
    """
    
    @staticmethod
    async def run_matching_for_job(
        job_id: int,
        top_k: int = 50,
        min_score: float = 0.7
    ) -> Dict:
        """
        Run matching process for a job: find top CVs and store results.
        
        Args:
            job_id: Job ID to match
            top_k: Number of top matches to find
            min_score: Minimum score threshold to save (0.0-1.0)
            
        Returns:
            Summary with counts and top matches
        """
        try:
            logger.info(f"Starting matching for job_id={job_id}")
            
            # Get matching CVs using RAG logic
            matches = JobRepository.find_matching_cvs(job_id, top_k=top_k)
            
            if not matches:
                logger.warning(f"No matches found for job_id={job_id}")
                return {
                    "job_id": job_id,
                    "total_found": 0,
                    "total_saved": 0,
                    "matches": []
                }
            
            # Save matches to database
            saved_count = 0
            saved_matches = []
            
            for match in matches:
                cv_id = match.get("cv_id")
                if not cv_id:
                    continue
                
                # Calculate final score from hybrid matching
                final_score = (
                    match.get("cosine_ann", 0) * 0.2 +
                    match.get("weighted_sim", 0) * 0.5 +
                    (match.get("llm_score", 0) / 100) * 0.3
                )
                
                # Only save if meets threshold
                if final_score >= min_score:
                    metadata = {
                        "cosine_ann": match.get("cosine_ann", 0),
                        "weighted_sim": match.get("weighted_sim", 0),
                        "llm_score": match.get("llm_score", 0),
                        "reason": match.get("reason", ""),
                        "user_id": match.get("user_id")
                    }
                    
                    match_result = await MatchRepository.create_or_update(
                        cv_id=cv_id,
                        job_id=job_id,
                        score=final_score,
                        metadata=metadata
                    )
                    
                    saved_count += 1
                    saved_matches.append({
                        "match_id": match_result.match_id,
                        "cv_id": cv_id,
                        "score": final_score,
                        "reason": metadata["reason"]
                    })
            
            logger.info(f"Saved {saved_count}/{len(matches)} matches for job_id={job_id}")
            
            return {
                "job_id": job_id,
                "total_found": len(matches),
                "total_saved": saved_count,
                "min_score": min_score,
                "matches": saved_matches[:10]  # Return top 10 for preview
            }
            
        except Exception as e:
            logger.error(f"Error in run_matching_for_job: {e}", exc_info=True)
            raise
    
    @staticmethod
    async def run_matching_for_cv(
        cv_id: int,
        top_k: int = 50,
        min_score: float = 0.7
    ) -> Dict:
        """
        Run matching process for a CV: find top Jobs and store results.
        
        Args:
            cv_id: CV ID to match
            top_k: Number of top matches to find
            min_score: Minimum score threshold to save (0.0-1.0)
            
        Returns:
            Summary with counts and top matches
        """
        try:
            logger.info(f"Starting matching for cv_id={cv_id}")
            
            # Get matching Jobs using RAG logic
            matches = CVRepository.find_matching_jobs(cv_id, top_k=top_k)
            
            if not matches:
                logger.warning(f"No matches found for cv_id={cv_id}")
                return {
                    "cv_id": cv_id,
                    "total_found": 0,
                    "total_saved": 0,
                    "matches": []
                }
            
            # Save matches to database
            saved_count = 0
            saved_matches = []
            
            for match in matches:
                job_id = match.get("job_id")
                if not job_id:
                    continue
                
                # Calculate final score from hybrid matching
                final_score = (
                    match.get("cosine_ann", 0) * 0.2 +
                    match.get("weighted_sim", 0) * 0.5 +
                    (match.get("llm_score", 0) / 100) * 0.3
                )
                
                # Only save if meets threshold
                if final_score >= min_score:
                    metadata = {
                        "cosine_ann": match.get("cosine_ann", 0),
                        "weighted_sim": match.get("weighted_sim", 0),
                        "llm_score": match.get("llm_score", 0),
                        "reason": match.get("reason", "")
                    }
                    
                    match_result = await MatchRepository.create_or_update(
                        cv_id=cv_id,
                        job_id=job_id,
                        score=final_score,
                        metadata=metadata
                    )
                    
                    saved_count += 1
                    saved_matches.append({
                        "match_id": match_result.match_id,
                        "job_id": job_id,
                        "score": final_score,
                        "reason": metadata["reason"]
                    })
            
            logger.info(f"Saved {saved_count}/{len(matches)} matches for cv_id={cv_id}")
            
            return {
                "cv_id": cv_id,
                "total_found": len(matches),
                "total_saved": saved_count,
                "min_score": min_score,
                "matches": saved_matches[:10]  # Return top 10 for preview
            }
            
        except Exception as e:
            logger.error(f"Error in run_matching_for_cv: {e}", exc_info=True)
            raise
    
    @staticmethod
    async def get_matches_for_job(
        job_id: int,
        min_score: float = 0.0,
        limit: int = 50,
        skip: int = 0
    ) -> List[Dict]:
        """
        Get stored matches for a job with enriched data.
        
        Returns:
            List of matches with CV details
        """
        matches = await MatchRepository.get_by_job_id(
            job_id=job_id,
            min_score=min_score,
            limit=limit,
            skip=skip
        )
        
        # Enrich with CV data
        result = []
        for match in matches:
            cv = await CVRepository.get_by_id(match.cv_id)
            if cv:
                result.append({
                    "match_id": match.match_id,
                    "cv_id": match.cv_id,
                    "score": match.score,
                    "metadata": match.metadata,
                    "cv": {
                        "title": cv.title,
                        "location": cv.location,
                        "experience": cv.experience,
                        "skills": cv.skills,
                        "user_id": cv.user_id
                    }
                })
        
        return result
    
    @staticmethod
    async def get_matches_for_cv(
        cv_id: int,
        min_score: float = 0.0,
        limit: int = 50,
        skip: int = 0
    ) -> List[Dict]:
        """
        Get stored matches for a CV with enriched data.
        
        Returns:
            List of matches with Job details
        """
        matches = await MatchRepository.get_by_cv_id(
            cv_id=cv_id,
            min_score=min_score,
            limit=limit,
            skip=skip
        )
        
        # Enrich with Job data
        result = []
        for match in matches:
            job = await JobRepository.get_by_id(match.job_id)
            if job:
                result.append({
                    "match_id": match.match_id,
                    "job_id": match.job_id,
                    "score": match.score,
                    "metadata": match.metadata,
                    "job": {
                        "title": job.title,
                        "role": job.role,
                        "location": job.location,
                        "job_type": job.job_type,
                        "experience_level": job.experience_level,
                        "skills": job.skills,
                        "recruiter_id": job.recruiter_id
                    }
                })
        
        return result


# ==========================================
# 4. APPLICATION SERVICE (Business Logic Layer)
# ==========================================

# services/application_service.py
import logging
from typing import Dict, Optional
from repositories.application_repo import ApplicationRepository
from repositories.match_repo import MatchRepository
from repositories.cv_repo import CVRepository
from repositories.job_repo import JobRepository

logger = logging.getLogger(__name__)


class ApplicationService:
    """
    Service layer for application operations.
    """
    
    @staticmethod
    async def create_application(
        job_id: int,
        candidate_id: int,
        cv_id: int,
        cover_letter: str = ""
    ) -> Dict:
        """
        Create new application. Links to match result if exists.
        
        Returns:
            Application details with related data
        """
        try:
            # Check if match exists
            match = await MatchRepository.get_by_cv_job(cv_id, job_id)
            match_id = match.match_id if match else None
            
            # Create application
            app = await ApplicationRepository.create(
                job_id=job_id,
                candidate_id=candidate_id,
                cv_id=cv_id,
                match_id=match_id,
                cover_letter=cover_letter
            )
            
            # Get related data
            cv = await CVRepository.get_by_id(cv_id)
            job = await JobRepository.get_by_id(job_id)
            
            return {
                "app_id": app.app_id,
                "job_id": app.job_id,
                "candidate_id": app.candidate_id,
                "cv_id": app.cv_id,
                "match_id": app.match_id,
                "status": app.status,
                "applied_at": app.applied_at,
                "match_score": match.score if match else None,
                "cv_title": cv.title if cv else None,
                "job_title": job.title if job else None
            }
            
        except ValueError as e:
            logger.warning(f"Application creation failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Error creating application: {e}", exc_info=True)
            raise
    
    @staticmethod
    async def get_applications_for_job(
        job_id: int,
        status: str = None,
        limit: int = 50,
        skip: int = 0
    ) -> Dict:
        """
        Get applications for a job with enriched data.
        
        Returns:
            List of applications with CV and match details
        """
        apps = await ApplicationRepository.get_by_job_id(
            job_id=job_id,
            status=status,
            limit=limit,
            skip=skip
        )
        
        total = await ApplicationRepository.count_by_job_id(job_id, status)
        
        # Enrich with CV and match data
        result = []
        for app in apps:
            cv = await CVRepository.get_by_id(app.cv_id)
            match = await MatchRepository.get_by_id(app.match_id) if app.match_id else None
            
            result.append({
                "app_id": app.app_id,
                "candidate_id": app.candidate_id,
                "status": app.status,
                "applied_at": app.applied_at,
                "match_score": match.score if match else None,
                "cv": {
                    "cv_id": app.cv_id,
                    "title": cv.title if cv else None,
                    "location": cv.location if cv else None,
                    "experience": cv.experience if cv else None,
                    "skills": cv.skills if cv else []
                }
            })
        
        return {
            "total": total,
            "applications": result
        }
    
    @staticmethod
    async def update_application_status(
        app_id: int,
        status: str
    ) -> Optional[Dict]:
        """Update application status"""
        app = await ApplicationRepository.update_status(app_id, status)
        
        if not app:
            return None
        
        return {
            "app_id": app.app_id,
            "status": app.status,
            "updated_at": app.updated_at
        }


# ==========================================
# 5. API ENDPOINTS
# ==========================================

# routes/matching_routes.py
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from services.matching_service import MatchingService

router = APIRouter(prefix="/api/matching", tags=["matching"])


class RunMatchingRequest(BaseModel):
    top_k: int = 50
    min_score: float = 0.7


@router.post("/job/{job_id}/run")
async def run_matching_for_job(
    job_id: int,
    request: RunMatchingRequest
):
    """
    Trigger matching process for a job.
    Finds top CVs and stores match results in database.
    """
    try:
        result = await MatchingService.run_matching_for_job(
            job_id=job_id,
            top_k=request.top_k,
            min_score=request.min_score
        )
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cv/{cv_id}/run")
async def run_matching_for_cv(
    cv_id: int,
    request: RunMatchingRequest
):
    """
    Trigger matching process for a CV.
    Finds top Jobs and stores match results in database.
    """
    try:
        result = await MatchingService.run_matching_for_cv(
            cv_id=cv_id,
            top_k=request.top_k,
            min_score=request.min_score
        )
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/job/{job_id}/matches")
async def get_matches_for_job(
    job_id: int,
    min_score: float = Query(0.0, ge=0.0, le=1.0),
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0)
):
    """
    Get stored matches for a job.
    Returns CVs that match this job with scores and details.
    """
    try:
        matches = await MatchingService.get_matches_for_job(
            job_id=job_id,
            min_score=min_score,
            limit=limit,
            skip=skip
        )
        
        total = await MatchRepository.count_by_job_id(job_id, min_score)
        
        return {
            "success": True,
            "data": {
                "total": total,
                "matches": matches
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cv/{cv_id}/matches")
async def get_matches_for_cv(
    cv_id: int,
    min_score: float = Query(0.0, ge=0.0, le=1.0),
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0)
):
    """
    Get stored matches for a CV.
    Returns Jobs that match this CV with scores and details.
    """
    try:
        matches = await MatchingService.get_matches_for_cv(
            cv_id=cv_id,
            min_score=min_score,
            limit=limit,
            skip=skip
        )
        
        total = await MatchRepository.count_by_cv_id(cv_id, min_score)
        
        return {
            "success": True,
            "data": {
                "total": total,
                "matches": matches
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# routes/application_routes.py
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from services.application_service import ApplicationService

router = APIRouter(prefix="/api/applications", tags=["applications"])


class CreateApplicationRequest(BaseModel):
    job_id: int
    candidate_id: int
    cv_id: int
    cover_letter: str = ""


class UpdateApplicationStatusRequest(BaseModel):
    status: str


@router.post("/")
async def create_application(request: CreateApplicationRequest):
    """
    Create new application.
    Candidate applies to a job with their CV.
    """
    try:
        result = await ApplicationService.create_application(
            job_id=request.job_id,
            candidate_id=request.candidate_id,
            cv_id=request.cv_id,
            cover_letter=request.cover_letter
        )
        return {
            "success": True,
            "data": result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/job/{job_id}")
async def get_applications_for_job(
    job_id: int,
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0)
):
    """
    Get applications for a job.
    Recruiter can see all applications for their job.
    """
    try:
        result = await ApplicationService.get_applications_for_job(
            job_id=job_id,
            status=status,
            limit=limit,
            skip=skip
        )
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/candidate/{candidate_id}")
async def get_applications_for_candidate(
    candidate_id: int,
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0)
):
    """
    Get applications by a candidate.
    Candidate can see their own applications.
    """
    try:
        apps = await ApplicationRepository.get_by_candidate_id(
            candidate_id=candidate_id,
            status=status,
            limit=limit,
            skip=skip
        )
        
        total = await ApplicationRepository.count_by_candidate_id(candidate_id, status)
        
        # Enrich with job data
        from repositories.job_repo import JobRepository
        from repositories.match_repo import MatchRepository
        
        result = []
        for app in apps:
            job = await JobRepository.get_by_id(app.job_id)
            match = await MatchRepository.get_by_id(app.match_id) if app.match_id else None
            
            result.append({
                "app_id": app.app_id,
                "status": app.status,
                "applied_at": app.applied_at,
                "match_score": match.score if match else None,
                "job": {
                    "job_id": app.job_id,
                    "title": job.title if job else None,
                    "role": job.role if job else None,
                    "location": job.location if job else None,
                    "job_type": job.job_type if job else None,
                    "experience_level": job.experience_level if job else None
                }
            })
        
        return {
            "success": True,
            "data": {
                "total": total,
                "applications": result
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{app_id}/status")
async def update_application_status(
    app_id: int,
    request: UpdateApplicationStatusRequest
):
    """
    Update application status.
    Recruiter can update status (viewed, interviewing, rejected, hired).
    """
    try:
        # Validate status
        valid_statuses = ["pending", "viewed", "interviewing", "rejected", "hired"]
        if request.status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        
        result = await ApplicationService.update_application_status(
            app_id=app_id,
            status=request.status
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="Application not found")
        
        return {
            "success": True,
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{app_id}")
async def delete_application(app_id: int):
    """
    Delete application.
    """
    try:
        from repositories.application_repo import ApplicationRepository
        
        success = await ApplicationRepository.delete(app_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Application not found")
        
        return {
            "success": True,
            "message": "Application deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# 6. REGISTRATION IN MAIN APP
# ==========================================

"""
# In your main.py or app.py, register the routes:

from routes.matching_routes import router as matching_router
from routes.application_routes import router as application_router

app = FastAPI()

# Register routers
app.include_router(matching_router)
app.include_router(application_router)
"""


# ==========================================
# 7. USAGE EXAMPLES
# ==========================================

"""
# Example 1: Run matching for a job (Recruiter creates job post)
POST /api/matching/job/123/run
Body: {
    "top_k": 50,
    "min_score": 0.7
}

Response: {
    "success": true,
    "data": {
        "job_id": 123,
        "total_found": 45,
        "total_saved": 18,
        "min_score": 0.7,
        "matches": [
            {
                "match_id": 1,
                "cv_id": 456,
                "score": 0.92,
                "reason": "Strong match on React, TypeScript..."
            },
            ...
        ]
    }
}


# Example 2: Get matches for a job (View matching candidates)
GET /api/matching/job/123/matches?min_score=0.8&limit=20

Response: {
    "success": true,
    "data": {
        "total": 18,
        "matches": [
            {
                "match_id": 1,
                "cv_id": 456,
                "score": 0.92,
                "metadata": {
                    "cosine_ann": 0.85,
                    "weighted_sim": 0.91,
                    "llm_score": 95,
                    "reason": "Strong match...",
                    "user_id": 789
                },
                "cv": {
                    "title": "Senior React Developer",
                    "location": "San Francisco",
                    "experience": "5 years",
                    "skills": ["React", "TypeScript", "Node.js"],
                    "user_id": 789
                }
            },
            ...
        ]
    }
}


# Example 3: Candidate applies to a job
POST /api/applications/
Body: {
    "job_id": 123,
    "candidate_id": 789,
    "cv_id": 456,
    "cover_letter": "I am very interested..."
}

Response: {
    "success": true,
    "data": {
        "app_id": 1,
        "job_id": 123,
        "candidate_id": 789,
        "cv_id": 456,
        "match_id": 1,
        "status": "pending",
        "applied_at": "2024-12-08T10:30:00",
        "match_score": 0.92,
        "cv_title": "Senior React Developer",
        "job_title": "Senior React Developer"
    }
}


# Example 4: Recruiter views applications for job
GET /api/applications/job/123?status=pending&limit=20

Response: {
    "success": true,
    "data": {
        "total": 15,
        "applications": [
            {
                "app_id": 1,
                "candidate_id": 789,
                "status": "pending",
                "applied_at": "2024-12-08T10:30:00",
                "match_score": 0.92,
                "cv": {
                    "cv_id": 456,
                    "title": "Senior React Developer",
                    "location": "San Francisco",
                    "experience": "5 years",
                    "skills": ["React", "TypeScript", "Node.js"]
                }
            },
            ...
        ]
    }
}


# Example 5: Recruiter updates application status
PATCH /api/applications/1/status
Body: {
    "status": "interviewing"
}

Response: {
    "success": true,
    "data": {
        "app_id": 1,
        "status": "interviewing",
        "updated_at": "2024-12-08T14:20:00"
    }
}


# Example 6: Run matching for a CV (Candidate uploads CV)
POST /api/matching/cv/456/run
Body: {
    "top_k": 50,
    "min_score": 0.7
}

Response: {
    "success": true,
    "data": {
        "cv_id": 456,
        "total_found": 35,
        "total_saved": 12,
        "min_score": 0.7,
        "matches": [
            {
                "match_id": 2,
                "job_id": 123,
                "score": 0.92,
                "reason": "Perfect fit for React position..."
            },
            ...
        ]
    }
}


# Example 7: Candidate views matched jobs
GET /api/matching/cv/456/matches?min_score=0.8

Response: {
    "success": true,
    "data": {
        "total": 12,
        "matches": [
            {
                "match_id": 2,
                "job_id": 123,
                "score": 0.92,
                "metadata": {
                    "cosine_ann": 0.87,
                    "weighted_sim": 0.93,
                    "llm_score": 94,
                    "reason": "Perfect fit..."
                },
                "job": {
                    "title": "Senior React Developer",
                    "role": "Frontend Engineer",
                    "location": "Remote",
                    "job_type": "Full-time",
                    "experience_level": "Senior",
                    "skills": ["React", "TypeScript", "Node.js"],
                    "recruiter_id": 100
                }
            },
            ...
        ]
    }
}
"""