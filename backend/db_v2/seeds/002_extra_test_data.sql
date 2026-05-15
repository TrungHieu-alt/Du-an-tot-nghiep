-- Extra test data for manual matching-v2 scenario coverage.
-- Scenarios: hard-filter cert, education hierarchy, seniority, missing embeddings.
-- IDs: CV 1006-1010, JD 2006-2010.

-- ---------------------------------------------------------------------------
-- Candidate profiles
-- ---------------------------------------------------------------------------
INSERT INTO candidate_profiles_v2
    (cv_id, title, skills, summary, experience, location, job_type, seniority, education, certifications)
VALUES
    -- 1006: exact DevOps match for JD 2006 (remote, senior, cka required)
    (1006,
     'Senior DevOps Engineer',
     ARRAY['docker', 'kubernetes', 'aws', 'terraform'],
     'DevOps engineer specialising in container orchestration and cloud infra.',
     '5 years managing Kubernetes clusters and AWS infrastructure at scale.',
     'Hà Nội', 'remote', 'senior', 'bachelor',
     ARRAY['cka', 'aws_saa']),

    -- 1007: ML engineer, TP. Hồ Chí Minh — should match JD 2007 only
    (1007,
     'Mid ML Engineer',
     ARRAY['python', 'tensorflow', 'ml', 'pandas'],
     'Machine learning engineer building training pipelines and model serving.',
     '3 years developing ML models and building data pipelines at an AI startup.',
     'TP. Hồ Chí Minh', 'fulltime', 'mid', 'master',
     ARRAY[]::TEXT[]),

    -- 1008: Frontend Lead — perfect match for JD 2008; CV 1002 (junior) filtered by seniority
    (1008,
     'Frontend Lead',
     ARRAY['react', 'vue', 'typescript', 'nodejs'],
     'Frontend lead with deep React and Vue experience, mentoring junior devs.',
     '7 years building large-scale React/Vue apps, leading frontend squads.',
     'Hà Nội', 'fulltime', 'lead', 'bachelor',
     ARRAY[]::TEXT[]),

    -- 1009: Intern — only candidate that passes seniority for JD 2009
    (1009,
     'Intern Backend Developer',
     ARRAY['python', 'sql'],
     'Computer science student with Python and SQL project experience.',
     '6-month internship building CRUD APIs with Python and PostgreSQL.',
     'Hà Nội', 'fulltime', 'intern', 'high_school',
     ARRAY[]::TEXT[]),

    -- 1010: NO EMBEDDINGS — tests zero-semantic-score path for JD 2010
    (1010,
     'Mid Data Scientist',
     ARRAY['python', 'ml', 'statistics'],
     'Data scientist applying statistical methods and ML to business problems.',
     '3 years building predictive models and running A/B tests at an analytics firm.',
     'Đà Nẵng', 'parttime', 'mid', 'phd',
     ARRAY['google_ml']);

-- ---------------------------------------------------------------------------
-- Job posts
-- ---------------------------------------------------------------------------
INSERT INTO job_posts_v2
    (job_id, title, skills, requirement, location, job_type, seniority, education, required_certifications)
