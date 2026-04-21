import asyncio
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from models.user import User
from models.candidateProfile import CandidateProfile
from models.recruiterProfile import RecruiterProfile
from models.candidateResume import CandidateResume
from models.jobPost import JobPost
import random
import string

MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "job_matching"

# Diverse data generators
WORK_FIELDS = [
    "Software Development", "Data Science", "Machine Learning", "Web Development",
    "Mobile Development", "DevOps", "Cybersecurity", "Cloud Computing",
    "Marketing", "Digital Marketing", "Content Marketing", "SEO/SEM",
    "Finance", "Investment Banking", "Financial Analysis", "Accounting",
    "Healthcare", "Nursing", "Medical Research", "Pharmacy",
    "Education", "Teaching", "Educational Technology", "Training",
    "Engineering", "Mechanical Engineering", "Electrical Engineering", "Civil Engineering",
    "Sales", "Business Development", "Customer Success", "Account Management",
    "Human Resources", "Talent Acquisition", "Employee Relations", "HR Analytics",
    "Design", "UX/UI Design", "Graphic Design", "Product Design",
    "Operations", "Supply Chain", "Logistics", "Project Management",
    "Legal", "Corporate Law", "Intellectual Property", "Compliance",
    "Consulting", "Management Consulting", "IT Consulting", "Strategy"
]

LOCATIONS = [
    "New York, NY", "San Francisco, CA", "Austin, TX", "Seattle, WA", "Boston, MA",
    "London, UK", "Berlin, Germany", "Paris, France", "Amsterdam, Netherlands",
    "Toronto, Canada", "Sydney, Australia", "Singapore", "Tokyo, Japan",
    "Mumbai, India", "Bangalore, India", "Shanghai, China", "Remote", "Hybrid"
]

EXPERIENCE_LEVELS = ["Entry Level", "Mid Level", "Senior Level", "Lead/Principal", "Executive"]

JOB_TYPES = ["Full-time", "Part-time", "Contract", "Freelance", "Internship"]

SKILLS_BY_FIELD = {
    "Software Development": ["Python", "Java", "JavaScript", "C++", "Go", "Rust", "React", "Angular", "Vue.js", "Node.js", "Django", "Flask", "Spring Boot", "Microservices", "API Development", "Git", "Docker", "Kubernetes"],
    "Data Science": ["Python", "R", "SQL", "Pandas", "NumPy", "Scikit-learn", "TensorFlow", "PyTorch", "Jupyter", "Tableau", "Power BI", "Statistics", "Machine Learning", "Deep Learning", "Data Visualization"],
    "Machine Learning": ["Python", "TensorFlow", "PyTorch", "Scikit-learn", "Keras", "Computer Vision", "NLP", "Reinforcement Learning", "MLOps", "AutoML", "Feature Engineering", "Model Deployment"],
    "Web Development": ["HTML", "CSS", "JavaScript", "TypeScript", "React", "Angular", "Vue.js", "Node.js", "Express.js", "Next.js", "PHP", "Laravel", "Ruby on Rails", "Django", "Flask"],
    "Mobile Development": ["React Native", "Flutter", "Swift", "Kotlin", "Java", "iOS Development", "Android Development", "Xamarin", "Ionic", "Cordova", "Mobile UI/UX"],
    "DevOps": ["Docker", "Kubernetes", "Jenkins", "GitLab CI", "AWS", "Azure", "GCP", "Terraform", "Ansible", "Linux", "Bash", "Monitoring", "CI/CD", "Infrastructure as Code"],
    "Cybersecurity": ["Network Security", "Ethical Hacking", "Cryptography", "SIEM", "Firewalls", "Penetration Testing", "Risk Assessment", "Compliance", "Incident Response", "Security Auditing"],
    "Cloud Computing": ["AWS", "Azure", "GCP", "Cloud Architecture", "Serverless", "Microservices", "Docker", "Kubernetes", "Cloud Security", "Cost Optimization", "Multi-cloud"],
    "Marketing": ["Digital Marketing", "Content Marketing", "Social Media", "SEO", "SEM", "Email Marketing", "Marketing Analytics", "Brand Management", "Campaign Management", "CRM"],
    "Finance": ["Financial Analysis", "Excel", "Financial Modeling", "Bloomberg", "Risk Management", "Portfolio Management", "Investment Banking", "Corporate Finance", "Accounting", "Auditing"],
    "Healthcare": ["Patient Care", "Medical Records", "HIPAA", "Clinical Research", "Healthcare Administration", "Nursing", "Medical Technology", "Health Informatics", "Telemedicine"],
    "Engineering": ["CAD", "SolidWorks", "AutoCAD", "MATLAB", "Project Management", "Quality Control", "Process Engineering", "Systems Engineering", "R&D"],
    "Sales": ["CRM", "Lead Generation", "Negotiation", "Customer Relationship", "Salesforce", "Cold Calling", "B2B Sales", "B2C Sales", "Account Management", "Sales Analytics"],
    "Design": ["Adobe Creative Suite", "Figma", "Sketch", "InVision", "User Research", "Wireframing", "Prototyping", "Visual Design", "Interaction Design", "Design Systems"]
}

