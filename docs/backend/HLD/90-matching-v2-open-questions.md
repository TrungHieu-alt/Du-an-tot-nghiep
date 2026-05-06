# Matching V2 Open Questions

Location đã chốt: `ha_noi|tp_hcm|da_nang` (remote bỏ qua location filter).

Mục tiêu file: chỉ giữ các quyết định chưa chốt cho prototype matching-only (database có thể reset và seed trực tiếp).

## 1. Taxonomy/normalization

- Mapping seniority canonical giữa CV/JD chốt danh mục cụ thể nào?
- Dictionary skills alias/synonym dùng nguồn nào và ai ownership?

## 2. Score policy

- `min_score` mặc định nên là bao nhiêu?
- `bonus_exact_skill` và `penalty_missing_required` có cap/max cụ thể không?
- Quy tắc tie-break khi `final_score` bằng nhau?

## 3. pgvector/index

- Chốt strategy ban đầu `hnsw` hay `ivfflat`?
- Điều kiện benchmark để đổi strategy?
- Reindex policy khi đổi embedding/model version?

## 4. API compatibility

- Route v2 có auth/role guard riêng ngay từ đầu không?
- Có cần endpoint compare old-vs-v2 cho internal QA không?
