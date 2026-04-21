import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from models.candidateResume import CandidateResume
from models.jobPost import JobPost
from repositories.cv_repo import CVRepository
from repositories.job_repo import JobRepository

# ✅ Thêm hàm init
async def init_db():
    """Initialize Beanie with MongoDB"""
    # Kết nối MongoDB
    client = AsyncIOMotorClient("mongodb://localhost:27017")  # ← Thay URL của bạn
    database = client.job_matching  # ← Thay database name
    
    # Initialize Beanie với models
    await init_beanie(
        database=database,
        document_models=[
            CandidateResume,
            JobPost,
        ]
    )
    print("✅ Database initialized")

async def test_cv_upload_text():
    """Test CV upload from text"""
    print("\n" + "=" * 60)
    print("TEST 2: Upload CV from Text")
    print("=" * 60)
    
    cv_text = """
    John Doe
    Software Engineer
    Location: Hanoi, Vietnam
    
    Summary:
    Experienced Software Engineer with 5+ years in Python, Django, and React.
    
    Experience:
    - Senior Developer at TechCorp (2020-2023)
    - Full-stack development with Python/Django backend and React frontend
    
    Skills: Python, Django, React, PostgreSQL, Docker, AWS
    """
    
    cv = await CVRepository.upload_cv_from_text(
        user_id=124,
        full_text=cv_text,
        title="John Doe - Software Engineer",
        is_main=True
    )
    
    print(f"✅ Uploaded CV:")
    print(f"   CV ID: {cv.cv_id}")
    print(f"   Title: {cv.title}")
    print(f"   Skills: {cv.skills}")
    
    return cv.cv_id

async def main():
    """Run all tests"""
    try:
        # ✅ QUAN TRỌNG: Init database trước
        await init_db()
        
        # Test CV upload
        cv_id = await test_cv_upload_text()
        
        # ... rest of tests
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())