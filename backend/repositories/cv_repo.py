import logging
from typing import Optional, List, Dict
from models.candidateResume import CandidateResume
from datetime import datetime

# RAG imports
from ragmodel.dataPreprocess.resumePreprocess import preprocess_resume
from ragmodel.dataPreprocess.resumeParser import parse_resume
from ragmodel.logics.embedder import embed_cv
import ragmodel.db.vectorStore as vs
from ragmodel.logics.matchingLogic import get_top_k_jds_for_cv, match_jd_to_cv

logger = logging.getLogger(__name__)

class CVRepository:
    
    # ============================
    # CRUD Operations
    # ============================
    
    @staticmethod
    async def create(
        user_id: int,
        title: str,
        location: Optional[str],
        experience: Optional[str],
        skills: List[str],
        summary: Optional[str],
        full_text: Optional[str],
        pdf_url: Optional[str],
        is_main: bool = False
    ) -> CandidateResume:
        """Create CV without embedding (basic CRUD)"""
        last_cv = await CandidateResume.find().sort([("cv_id", -1)]).limit(1).to_list(1)
        cv_id = (last_cv[0].cv_id + 1) if last_cv else 1
        
        cv = CandidateResume(
            cv_id=cv_id,
            user_id=user_id,
            title=title,
            location=location,
            experience=experience,
            skills=skills,
            summary=summary,
            full_text=full_text,
            pdf_url=pdf_url,
            is_main=is_main,
        )
        await cv.insert()
        return cv
    
    @staticmethod
    async def get_by_id(cv_id: int) -> Optional[CandidateResume]:
        return await CandidateResume.find_one(CandidateResume.cv_id == cv_id)
    
    @staticmethod
    async def get_by_user(user_id: int) -> List[CandidateResume]:
        return await CandidateResume.find(CandidateResume.user_id == user_id).to_list(None)
    
    @staticmethod
    async def get_all() -> List[CandidateResume]:
        return await CandidateResume.find().to_list(None)
    
    @staticmethod
    async def update(cv_id: int, **kwargs) -> Optional[CandidateResume]:
        cv = await CandidateResume.find_one(CandidateResume.cv_id == cv_id)
        if cv:
            kwargs["updated_at"] = datetime.utcnow()
            await cv.update({"$set": kwargs})
            return await CVRepository.get_by_id(cv_id)
        return None
    
    @staticmethod
    async def delete(cv_id: int) -> bool:
        cv = await CandidateResume.find_one(CandidateResume.cv_id == cv_id)
        if cv:
            # Delete from ChromaDB
            try:
                vs.delete_cv(f"cv_{cv_id}")
                logger.info(f"Deleted CV embeddings from ChromaDB: cv_{cv_id}")
            except Exception as e:
                logger.warning(f"Failed to delete CV embeddings: {e}")
            
            # Delete from MongoDB
            await cv.delete()
            return True
        return False
    
    # ============================
    # UPLOAD CV (PDF → Parse → Embed → Store)
    # ============================
    
    @staticmethod
    async def upload_cv_from_pdf(
        user_id: int,
        pdf_path: str,
        pdf_url: Optional[str] = None,
        is_main: bool = False
    ) -> CandidateResume:
        """
        Upload CV from PDF file.
        
        Flow:
        1. Preprocess PDF (read, translate, clean, split)
        2. Parse to structured JSON
        3. Generate embeddings
        4. Store in ChromaDB
        5. Store in MongoDB
        
        Args:
            user_id: User ID
            pdf_path: Path to PDF file
            pdf_url: Optional URL to stored PDF
            is_main: Whether this is the main CV
            
        Returns:
            CandidateResume object
        """
        try:
            # Step 1: Preprocess
            logger.info(f"Preprocessing CV from: {pdf_path}")
            preprocessed_text = preprocess_resume(pdf_path)
            
            # Step 2: Parse
            logger.info("Parsing CV...")
            cv_data = parse_resume(preprocessed_text)
            
            # Validate required fields
            if not cv_data.get("full_text"):
                cv_data["full_text"] = preprocessed_text
            
            # Step 3: Generate embeddings
            logger.info("Generating CV embeddings...")
            cv_embeddings = embed_cv(cv_data)
            
            # Step 4: Create MongoDB record first (to get cv_id)
            last_cv = await CandidateResume.find().sort([("cv_id", -1)]).limit(1).to_list(1)
            cv_id = (last_cv[0].cv_id + 1) if last_cv else 1
            
            cv = CandidateResume(
                cv_id=cv_id,
                user_id=user_id,
                title=cv_data.get("job_title", "Untitled CV"),
                location=cv_data.get("location", ""),
                experience=cv_data.get("experience", ""),
                skills=cv_data.get("skills", []),
                summary=cv_data.get("summary", ""),
                full_text=cv_data.get("full_text", ""),
                pdf_url=pdf_url,
                is_main=is_main,
                embedding=None,  # We store in ChromaDB, not here
            )
            await cv.insert()
            logger.info(f"Created CV in MongoDB: cv_id={cv_id}")
            
            # Step 5: Store embeddings in ChromaDB with user_id in metadata
            chroma_id = f"cv_{cv_id}"
            
            # Add user_id to cv_data for metadata
            cv_data_with_user = {**cv_data, "user_id": user_id, "cv_id": cv_id}
            
            vs.store_cv(chroma_id, cv_embeddings, cv_data_with_user)
            logger.info(f"Stored CV embeddings in ChromaDB: {chroma_id}")
            
            return cv
            
        except Exception as e:
            logger.error(f"Failed to upload CV: {e}", exc_info=True)
            raise
    
    @staticmethod
    async def upload_cv_from_text(
        user_id: int,
        full_text: str,
        title: Optional[str] = None,
        pdf_url: Optional[str] = None,
        is_main: bool = False
    ) -> CandidateResume:
        """
        Upload CV from plain text (alternative to PDF).
        
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
            # Step 1: Preprocess (skip file reading, directly process text)
            logger.info("Preprocessing CV from text...")
            preprocessed_text = preprocess_resume(full_text)  # Can handle string input
            
            # Step 2: Parse
            logger.info("Parsing CV...")
            cv_data = parse_resume(preprocessed_text)
            
            if not cv_data.get("full_text"):
                cv_data["full_text"] = preprocessed_text
            
            # Step 3: Generate embeddings
            logger.info("Generating CV embeddings...")
            cv_embeddings = embed_cv(cv_data)
            
            # Step 4: Create MongoDB record
            last_cv = await CandidateResume.find().sort([("cv_id", -1)]).limit(1).to_list(1)
            cv_id = (last_cv[0].cv_id + 1) if last_cv else 1
            
            cv = CandidateResume(
                cv_id=cv_id,
                user_id=user_id,
                title=title or cv_data.get("job_title", "Untitled CV"),
                location=cv_data.get("location", ""),
                experience=cv_data.get("experience", ""),
                skills=cv_data.get("skills", []),
                summary=cv_data.get("summary", ""),
                full_text=cv_data.get("full_text", ""),
                pdf_url=pdf_url,
                is_main=is_main,
                embedding=None,
            )
            await cv.insert()
            logger.info(f"Created CV in MongoDB: cv_id={cv_id}")
            
            # Step 5: Store in ChromaDB
            chroma_id = f"cv_{cv_id}"
            cv_data_with_user = {**cv_data, "user_id": user_id, "cv_id": cv_id}
            
            vs.store_cv(chroma_id, cv_embeddings, cv_data_with_user)
            logger.info(f"Stored CV embeddings in ChromaDB: {chroma_id}")
            
            return cv
            
        except Exception as e:
            logger.error(f"Failed to upload CV from text: {e}", exc_info=True)
            raise
    
    # ============================
    # MATCHING Operations
    # ============================
    
    @staticmethod
    def find_matching_jobs(cv_id: int, top_k: int = 5) -> List[Dict]:
        """
        Find top-K matching jobs for a CV.
        
        Args:
            cv_id: CV ID
            top_k: Number of top matches to return
            
        Returns:
            List of matching jobs with scores and reasons
        """
        try:
            # Get CV from ChromaDB
            chroma_id = f"cv_{cv_id}"
            cv_result = vs.cv_full.get(ids=[chroma_id])
            
            if not cv_result or not cv_result.get("metadatas"):
                raise ValueError(f"CV {cv_id} not found in ChromaDB")
            
            cv_metadata = cv_result["metadatas"][0]
            
            # Prepare cv_json for matching
            cv_json = {
                "summary": cv_metadata.get("summary", ""),
                "experience": cv_metadata.get("experience", ""),
                "job_title": cv_metadata.get("job_title", ""),
                "skills": cv_metadata.get("skills", []),
                "location": cv_metadata.get("location", ""),
                "full_text": cv_metadata.get("full_text", ""),
            }
            
            # Find matches
            matches = get_top_k_jds_for_cv(cv_json, final_k=top_k)
            
            # Extract job_id from chroma_id (format: "jd_{job_id}")
            for match in matches:
                jd_chroma_id = match["id"]
                job_id = int(jd_chroma_id.replace("jd_", ""))
                match["job_id"] = job_id
            
            return matches
            
        except Exception as e:
            logger.error(f"Failed to find matching jobs for CV {cv_id}: {e}")
            return []
    
    @staticmethod
    def calculate_cv_jd_match(cv_id: int, job_id: int) -> Dict:
        """
        Calculate match score between a CV and a Job.
        
        Args:
            cv_id: CV ID
            job_id: Job ID
            
        Returns:
            Match result with scores
        """
        try:
            chroma_cv_id = f"cv_{cv_id}"
            chroma_jd_id = f"jd_{job_id}"
            
            result = match_jd_to_cv(chroma_jd_id, chroma_cv_id)
            
            # Add original IDs
            result["cv_id"] = cv_id
            result["job_id"] = job_id
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to calculate match: {e}")
            return {
                "cv_id": cv_id,
                "job_id": job_id,
                "scores": {},
                "final_score": 0.0,
                "error": str(e)
            }