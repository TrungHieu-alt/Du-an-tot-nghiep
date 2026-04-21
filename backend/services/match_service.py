# services/match_service.py
import logging
from typing import List, Dict
from repositories.match_repo import MatchRepository
from repositories.cv_repo import CVRepository
from repositories.job_repo import JobRepository

logger = logging.getLogger(__name__)


class MatchingService:
    """
    Service layer for matching operations.
    Manages bidirectional TOP K synchronization for CV-Job matches.
    """
    
    @staticmethod
    async def _calculate_final_score(match: Dict) -> float:
        """
        Calculate final score from hybrid matching components.
        
        Weights:
        - Cosine ANN: 20%
        - Weighted Sim: 50%
        - LLM Score: 30%
        """
        return (
            match.get("cosine_ann", 0) * 0.2 +
            match.get("weighted_sim", 0) * 0.5 +
            (match.get("llm_score", 0) / 100) * 0.3
        )
    
    @staticmethod
    async def _build_match_metadata(match: Dict) -> Dict:
        """Extract and structure matching metadata from RAG result."""
        return {
            "cosine_ann": match.get("cosine_ann", 0),
            "weighted_sim": match.get("weighted_sim", 0),
            "llm_score": match.get("llm_score", 0),
            "reason": match.get("reason", "")
        }
    
    @staticmethod
    async def run_matching_for_job(
        job_id: int,
        top_k: int = 50,
        min_score: float = 0.7
    ) -> Dict:
        """
        Run matching process for a job: find top CVs and maintain TOP K matches.
        
        Logic:
        - Get top CVs from RAG
        - Create/update matches if score >= min_score
        - Delete matches outside TOP K for this job
        - Ensures job has at most TOP K best CV matches
        
        Args:
            job_id: Job ID to match
            top_k: Maximum number of matches to keep for this job
            min_score: Minimum score threshold to save (0.0-1.0)
            
        Returns:
            Summary with counts and top matches
        """
        try:
            logger.info(f"Starting matching for job_id={job_id}, top_k={top_k}")
            
            # Get matching CVs using RAG logic
            matches = JobRepository.find_matching_cvs(job_id, top_k=top_k)
            
            if not matches:
                logger.warning(f"No matches found for job_id={job_id}")
                # Still clean up old matches outside TOP K
                await MatchRepository.delete_matches_outside_top_k_for_job(job_id, top_k)
                return {
                    "job_id": job_id,
                    "total_found": 0,
                    "total_saved": 0,
                    "matches": []
                }
            
            # Process matches: create/update if meets threshold
            saved_count = 0
            saved_matches = []
            
            for match in matches:
                cv_id = match.get("cv_id")
                if not cv_id:
                    continue
                
                # Calculate final score
                final_score = await MatchingService._calculate_final_score(match)
                
                # Only save if meets threshold
                if final_score >= min_score:
                    metadata = await MatchingService._build_match_metadata(match)
                    
                    # Create or update match (don't delete old matches yet)
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
            
            # Clean up matches outside TOP K for this job
            deleted_count = await MatchRepository.delete_matches_outside_top_k_for_job(
                job_id, top_k
            )
            
            logger.info(
                f"Job {job_id}: Saved {saved_count}/{len(matches)} matches, "
                f"deleted {deleted_count} matches outside TOP K"
            )
            
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
        Run matching process for a CV: find top Jobs and maintain TOP K matches.
        
        Logic:
        - Get top Jobs from RAG
        - Create/update matches if score >= min_score
        - Delete matches outside TOP K for this CV
        - Ensures CV has at most TOP K best Job matches
        
        Args:
            cv_id: CV ID to match
            top_k: Maximum number of matches to keep for this CV
            min_score: Minimum score threshold to save (0.0-1.0)
            
        Returns:
            Summary with counts and top matches
        """
        try:
            logger.info(f"Starting matching for cv_id={cv_id}, top_k={top_k}")
            
            # Get matching Jobs using RAG logic
            matches = CVRepository.find_matching_jobs(cv_id, top_k=top_k)
            
            if not matches:
                logger.warning(f"No matches found for cv_id={cv_id}")
                # Still clean up old matches outside TOP K
                await MatchRepository.delete_matches_outside_top_k_for_cv(cv_id, top_k)
                return {
                    "cv_id": cv_id,
                    "total_found": 0,
                    "total_saved": 0,
                    "matches": []
                }
            
            # Process matches: create/update if meets threshold
            saved_count = 0
            saved_matches = []
            
            for match in matches:
                job_id = match.get("job_id")
                if not job_id:
                    continue
                
                # Calculate final score
                final_score = await MatchingService._calculate_final_score(match)
                
                # Only save if meets threshold
                if final_score >= min_score:
                    metadata = await MatchingService._build_match_metadata(match)
                    
                    # Create or update match (don't delete old matches yet)
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
            
            # Clean up matches outside TOP K for this CV
            deleted_count = await MatchRepository.delete_matches_outside_top_k_for_cv(
                cv_id, top_k
            )
            
            logger.info(
                f"CV {cv_id}: Saved {saved_count}/{len(matches)} matches, "
                f"deleted {deleted_count} matches outside TOP K"
            )
            
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
        Get stored matches for a job with enriched CV data.
        Enrichment happens at query time, not stored in DB.
        
        Returns:
            List of matches with CV details
        """
        # Get match results from DB (only IDs and scores)
        matches = await MatchRepository.get_by_job_id(
            job_id=job_id,
            min_score=min_score,
            limit=limit,
            skip=skip
        )
        
        # Enrich with CV data on-the-fly for response
        result = []
        for match in matches:
            cv = await CVRepository.get_by_id(match.cv_id)
            if cv:
                result.append({
                    "match_id": match.match_id,
                    "cv_id": match.cv_id,
                    "score": match.score,
                    "metadata": match.metadata,
                    "created_at": match.created_at,
                    "updated_at": match.updated_at,
                    # Enriched CV data (not stored in match_results collection)
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
        Get stored matches for a CV with enriched Job data.
        Enrichment happens at query time, not stored in DB.
        
        Returns:
            List of matches with Job details
        """
        # Get match results from DB (only IDs and scores)
        matches = await MatchRepository.get_by_cv_id(
            cv_id=cv_id,
            min_score=min_score,
            limit=limit,
            skip=skip
        )
        
        # Enrich with Job data on-the-fly for response
        result = []
        for match in matches:
            job = await JobRepository.get_by_id(match.job_id)
            if job:
                result.append({
                    "match_id": match.match_id,
                    "job_id": match.job_id,
                    "score": match.score,
                    "metadata": match.metadata,
                    "created_at": match.created_at,
                    "updated_at": match.updated_at,
                    # Enriched Job data (not stored in match_results collection)
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

    @staticmethod
    async def delete_matches_for_cv(cv_id: int) -> Dict:
        """
        Delete all matches for a CV (cascade delete).
        Called only when CV is deleted.
        Note: NOT called during re-matching (which uses TOP K cleanup instead).
        """
        try:
            logger.info(f"Deleting all matches for cv_id={cv_id}")
            deleted_count = await MatchRepository.delete_by_cv_id(cv_id)
            logger.info(f"Deleted {deleted_count} matches for cv_id={cv_id}")
            
            return {
                "cv_id": cv_id,
                "deleted_count": deleted_count
            }
        except Exception as e:
            logger.error(f"Error deleting matches for cv_id={cv_id}: {e}", exc_info=True)
            raise

    @staticmethod
    async def delete_matches_for_job(job_id: int) -> Dict:
        """
        Delete all matches for a Job (cascade delete).
        Called only when Job is deleted.
        Note: NOT called during re-matching (which uses TOP K cleanup instead).
        """
        try:
            logger.info(f"Deleting all matches for job_id={job_id}")
            deleted_count = await MatchRepository.delete_by_job_id(job_id)
            logger.info(f"Deleted {deleted_count} matches for job_id={job_id}")
            
            return {
                "job_id": job_id,
                "deleted_count": deleted_count
            }
        except Exception as e:
            logger.error(f"Error deleting matches for job_id={job_id}: {e}", exc_info=True)
            raise