COMPANY_NAMES = [
    "TechCorp", "DataSys", "InnovateLabs", "GlobalTech", "NextGen Solutions",
    "FutureWorks", "SmartTech", "CloudNine", "DigitalFirst", "AgileCorp",
    "MediHealth", "EduLearn", "FinancePlus", "MarketMasters", "BuildRight",
    "SellSmart", "DesignHub", "ConsultPro", "LegalAid", "OpsOptimize"
]

def generate_email(name):
    """Generate a simple email from name"""
    return f"{name.lower().replace(' ', '.')}@example.com"

def generate_password():
    """Generate a simple password hash (in real app, use proper hashing)"""
    return "hashed_password_" + ''.join(random.choices(string.ascii_letters + string.digits, k=8))

def get_random_skills(field, count=5):
    """Get random skills for a field"""
    if field in SKILLS_BY_FIELD:
        skills = SKILLS_BY_FIELD[field]
        return random.sample(skills, min(count, len(skills)))
    return ["General Skills"]

def generate_experience_text(level, field):
    """Generate experience description"""
    years = {
        "Entry Level": "0-2 years",
        "Mid Level": "3-5 years",
        "Senior Level": "6-10 years",
        "Lead/Principal": "10-15 years",
        "Executive": "15+ years"
    }
    return f"{years[level]} of experience in {field}"

def generate_summary(name, field, level):
    """Generate a professional summary"""
    return f"Experienced {level.lower()} professional in {field} with a passion for innovation and delivering high-quality results."

def generate_job_title(field, level):
    """Generate job title based on field and level"""
    titles = {
        "Entry Level": ["Junior", "Associate", "Entry-level"],
        "Mid Level": ["", "Senior"],
        "Senior Level": ["Senior", "Lead"],
        "Lead/Principal": ["Principal", "Lead", "Staff"],
        "Executive": ["Director", "VP", "Chief", "Head"]
    }
    prefix = random.choice(titles[level])
    return f"{prefix} {field} Specialist" if prefix else f"{field} Specialist"