VALUES
    -- 2006: remote DevOps, requires CKA cert — matches CV 1006 and CV 1003
    (2006,
     'Senior DevOps Engineer',
     ARRAY['docker', 'kubernetes', 'aws', 'terraform'],
     'Own cloud infra on AWS and Kubernetes. 5+ years. CKA required.',
     'Hà Nội', 'remote', 'senior', 'bachelor',
     ARRAY['cka']),

    -- 2007: mid ML, TP. Hồ Chí Minh — only CV 1007 passes all hard filters
    (2007,
     'Mid ML Engineer',
     ARRAY['python', 'tensorflow', 'ml'],
     'Build and maintain ML training pipelines. 2-4 years experience.',
     'TP. Hồ Chí Minh', 'fulltime', 'mid', 'bachelor',
     ARRAY[]::TEXT[]),

    -- 2008: lead frontend, Hà Nội — CV 1008 matches; CV 1002 (junior) filtered by seniority
    (2008,
     'Frontend Lead',
     ARRAY['react', 'vue', 'typescript', 'nodejs'],
     'Lead the frontend guild. Define standards, mentor team. 6+ years.',
     'Hà Nội', 'fulltime', 'lead', 'bachelor',
     ARRAY[]::TEXT[]),

    -- 2009: intern backend, Hà Nội — only CV 1009 (intern) passes seniority filter
    (2009,
     'Intern Backend Developer',
     ARRAY['python', 'sql'],
     'Internship for CS students. Work on REST API development in Python.',
     'Hà Nội', 'fulltime', 'intern', 'high_school',
     ARRAY[]::TEXT[]),

    -- 2010: mid data scientist, Đà Nẵng, requires google_ml cert
    --   CV 1010 passes hard filter but has NO embeddings -> final_score ~ 0.14 (below 0.7 default)
    --   Tests: missing-embedding scoring + certification filter
    (2010,
     'Mid Data Scientist',
     ARRAY['python', 'ml', 'statistics'],
     'Apply statistical methods and ML models to product analytics problems.',
     'Đà Nẵng', 'parttime', 'mid', 'master',
     ARRAY['google_ml']);

-- ---------------------------------------------------------------------------
-- Candidate embeddings (1006-1009; 1010 intentionally omitted)
-- ---------------------------------------------------------------------------
INSERT INTO candidate_embeddings_v2
    (cv_id, emb_title, emb_skills, emb_summary, emb_experience)
VALUES
    (1006,
     array_fill(0.55::real, ARRAY[384])::vector,
     array_fill(0.56::real, ARRAY[384])::vector,
     array_fill(0.57::real, ARRAY[384])::vector,
     array_fill(0.58::real, ARRAY[384])::vector),
    (1007,
     array_fill(0.85::real, ARRAY[384])::vector,
     array_fill(0.86::real, ARRAY[384])::vector,
     array_fill(0.87::real, ARRAY[384])::vector,
     array_fill(0.88::real, ARRAY[384])::vector),
    (1008,
     array_fill(0.90::real, ARRAY[384])::vector,
     array_fill(0.91::real, ARRAY[384])::vector,
     array_fill(0.92::real, ARRAY[384])::vector,
     array_fill(0.93::real, ARRAY[384])::vector),
    (1009,
     array_fill(0.95::real, ARRAY[384])::vector,
     array_fill(0.96::real, ARRAY[384])::vector,
     array_fill(0.97::real, ARRAY[384])::vector,
     array_fill(0.98::real, ARRAY[384])::vector);
-- CV 1010: no row inserted -> missing-embedding path exercised

-- ---------------------------------------------------------------------------
-- Job embeddings (all 5 new JDs)
-- ---------------------------------------------------------------------------
INSERT INTO job_embeddings_v2
    (job_id, emb_title, emb_skills, emb_requirement)
VALUES
    (2006,
     array_fill(0.55::real, ARRAY[384])::vector,
     array_fill(0.56::real, ARRAY[384])::vector,
     array_fill(0.57::real, ARRAY[384])::vector),
    (2007,
     array_fill(0.85::real, ARRAY[384])::vector,
     array_fill(0.86::real, ARRAY[384])::vector,
     array_fill(0.87::real, ARRAY[384])::vector),
    (2008,
     array_fill(0.90::real, ARRAY[384])::vector,
     array_fill(0.91::real, ARRAY[384])::vector,
     array_fill(0.92::real, ARRAY[384])::vector),
    (2009,
     array_fill(0.95::real, ARRAY[384])::vector,
     array_fill(0.96::real, ARRAY[384])::vector,
     array_fill(0.97::real, ARRAY[384])::vector),
    (2010,
     array_fill(0.75::real, ARRAY[384])::vector,
     array_fill(0.76::real, ARRAY[384])::vector,
     array_fill(0.77::real, ARRAY[384])::vector);
