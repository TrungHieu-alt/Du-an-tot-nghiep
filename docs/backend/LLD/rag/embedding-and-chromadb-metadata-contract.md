# LLD V2: Embedding and pgvector Contract

## Scope

Tài liệu này thay thế contract Chroma cũ cho prototype v2 dùng PostgreSQL + pgvector.

## Embedding Contract

- Mỗi field semantic có một vector riêng.
- Mỗi record embedding có version metadata:
  - `embedding_model_version`
  - `feature_version`

## CV Embedding Fields

- `emb_title`
- `emb_skills`
- `emb_summary`
- `emb_experience`
- `emb_full` (lưu cho mục đích mở rộng, không dùng scoring MVP)

## JD Embedding Fields

- `emb_title`
- `emb_skills`
- `emb_requirement`
- `emb_full` (lưu cho mục đích mở rộng, không dùng scoring MVP)

## Storage Contract

Gợi ý tách bảng:
- `candidate_embeddings_v2`
- `job_embeddings_v2`

Mỗi bảng lưu:
- khóa business (`cv_id` hoặc `job_id`)
- vector columns
- model/version metadata
- timestamps

## Index Contract

- Dùng pgvector index theo benchmark (`hnsw` hoặc `ivfflat`).
- ANN query dùng vector anchor tương ứng theo mode JD->CV hoặc CV->JD.