async def populate_database():
    """Populate database with diverse sample data"""
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]

    await init_beanie(
        database=db,
        document_models=[
            User, CandidateProfile, RecruiterProfile, JobPost, CandidateResume
        ],
    )

    print("Starting database population...")

    # Clear existing data
    await User.delete_all()
    await CandidateProfile.delete_all()
    await RecruiterProfile.delete_all()
    await JobPost.delete_all()
    await CandidateResume.delete_all()
    print("Cleared existing data")

    # Create recruiters (50)
    recruiters = []
    recruiter_profiles = []
    for i in range(1, 51):
        user = User(
            user_id=i,
            email=generate_email(f"recruiter{i}"),
            password_hash=generate_password(),
            role="recruiter"
        )
        await user.insert()
        recruiters.append(user)

        profile = RecruiterProfile(
            user_id=i,
            company_name=random.choice(COMPANY_NAMES) + f" {i}",
            recruiter_title=f"Recruitment Manager {i}",
            company_logo=None,
            about_company=f"A leading company in various industries specializing in innovative solutions.",
            hiring_fields=random.sample(WORK_FIELDS, random.randint(2, 5))
        )
        await profile.insert()
        recruiter_profiles.append(profile)

    print(f"Created {len(recruiters)} recruiters")

    # Create candidates (100)
    candidates = []
    candidate_profiles = []
    resumes = []
    for i in range(51, 151):
        user = User(
            user_id=i,
            email=generate_email(f"candidate{i}"),
            password_hash=generate_password(),
            role="candidate"
        )
        await user.insert()
        candidates.append(user)

        field = random.choice(WORK_FIELDS)
        level = random.choice(EXPERIENCE_LEVELS)
        exp_years = {
            "Entry Level": random.randint(0, 2),
            "Mid Level": random.randint(3, 5),
            "Senior Level": random.randint(6, 10),
            "Lead/Principal": random.randint(10, 15),
            "Executive": random.randint(15, 25)
        }[level]

        profile = CandidateProfile(
            user_id=i,
            full_name=f"John Doe {i}",
            location=random.choice(LOCATIONS),
            experience_years=exp_years,
            skills=get_random_skills(field, random.randint(3, 8)),
            summary=generate_summary(f"John Doe {i}", field, level)
        )
        await profile.insert()
        candidate_profiles.append(profile)

        # Create resume
        resume = CandidateResume(
            cv_id=i - 50,  # Start from 1
            user_id=i,
            title=f"{field} Professional",
            location=profile.location,
            experience=generate_experience_text(level, field),
            skills=profile.skills,
            summary=profile.summary,
            full_text=f"Professional with {profile.experience_years} years in {field}. Skills include {', '.join(profile.skills)}. {profile.summary}",
            embedding=None,
            is_main=True
        )
        await resume.insert()
        resumes.append(resume)

    print(f"Created {len(candidates)} candidates with profiles and resumes")

    # Create job posts (100)
    job_posts = []
    for i in range(1, 101):
        recruiter = random.choice(recruiters)
        field = random.choice(WORK_FIELDS)
        level = random.choice(EXPERIENCE_LEVELS)
        min_salary = {
            "Entry Level": random.randint(40000, 60000),
            "Mid Level": random.randint(60000, 90000),
            "Senior Level": random.randint(90000, 130000),
            "Lead/Principal": random.randint(130000, 180000),
            "Executive": random.randint(180000, 250000)
        }[level]
        max_salary = min_salary + random.randint(10000, 30000)

        job = JobPost(
            job_id=i,
            recruiter_id=recruiter.user_id,
            title=generate_job_title(field, level),
            role=f"{field} Role",
            location=random.choice(LOCATIONS),
            job_type=random.choice(JOB_TYPES),
            experience_level=level,
            skills=get_random_skills(field, random.randint(4, 10)),
            salary_min=min_salary,
            salary_max=max_salary,
            full_text=f"We are looking for an experienced {level.lower()} {field} professional to join our team. Requirements: {', '.join(get_random_skills(field, 5))}. Competitive salary and benefits package.",
            embedding=None
        )
        await job.insert()
        job_posts.append(job)

    print(f"Created {len(job_posts)} job posts")

    print("Database population completed successfully!")
    print(f"Total: {len(recruiters)} recruiters, {len(candidates)} candidates, {len(resumes)} resumes, {len(job_posts)} job posts")

if __name__ == "__main__":
    asyncio.run(populate_database())