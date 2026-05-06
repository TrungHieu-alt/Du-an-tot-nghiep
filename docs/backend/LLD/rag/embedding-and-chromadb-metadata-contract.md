# LLD V2: Embedding and pgvector Contract

## Scope

Tài liệu này mô tả embedding fields tối thiểu cho prototype v2 run-only dùng PostgreSQL + pgvector.

## Embedding Contract

- Mỗi field semantic có một vector riêng.
- Prototype run-only không yêu cầu version metadata hoặc timestamps trong embedding tables.

## CV Embedding Fields

- `emb_title`
- `emb_skills`
- `emb_summary`
- `emb_experience`

## JD Embedding Fields

- `emb_title`
- `emb_skills`
- `emb_requirement`

## Storage Contract

Gợi ý tách bảng:
- `candidate_embeddings_v2`
- `job_embeddings_v2`

Mỗi bảng lưu:
- khóa business (`cv_id` hoặc `job_id`)
- vector columns

## Index Contract

- Prototype run-only không yêu cầu pgvector ANN index.
- Dùng exhaustive scoring trên seed/test dataset.
- `hnsw`/`ivfflat` chỉ chốt ở later phase khi có benchmark.
