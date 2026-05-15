-- Remove deprecated normal Job/CV embedding and translation metadata.
-- V2 prototype embedding tables remain unchanged.

DROP INDEX IF EXISTS jobs_embedding_gin_idx;
DROP INDEX IF EXISTS cvs_embedding_gin_idx;

ALTER TABLE jobs DROP COLUMN IF EXISTS embedding;
ALTER TABLE jobs DROP COLUMN IF EXISTS embedding_text;
ALTER TABLE jobs DROP COLUMN IF EXISTS embedding_vector;
ALTER TABLE jobs DROP COLUMN IF EXISTS translated;
ALTER TABLE jobs DROP COLUMN IF EXISTS translated_text;
ALTER TABLE jobs DROP COLUMN IF EXISTS translation_warnings;
ALTER TABLE jobs DROP COLUMN IF EXISTS source_language;
ALTER TABLE jobs DROP COLUMN IF EXISTS target_language;
ALTER TABLE jobs DROP COLUMN IF EXISTS language_detected;

ALTER TABLE cvs DROP COLUMN IF EXISTS embedding;
ALTER TABLE cvs DROP COLUMN IF EXISTS embedding_text;
ALTER TABLE cvs DROP COLUMN IF EXISTS embedding_vector;
ALTER TABLE cvs DROP COLUMN IF EXISTS translated;
ALTER TABLE cvs DROP COLUMN IF EXISTS translated_text;
ALTER TABLE cvs DROP COLUMN IF EXISTS translation_warnings;
ALTER TABLE cvs DROP COLUMN IF EXISTS source_language;
ALTER TABLE cvs DROP COLUMN IF EXISTS target_language;
ALTER TABLE cvs DROP COLUMN IF EXISTS language_detected;

UPDATE jobs
SET recruiter = recruiter
    - 'translated'
    - 'translatedText'
    - 'translationWarnings'
    - 'translation_warnings'
    - 'translation'
    - 'sourceLanguage'
    - 'source_language'
    - 'targetLanguage'
    - 'target_language'
    - 'languageDetected'
    - 'language_detected'
WHERE recruiter IS NOT NULL;

UPDATE cvs
SET file = file
    - 'translated'
    - 'translatedText'
    - 'translationWarnings'
    - 'translation_warnings'
    - 'translation'
    - 'sourceLanguage'
    - 'source_language'
    - 'targetLanguage'
    - 'target_language'
    - 'languageDetected'
    - 'language_detected'
WHERE file IS NOT NULL;
