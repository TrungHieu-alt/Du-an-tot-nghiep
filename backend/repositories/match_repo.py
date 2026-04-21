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
            MatchResult.cv_id == cv_id,
            MatchResult.job_id == job_id
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
            MatchResult.cv_id == cv_id,
            MatchResult.job_id == job_id
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
            MatchResult.cv_id == cv_id,
            MatchResult.score >= min_score
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
            MatchResult.job_id == job_id,
            MatchResult.score >= min_score
        ).sort([("score", -1)])
        
        if skip > 0:
            query = query.skip(skip)
        if limit:
            query = query.limit(limit)
            
        return await query.to_list(limit)
    
    @staticmethod
    async def get_top_k_by_cv_id(cv_id: int, top_k: int) -> List[MatchResult]:
        """Get TOP K matches for a CV, sorted by score (desc)"""
        return await MatchResult.find(
            MatchResult.cv_id == cv_id
        ).sort([("score", -1)]).limit(top_k).to_list(top_k)
    
    @staticmethod
    async def get_top_k_by_job_id(job_id: int, top_k: int) -> List[MatchResult]:
        """Get TOP K matches for a Job, sorted by score (desc)"""
        return await MatchResult.find(
            MatchResult.job_id == job_id
        ).sort([("score", -1)]).limit(top_k).to_list(top_k)
    
    @staticmethod
    async def delete_cv_job_pair(cv_id: int, job_id: int) -> int:
        """Delete specific match between CV and Job"""
        result = await MatchResult.find(
            MatchResult.cv_id == cv_id,
            MatchResult.job_id == job_id
        ).delete()
        return result.deleted_count if result else 0
    
    @staticmethod
    async def delete_matches_outside_top_k_for_cv(cv_id: int, top_k: int) -> int:
        """Delete matches for CV that are outside TOP K"""
        # Get all matches for this CV, sorted by score
        all_matches = await MatchResult.find(
            MatchResult.cv_id == cv_id
        ).sort([("score", -1)]).to_list(None)
        
        # Delete matches beyond TOP K
        if len(all_matches) > top_k:
            matches_to_delete = all_matches[top_k:]
            job_ids_to_delete = [m.job_id for m in matches_to_delete]
            
            result = await MatchResult.find(
                MatchResult.cv_id == cv_id,
                MatchResult.job_id.in_(job_ids_to_delete)
            ).delete()
            return result.deleted_count if result else 0
        
        return 0
    
    @staticmethod
    async def delete_matches_outside_top_k_for_job(job_id: int, top_k: int) -> int:
        """Delete matches for Job that are outside TOP K"""
        # Get all matches for this job, sorted by score
        all_matches = await MatchResult.find(
            MatchResult.job_id == job_id
        ).sort([("score", -1)]).to_list(None)
        
        # Delete matches beyond TOP K
        if len(all_matches) > top_k:
            matches_to_delete = all_matches[top_k:]
            cv_ids_to_delete = [m.cv_id for m in matches_to_delete]
            
            result = await MatchResult.find(
                MatchResult.job_id == job_id,
                MatchResult.cv_id.in_(cv_ids_to_delete)
            ).delete()
            return result.deleted_count if result else 0
        
        return 0
    
    @staticmethod
    async def count_by_job_id(job_id: int, min_score: float = 0.0) -> int:
        """Count matches for a job"""
        return await MatchResult.find(
            MatchResult.job_id == job_id,
            MatchResult.score >= min_score
        ).count()
    
    @staticmethod
    async def count_by_cv_id(cv_id: int, min_score: float = 0.0) -> int:
        """Count matches for a CV"""
        return await MatchResult.find(
            MatchResult.cv_id == cv_id,
            MatchResult.score >= min_score
        ).count()
    
    @staticmethod
    async def delete_by_cv_id(cv_id: int) -> int:
        """Delete all matches for a CV (cascade delete) - only on CV deletion"""
        result = await MatchResult.find(MatchResult.cv_id == cv_id).delete()
        return result.deleted_count if result else 0
    
    @staticmethod
    async def delete_by_job_id(job_id: int) -> int:
        """Delete all matches for a Job (cascade delete) - only on Job deletion"""
        result = await MatchResult.find(MatchResult.job_id == job_id).delete()
        return result.deleted_count if result else 0