# Backend HLD V2: Data and Storage Boundaries

## Storage Ownership

V2 run-only prototype dùng PostgreSQL cho:
- JD/CV prototype records
- vector embeddings qua pgvector
- auth users for the additive login/register surface
- normal Job/CV rows for public search and owner-managed CRUD

## Data Boundaries

- PostgreSQL: source of truth cho dữ liệu JD/CV prototype.
- pgvector: vector storage/scoring layer nằm trong PostgreSQL, không tách DB riêng.
- Embedding generation uses local
  `sentence-transformers/all-MiniLM-L6-v2` only; PostgreSQL stores the resulting
  384-dimensional vectors.
- Matching results được trả trực tiếp từ run endpoint, không persist trong scope hiện tại.
- Normal Job/CV data is stored only in PostgreSQL tables `jobs` and `cvs`.
  Ownership is held on child rows through `created_by -> users.id`.
  PDF CV uploads store file metadata in `cvs.file` JSONB.

## Core Tables (V2)

Matching-owned tables:

- `candidate_profiles_v2`
- `job_posts_v2`
- `candidate_embeddings_v2`
- `job_embeddings_v2`

Auth-owned table:

- `users`

Normal Job/CV tables:

- `jobs`
- `cvs`

## Match Result Contract

Không có persisted result table trong run-only prototype.

Nếu later phase cần lưu kết quả, schema `match_results_v2` phải được mở lại trong `docs/REQUIREMENTS.md` trước khi code.

## Vector and Index Contract

- Column type: `vector(<dim>)`
- Current dimension: `384`, matching local
  `sentence-transformers/all-MiniLM-L6-v2`.
- Prototype không yêu cầu `hnsw` hoặc `ivfflat` index.
- Dùng exhaustive scoring trên seed/test dataset để dễ debug và kiểm chứng.
- Index strategy chỉ chốt ở later phase khi có benchmark.
