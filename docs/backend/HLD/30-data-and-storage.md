# Backend HLD V2: Data and Storage Boundaries

## Storage Ownership

V2 dùng PostgreSQL làm storage thống nhất:
- business entities
- matching records
- vector embeddings qua pgvector

## Data Boundaries

- PostgreSQL: source of truth cho dữ liệu nghiệp vụ + kết quả matching.
- pgvector: retrieval/index layer nằm trong PostgreSQL, không tách DB riêng.

## Core Tables (V2)

- `candidate_profiles_v2`
- `job_posts_v2`
- `candidate_embeddings_v2`
- `job_embeddings_v2`
- `match_results_v2`

## Match Result Contract

`match_results_v2` lưu:
- ids: `cv_id`, `job_id`
- `final_score`
- breakdown: `title_score`, `skills_score`, `req_exp_score`, `req_summary_score`
- adjustment: `exact_skill_bonus`, `required_penalty`
- versioning: `feature_version`, `embedding_model_version`, `scoring_version`
- audit timestamps

## Vector and Index Contract

- Column type: `vector(<dim>)`
- Index strategy: benchmark-driven (`hnsw` hoặc `ivfflat`)
- ANN query dùng embedding anchor của entity khởi chạy matching.
