import logging
from typing import Optional, List, Dict
from models.jobPost import JobPost
from datetime import datetime

# RAG imports
from ragmodel.dataPreprocess.jobPreprocess import preprocess_jd
from ragmodel.dataPreprocess.jobParser import parse_jd
from ragmodel.logics.embedder import embed_jd
import ragmodel.db.vectorStore as vs
from ragmodel.logics.matchingLogic import get_top_k_cvs_for_jd, match_jd_to_cv

logger = logging.getLogger(__name__)

class JobRepository:
    
    # ============================
    # CRUD Operations
    # ============================
    
    @staticmethod
    async def create(
        recruiter_id: int,
        title: str,
        role: str,
        location: str,
        job_type: str,
        experience_level: str,
        skills: List[str],
        salary_min: Optional[float],
        salary_max: Optional[float],
        full_text: Optional[str],
        pdf_url: Optional[str]
    ) -> JobPost:
        """Create Job without embedding (basic CRUD)"""
        last_job = await JobPost.find().sort([("job_id", -1)]).limit(1).to_list(1)
        job_id = (last_job[0].job_id + 1) if last_job else 1
        
        job = JobPost(
            job_id=job_id,
            recruiter_id=recruiter_id,
            title=title,
            role=role,
            location=location,
            job_type=job_type,
            experience_level=experience_level,
            skills=skills,
            salary_min=salary_min,
            salary_max=salary_max,
            full_text=full_text,
            pdf_url=pdf_url,
        )
        await job.insert()
        return job
    
    @staticmethod
    async def get_by_id(job_id: int) -> Optional[JobPost]:
        return await JobPost.find_one(JobPost.job_id == job_id)
    
    @staticmethod
    async def get_by_recruiter(recruiter_id: int) -> List[JobPost]:
        return await JobPost.find(JobPost.recruiter_id == recruiter_id).to_list(None)
    
    @staticmethod
    async def get_all() -> List[JobPost]:
        return await JobPost.find().to_list(None)
    
    @staticmethod
    async def update(job_id: int, **kwargs) -> Optional[JobPost]:
        job = await JobPost.find_one(JobPost.job_id == job_id)
        if job:
            kwargs["updated_at"] = datetime.utcnow()
            await job.update({"$set": kwargs})
            return await JobRepository.get_by_id(job_id)
        return None
    
    @staticmethod
    async def delete(job_id: int) -> bool:
        job = await JobPost.find_one(JobPost.job_id == job_id)
        if job:
            # Delete from ChromaDB
            try:
                vs.delete_jd(f"jd_{job_id}")
                logger.info(f"Deleted Job embeddings from ChromaDB: jd_{job_id}")
            except Exception as e:
                logger.warning(f"Failed to delete Job embeddings: {e}")
            
            # Delete from MongoDB
            await job.delete()
            return True
        return False
    
    # ============================
    # UPLOAD JOB (Text → Parse → Embed → Store)
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
        Upload Job from full text.
        
        Flow:
        1. Preprocess text (translate, clean, split)
        2. Parse to structured JSON
        3. Generate embeddings
        4. Store in ChromaDB
        5. Store in MongoDB
        
        Args:
            recruiter_id: Recruiter ID
            full_text: Full job description text
            title: Optional job title (if not provided, will be parsed)
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
            # Step 1: Preprocess
            logger.info("Preprocessing Job text...")
            preprocessed_text = preprocess_jd(full_text)
            
            # Step 2: Parse
            logger.info("Parsing Job...")
            jd_data = parse_jd(preprocessed_text)
            
            # Validate required fields
            if not jd_data.get("full_text"):
                jd_data["full_text"] = preprocessed_text
            
            # Step 3: Generate embeddings
            logger.info("Generating Job embeddings...")
            jd_embeddings = embed_jd(jd_data)
            
            # Step 4: Create MongoDB record first (to get job_id)
            last_job = await JobPost.find().sort([("job_id", -1)]).limit(1).to_list(1)
            job_id = (last_job[0].job_id + 1) if last_job else 1
            
            # Merge parsed data with provided data (provided data takes priority)
            job = JobPost(
                job_id=job_id,
                recruiter_id=recruiter_id,
                title=title or jd_data.get("job_title", "Untitled Job"),
                role=role or jd_data.get("job_title", ""),
                location=location or jd_data.get("location", ""),
                job_type=job_type or "Full-time",  # Default
                experience_level=experience_level or "Mid-level",  # Default
                skills=jd_data.get("skills", []),
                salary_min=salary_min,
                salary_max=salary_max,
                full_text=jd_data.get("full_text", ""),
                pdf_url=pdf_url,
                embedding=None,  # We store in ChromaDB, not here
            )
            await job.insert()
            logger.info(f"Created Job in MongoDB: job_id={job_id}")
            
            # Step 5: Store embeddings in ChromaDB with recruiter_id in metadata
            chroma_id = f"jd_{job_id}"
            
            # Add recruiter_id and job_id to metadata
            jd_data_with_meta = {
                **jd_data, 
                "recruiter_id": recruiter_id, 
                "job_id": job_id,
                "title": job.title,
                "role": job.role,
                "job_type": job.job_type,
                "experience_level": job.experience_level,
            }
            
            vs.store_jd(chroma_id, jd_embeddings, jd_data_with_meta)
            logger.info(f"Stored Job embeddings in ChromaDB: {chroma_id}")
            
            return job
            
        except Exception as e:
            logger.error(f"Failed to upload Job: {e}", exc_info=True)
            raise
    
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
        Upload Job from PDF file (alternative method).
        
        Args:
            recruiter_id: Recruiter ID
            pdf_path: Path to PDF file
            Other args: Same as upload_job_from_text
            
        Returns:
            JobPost object
        """
        try:
            # Step 1: Preprocess (read PDF)
            logger.info(f"Preprocessing Job from PDF: {pdf_path}")
            preprocessed_text = preprocess_jd(pdf_path)  # Can handle file path
            
            # Step 2: Parse
            logger.info("Parsing Job...")
            jd_data = parse_jd(preprocessed_text)
            
            if not jd_data.get("full_text"):
                jd_data["full_text"] = preprocessed_text
            
            # Step 3: Generate embeddings
            logger.info("Generating Job embeddings...")
            jd_embeddings = embed_jd(jd_data)
            
            # Step 4: Create MongoDB record
            last_job = await JobPost.find().sort([("job_id", -1)]).limit(1).to_list(1)
            job_id = (last_job[0].job_id + 1) if last_job else 1
            
            job = JobPost(
                job_id=job_id,
                recruiter_id=recruiter_id,
                title=title or jd_data.get("job_title", "Untitled Job"),
                role=role or jd_data.get("job_title", ""),
                location=location or jd_data.get("location", ""),
                job_type=job_type or "Full-time",
                experience_level=experience_level or "Mid-level",
                skills=jd_data.get("skills", []),
                salary_min=salary_min,
                salary_max=salary_max,
                full_text=jd_data.get("full_text", ""),
                pdf_url=pdf_url,
                embedding=None,
            )
            await job.insert()
            logger.info(f"Created Job in MongoDB: job_id={job_id}")
            
            # Step 5: Store in ChromaDB
            chroma_id = f"jd_{job_id}"
            jd_data_with_meta = {
                **jd_data,
                "recruiter_id": recruiter_id,
                "job_id": job_id,
                "title": job.title,
                "role": job.role,
                "job_type": job.job_type,
                "experience_level": job.experience_level,
            }
            
            vs.store_jd(chroma_id, jd_embeddings, jd_data_with_meta)
            logger.info(f"Stored Job embeddings in ChromaDB: {chroma_id}")
            
            return job
            
        except Exception as e:
            logger.error(f"Failed to upload Job from PDF: {e}", exc_info=True)
            raise
    
    # ============================
    # MATCHING Operations
    # ============================
    
    @staticmethod
    def find_matching_cvs(job_id: int, top_k: int = 5) -> List[Dict]:
        """
        Find top-K matching CVs for a Job.
        
        Args:
            job_id: Job ID
            top_k: Number of top matches to return
            
        Returns:
            List of matching CVs with scores and reasons
        """
        try:
            # Get Job from ChromaDB
            chroma_id = f"jd_{job_id}"
            jd_result = vs.jd_full.get(ids=[chroma_id])
            
            if not jd_result or not jd_result.get("metadatas"):
                raise ValueError(f"Job {job_id} not found in ChromaDB")
            
            jd_metadata = jd_result["metadatas"][0]
            
            # Prepare jd_json for matching
            jd_json = {
                "job_description": jd_metadata.get("job_description", ""),
                "job_requirement": jd_metadata.get("job_requirement", ""),
                "job_title": jd_metadata.get("job_title", ""),
                "skills": jd_metadata.get("skills", []),
                "location": jd_metadata.get("location", ""),
                "full_text": jd_metadata.get("full_text", ""),
            }
            
            # Find matches
            matches = get_top_k_cvs_for_jd(jd_json, final_k=top_k)
            
            # Extract cv_id and user_id from metadata
            for match in matches:
                cv_chroma_id = match["id"]
                cv_id = int(cv_chroma_id.replace("cv_", ""))
                user_id = match["cv"].get("user_id")
                
                match["cv_id"] = cv_id
                match["user_id"] = user_id
            
            return matches
            
        except Exception as e:
            logger.error(f"Failed to find matching CVs for Job {job_id}: {e}")
            return []
    
    @staticmethod
    def calculate_jd_cv_match(job_id: int, cv_id: int) -> Dict:
        """
        Calculate match score between a Job and a CV.
        
        Args:
            job_id: Job ID
            cv_id: CV ID
            
        Returns:
            Match result with scores
        """
        try:
            chroma_jd_id = f"jd_{job_id}"
            chroma_cv_id = f"cv_{cv_id}"
            
            result = match_jd_to_cv(chroma_jd_id, chroma_cv_id)
            
            # Add original IDs
            result["job_id"] = job_id
            result["cv_id"] = cv_id
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to calculate match: {e}")
            return {
                "job_id": job_id,
                "cv_id": cv_id,
                "scores": {},
                "final_score": 0.0,
                "error": str(e)
            }