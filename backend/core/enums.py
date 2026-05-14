"""Canonical enum keys persisted by normal CV/Job records."""

from __future__ import annotations

SKILL_LEVELS = ("beginner", "intermediate", "advanced", "expert", "unknown")
SENIORITY_LEVELS = ("intern", "fresher", "junior", "middle", "senior", "lead", "manager", "director", "unknown")
EMPLOYMENT_TYPES = ("fulltime", "parttime", "contract", "internship", "freelance", "temporary", "unknown")
REMOTE_TYPES = ("onsite", "remote", "hybrid", "unknown")
EDUCATION_LEVELS = ("high_school", "vocational", "associate", "bachelor", "master", "phd", "certificate", "unknown")
LANGUAGE_LEVELS = ("basic", "conversational", "intermediate", "proficient", "fluent", "native", "unknown")
PRE_SCREEN_QUESTION_TYPES = ("text", "number", "single-choice", "multi-choice", "unknown")
CV_STATUSES = ("draft", "published", "archived", "unknown")
JOB_STATUSES = ("draft", "published", "closed", "unknown")
VISIBILITY_OPTIONS = ("public", "private", "unlisted", "unknown")
SKILL_CATEGORIES = (
    "technical",
    "professional",
    "soft_skill",
    "language",
    "tool",
    "domain_knowledge",
    "certification",
    "management",
    "unknown",
)
PORTFOLIO_MEDIA_TYPES = (
    "website",
    "github",
    "linkedin",
    "behance",
    "dribbble",
    "youtube",
    "document",
    "image",
    "video",
    "other",
    "unknown",
)
SALARY_PERIODS = ("hour", "day", "month", "year", "project", "unknown")
CURRENCIES = ("VND", "USD", "EUR", "JPY", "KRW", "unknown")

INDUSTRIES = (
    "information_technology",
    "accounting_finance",
    "sales",
    "marketing",
    "human_resources",
    "education",
    "healthcare",
    "engineering_construction",
    "design_creative",
    "customer_service",
    "operations",
    "logistics_supply_chain",
    "hospitality_tourism",
    "legal",
    "manufacturing",
    "retail",
    "other",
    "unknown",
)

OCCUPATION_GROUPS = (
    "software_engineering",
    "data_ai",
    "it_support",
    "cybersecurity",
    "devops_cloud",
    "accountant",
    "auditor",
    "financial_analyst",
    "tax_specialist",
    "sales_executive",
    "business_development",
    "account_manager",
    "digital_marketing",
    "content_marketing",
    "seo_sem",
    "brand_marketing",
    "hr_recruitment",
    "compensation_benefits",
    "training_development",
    "teacher",
    "lecturer",
    "academic_advisor",
    "doctor",
    "nurse",
    "pharmacist",
    "medical_technician",
    "civil_engineer",
    "mechanical_engineer",
    "electrical_engineer",
    "architect",
    "graphic_designer",
    "ui_ux_designer",
    "video_editor",
    "customer_support",
    "call_center_agent",
    "operations_staff",
    "operations_manager",
    "logistics_staff",
    "warehouse_staff",
    "supply_chain_planner",
    "hotel_staff",
    "tour_guide",
    "restaurant_staff",
    "legal_staff",
    "lawyer",
    "compliance_officer",
    "production_worker",
    "quality_control",
    "production_manager",
    "retail_staff",
    "store_manager",
    "other",
    "unknown",
)

