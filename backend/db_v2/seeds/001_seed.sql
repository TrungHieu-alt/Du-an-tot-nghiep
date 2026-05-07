-- Matching V2 Prototype (Run-Only) — deterministic seed data.
-- All embeddings are valid 384-dim vectors built via array_fill, so the file
-- stays readable and reproducible. Per REQUIREMENTS.md §9, missing embeddings
-- are allowed; this seed populates every embedding for sanity coverage.

-- ----------------------------------------------------------------------------
-- Candidate profiles
-- ----------------------------------------------------------------------------
INSERT INTO candidate_profiles_v2
    (cv_id, title, skills, summary, experience, location, job_type, seniority, education, certifications)
VALUES
    (1001,
     'Senior Backend Engineer',
     ARRAY['python', 'fastapi', 'postgres'],
     'Backend engineer with 6 years building REST APIs and data pipelines.',
     '6 years at fintech and e-commerce companies, owning Python services on PostgreSQL.',
     'ha_noi', 'fulltime', 'senior', 'dai_hoc',
     ARRAY['aws_saa']),
    (1002,
     'Junior Frontend Developer',
     ARRAY['react', 'typescript', 'vite'],
     'Frontend developer focused on React SPA work.',
     '1.5 years building React + TypeScript dashboards with Vite tooling.',
     'tp_hcm', 'fulltime', 'junior', 'dai_hoc',
     ARRAY[]::TEXT[]),
    (1003,
     'Senior Fullstack Engineer',
     ARRAY['python', 'react', 'postgres', 'docker'],
     'Fullstack engineer comfortable across Python services and React apps.',
     '5 years building Python backends and React frontends, deploying via Docker.',
     'ha_noi', 'remote', 'senior', 'thac_si',
     ARRAY['aws_saa', 'cka']),
    (1004,
     'Mid Backend Developer',
     ARRAY['java', 'spring', 'mysql'],
     'Java backend developer with Spring Boot focus.',
     '3 years writing Spring Boot services backed by MySQL.',
     'da_nang', 'parttime', 'mid', 'lop_12',
     ARRAY[]::TEXT[]),
    (1005,
     'Lead Data Engineer',
     ARRAY['python', 'sql', 'spark', 'ml'],
     'Data engineering lead with hands-on Spark and ML pipeline experience.',
     '8 years building large-scale data pipelines and leading data platform teams.',
     'ha_noi', 'fulltime', 'lead', 'tien_si',
     ARRAY['databricks_de']);

-- ----------------------------------------------------------------------------
-- Job posts
-- ----------------------------------------------------------------------------
INSERT INTO job_posts_v2
    (job_id, title, skills, requirement, location, job_type, seniority, education, required_certifications)
VALUES
    (2001,
     'Backend Engineer',
     ARRAY['python', 'fastapi'],
     'Build REST APIs in Python/FastAPI with PostgreSQL. 1-3 years experience.',
     'ha_noi', 'fulltime', 'junior', 'dai_hoc',
     ARRAY[]::TEXT[]),
    (2002,
     'Frontend Engineer',
     ARRAY['react', 'typescript'],
     'Build React + TypeScript SPAs. Familiar with modern Vite tooling.',
     'tp_hcm', 'fulltime', 'junior', 'dai_hoc',
     ARRAY[]::TEXT[]),
    (2003,
     'Senior Fullstack Engineer',
     ARRAY['python', 'react', 'postgres'],
     'Own Python services and React UIs end-to-end. 5+ years experience.',
     'ha_noi', 'remote', 'senior', 'dai_hoc',
     ARRAY[]::TEXT[]),
    (2004,
     'Lead Data Engineer',
     ARRAY['python', 'spark', 'sql'],
     'Lead a data platform team building Spark pipelines on PostgreSQL warehouse.',
     'ha_noi', 'fulltime', 'lead', 'thac_si',
     ARRAY['databricks_de']),
    (2005,
     'Java Backend Developer',
     ARRAY['java', 'spring'],
     'Maintain Spring Boot services. Part-time role at our Da Nang office.',
     'da_nang', 'parttime', 'mid', 'lop_12',
     ARRAY[]::TEXT[]);

-- ----------------------------------------------------------------------------
-- Candidate embeddings — deterministic 384-dim vectors via array_fill.
-- Each record uses a unique base value per field so vectors are distinct.
-- ----------------------------------------------------------------------------
INSERT INTO candidate_embeddings_v2
    (cv_id, emb_title, emb_skills, emb_summary, emb_experience)
VALUES
    (1001,
     array_fill(0.10::real, ARRAY[384])::vector,
     array_fill(0.11::real, ARRAY[384])::vector,
     array_fill(0.12::real, ARRAY[384])::vector,
     array_fill(0.13::real, ARRAY[384])::vector),
    (1002,
     array_fill(0.20::real, ARRAY[384])::vector,
     array_fill(0.21::real, ARRAY[384])::vector,
     array_fill(0.22::real, ARRAY[384])::vector,
     array_fill(0.23::real, ARRAY[384])::vector),
    (1003,
     array_fill(0.30::real, ARRAY[384])::vector,
     array_fill(0.31::real, ARRAY[384])::vector,
     array_fill(0.32::real, ARRAY[384])::vector,
     array_fill(0.33::real, ARRAY[384])::vector),
    (1004,
     array_fill(0.40::real, ARRAY[384])::vector,
     array_fill(0.41::real, ARRAY[384])::vector,
     array_fill(0.42::real, ARRAY[384])::vector,
     array_fill(0.43::real, ARRAY[384])::vector),
    (1005,
     array_fill(0.50::real, ARRAY[384])::vector,
     array_fill(0.51::real, ARRAY[384])::vector,
     array_fill(0.52::real, ARRAY[384])::vector,
     array_fill(0.53::real, ARRAY[384])::vector);

-- ----------------------------------------------------------------------------
-- Job embeddings
-- ----------------------------------------------------------------------------
INSERT INTO job_embeddings_v2
    (job_id, emb_title, emb_skills, emb_requirement)
VALUES
    (2001,
     array_fill(0.60::real, ARRAY[384])::vector,
     array_fill(0.61::real, ARRAY[384])::vector,
     array_fill(0.62::real, ARRAY[384])::vector),
    (2002,
     array_fill(0.65::real, ARRAY[384])::vector,
     array_fill(0.66::real, ARRAY[384])::vector,
     array_fill(0.67::real, ARRAY[384])::vector),
    (2003,
     array_fill(0.70::real, ARRAY[384])::vector,
     array_fill(0.71::real, ARRAY[384])::vector,
     array_fill(0.72::real, ARRAY[384])::vector),
    (2004,
     array_fill(0.75::real, ARRAY[384])::vector,
     array_fill(0.76::real, ARRAY[384])::vector,
     array_fill(0.77::real, ARRAY[384])::vector),
    (2005,
     array_fill(0.80::real, ARRAY[384])::vector,
     array_fill(0.81::real, ARRAY[384])::vector,
     array_fill(0.82::real, ARRAY[384])::vector);
