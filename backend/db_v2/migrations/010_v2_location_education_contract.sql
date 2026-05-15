-- Migrate the V2 location/education contract only.
-- Scope: candidate_profiles_v2.location, candidate_profiles_v2.education,
--        job_posts_v2.location, job_posts_v2.education.
-- Normal cvs/jobs tables and V2 embedding tables are intentionally untouched.

ALTER TABLE candidate_profiles_v2
    DROP CONSTRAINT IF EXISTS candidate_profiles_v2_location_chk;
ALTER TABLE candidate_profiles_v2
    DROP CONSTRAINT IF EXISTS candidate_profiles_v2_education_chk;
ALTER TABLE job_posts_v2
    DROP CONSTRAINT IF EXISTS job_posts_v2_location_chk;
ALTER TABLE job_posts_v2
    DROP CONSTRAINT IF EXISTS job_posts_v2_education_chk;

UPDATE candidate_profiles_v2
SET location = CASE location
    WHEN 'ha_noi' THEN 'Hà Nội'
    WHEN 'tp_hcm' THEN 'TP. Hồ Chí Minh'
    WHEN 'da_nang' THEN 'Đà Nẵng'
    ELSE location
END
WHERE location IN ('ha_noi', 'tp_hcm', 'da_nang');

UPDATE job_posts_v2
SET location = CASE location
    WHEN 'ha_noi' THEN 'Hà Nội'
    WHEN 'tp_hcm' THEN 'TP. Hồ Chí Minh'
    WHEN 'da_nang' THEN 'Đà Nẵng'
    ELSE location
END
WHERE location IN ('ha_noi', 'tp_hcm', 'da_nang');

UPDATE candidate_profiles_v2
SET education = CASE education
    WHEN 'dai_hoc' THEN 'bachelor'
    WHEN 'thac_si' THEN 'master'
    WHEN 'tien_si' THEN 'phd'
    WHEN 'lop_12' THEN 'high_school'
    WHEN 'lop_9' THEN 'high_school'
    ELSE education
END
WHERE education IN ('dai_hoc', 'thac_si', 'tien_si', 'lop_12', 'lop_9');

UPDATE job_posts_v2
SET education = CASE education
    WHEN 'dai_hoc' THEN 'bachelor'
    WHEN 'thac_si' THEN 'master'
    WHEN 'tien_si' THEN 'phd'
    WHEN 'lop_12' THEN 'high_school'
    WHEN 'lop_9' THEN 'high_school'
    ELSE education
END
WHERE education IN ('dai_hoc', 'thac_si', 'tien_si', 'lop_12', 'lop_9');

ALTER TABLE candidate_profiles_v2
    ADD CONSTRAINT candidate_profiles_v2_location_chk
    CHECK (location IN ('Hà Nội', 'TP. Hồ Chí Minh', 'Đà Nẵng'));
ALTER TABLE candidate_profiles_v2
    ADD CONSTRAINT candidate_profiles_v2_education_chk
    CHECK (education IN ('high_school', 'bachelor', 'master', 'phd'));

ALTER TABLE job_posts_v2
    ADD CONSTRAINT job_posts_v2_location_chk
    CHECK (location IN ('Hà Nội', 'TP. Hồ Chí Minh', 'Đà Nẵng'));
ALTER TABLE job_posts_v2
    ADD CONSTRAINT job_posts_v2_education_chk
    CHECK (education IN ('high_school', 'bachelor', 'master', 'phd'));
