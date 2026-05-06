# Matching V2 Open Questions

Mục tiêu file: gom tất cả điểm cần quyết định trước khi code/rollout.

## 1. Taxonomy và normalization

- Bộ mapping seniority canonical giữa CV/JD (junior, mid, senior, lead...) chốt như thế nào?
- Mapping education level tương đương giữa nguồn dữ liệu khác nhau?
- Dictionary kỹ năng alias/synonym dùng nguồn nào và ai ownership?

## 2. Hard filter policy chi tiết

- `location` có strict tuyệt đối hay cho phép remote/hybrid fallback?
- `job_type` có mapping giữa contract/full-time/part-time khi CV không khai báo rõ?
- Education/certification bắt buộc: nếu dữ liệu CV thiếu thì loại ngay hay đưa vào trạng thái "insufficient_data"?

## 3. pgvector/index tuning

- Chốt strategy ban đầu: `hnsw` hay `ivfflat`?
- Tiêu chí benchmark để đổi index strategy?
- Reindex policy khi đổi `embedding_model_version`?

## 4. Score threshold và xếp hạng

- `min_score` mặc định của v2 là bao nhiêu?
- `bonus_exact_skill` và `penalty_missing_required` có cap/max cụ thể?
- Quy tắc tie-break khi final_score bằng nhau?

## 5. Data lifecycle

- TTL hoặc retention cho `match_results_v2`?
- Shadow-run result có lưu bảng riêng không?
- Chính sách backfill khi schema/feature_version thay đổi?

## 6. API và tương thích

- Route v2 có auth/role guard khác route cũ không?
- Có cần endpoint compare old-vs-v2 trong cùng response cho internal QA?
- Thời điểm deprecate route matching cũ sau khi v2 ổn định?
