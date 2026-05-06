# Backend HLD V2: Data and Storage Boundaries

## Storage Ownership

V2 run-only prototype dùng PostgreSQL cho:
- JD/CV prototype records
- vector embeddings qua pgvector

## Data Boundaries

- PostgreSQL: source of truth cho dữ liệu JD/CV prototype.
- pgvector: vector storage/scoring layer nằm trong PostgreSQL, không tách DB riêng.
- Matching results được trả trực tiếp từ run endpoint, không persist trong scope hiện tại.

## Core Tables (V2)

- `candidate_profiles_v2`
- `job_posts_v2`
- `candidate_embeddings_v2`
- `job_embeddings_v2`

## Match Result Contract

Không có persisted result table trong run-only prototype.

Nếu later phase cần lưu kết quả, schema `match_results_v2` phải được mở lại trong `docs/REQUIREMENTS.md` trước khi code.

## Vector and Index Contract

- Column type: `vector(<dim>)`
- Prototype không yêu cầu `hnsw` hoặc `ivfflat` index.
- Dùng exhaustive scoring trên seed/test dataset để dễ debug và kiểm chứng.
- Index strategy chỉ chốt ở later phase khi có benchmark.
