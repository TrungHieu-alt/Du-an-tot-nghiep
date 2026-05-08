# Matching V2 Scenario Test Cases

Purpose: source of truth for Matching V2 test coverage, including executed baseline cases and the compact scenario dataset planned before any broad scale dataset.

This file replaces the previous standalone baseline test report.

## Scope

Target dataset:
- 6 JD.
- 36 CV.
- Exactly 6 designed CV per JD.
- Deterministic, local, normalized, non-constant 384-dimensional embeddings.
- No user, recruiter, candidate, application, or persisted match result data.

Out of scope:
- Broad 40 JD / 240 CV dataset.
- LLM scoring or reasoning.
- Persisted `match_results_v2`.
- ANN tuning, benchmark metrics, or labeled quality conclusions.

## Slice 6 Implementation Plan

This plan prepares the Matching V2 scenario dataset and verification flow. Broad 40 JD / 240 CV data is deferred until the compact scenario dataset passes.

| Slice | Mục tiêu | Deliverables | Definition of Done |
|---|---|---|---|
| Slice 6A — Seed Tooling + SQLAlchemy Models, No Runtime Refactor | Dùng SQLAlchemy cho seed tooling và schema mapping JD/CV V2, không thay runtime matching path. | SQLAlchemy dependency nếu thiếu; `pgvector.sqlalchemy.Vector(384)` hoặc `TypeDecorator` rõ ràng cho vector; engine/session factory cho DB V2; ORM models cho 4 bảng; seed tooling dùng ORM; tests insert/read qua ORM. | 1. SQLAlchemy kết nối được PostgreSQL V2 qua Docker Compose.<br>2. ORM map đúng 4 bảng: `job_posts_v2`, `candidate_profiles_v2`, `job_embeddings_v2`, `candidate_embeddings_v2`.<br>3. Vector mapping được chốt rõ: dùng `pgvector.sqlalchemy.Vector(384)` nếu thêm package `pgvector`, hoặc dùng `TypeDecorator` nội bộ có test insert/read.<br>4. Nếu thêm package mới, dependency được cập nhật rõ.<br>5. Không map `user`, `recruiter`, `candidate`, `application` vào prototype scope.<br>6. Không tạo `match_results_v2`.<br>7. Không import/use SQLAlchemy trong runtime matching path/router/runner.<br>8. Runtime matching vẫn dùng loader hiện tại trong slice này.<br>9. ORM insert/read được JD, CV, embeddings.<br>10. Tests cho ORM seed tooling pass. |
| Slice 6B — Minimal Scenario JD/CV Dataset + Deterministic Embeddings | Tạo dataset nhỏ nhất nhưng đủ kiểm tra các kịch bản matching V2 cốt lõi trước khi scale. Dataset có 6 JD + 36 CV, mỗi JD có đúng 6 CV được thiết kế quanh nó, không cộng dồn seed cũ. | Prompt/tool tạo JD/CV JSON; JSON scenario dataset; JSON schema validation; seed profile `scenario` hoặc reset script truncate rồi insert; deterministic embedding generator; scenario matrix mô tả pass/fail/ranking kỳ vọng; docs cách seed scenario dataset. | 1. Scenario seed không cộng dồn seed cũ: dùng seed profile `scenario` hoặc script truncate rồi insert.<br>2. Sau scenario reset DB có đúng 6 JD + 36 CV, không cộng dồn seed demo cũ.<br>3. Mỗi JD có đúng 6 CV được thiết kế quanh nó.<br>4. Dataset phủ tối thiểu 6 nhóm: Backend/DevOps, Frontend, AI/Data, Product/BA, Sales/Marketing, Finance/HR/Admin hoặc Ops/Service.<br>5. Có đúng 6 `job_embeddings_v2` + 36 `candidate_embeddings_v2`, trừ missing embedding case có chủ ý nếu được ghi rõ trong scenario matrix.<br>6. Dataset chỉ có JD/CV/embeddings, không có user/recruiter/application.<br>7. JSON schema validate taxonomy: `location`, `job_type`, `seniority`, `education`.<br>8. Skills/certifications lowercase, trim, unique.<br>9. Mỗi JD có ít nhất 1 strong pass, 1 good pass, 1 noisy pass.<br>10. Toàn dataset cover đủ fail cases: sai location non-remote, sai job_type, sai seniority, education thấp, thiếu certification, skill overlap thấp, title giống skill khác, skill giống nhưng fail seniority/location.<br>11. Có case explicit cho JD `remote` bỏ qua location.<br>12. Có case explicit cho non-remote strict location.<br>13. Có case education hierarchy: cao hơn pass, thấp hơn fail.<br>14. Có case multi-cert subset fail.<br>15. Có case `total_after_filter = 0`.<br>16. Có case `min_score = 0` để tách hard-filter exclusion khỏi score threshold.<br>17. Có case tie-break deterministic theo ID.<br>18. Có case `top_k` khi số candidate pass filter > `top_k`.<br>19. Có missing/partial embedding case: không crash, score field thiếu = 0, reasoning ghi rõ.<br>20. Mỗi CV khác nhau ít nhất 3 nhóm: title, skills, summary, experience, seniority, education, location/job_type, certifications.<br>21. Embedding generator là token-hash/bag-of-skills field-specific, normalized 384-dim, deterministic, không network.<br>22. Không dùng vector hằng làm mất ý nghĩa cosine ranking.<br>23. Reset + seed chạy sạch trên DB trống.<br>24. Broad 40/240 dataset được defer sang later slice. |
| Slice 6C — Ranking Expectations + E2E Verification | Kiểm tra matching trên scenario dataset bằng expected ranking, tách rõ hard-filter exclusion khỏi `min_score` exclusion. | Ranking expectation JSON; tests cho JD -> CV và CV -> JD; hard-filter tests; smoke live; OpenAPI V2 namespace check. | 1. Expectations có `anchor_type`, `anchor_id`, `top_k`, `min_score`, `expected_top_id`, `must_include`, `must_exclude`, `must_exclude_reason`, `must_rank_above`.<br>2. Hard-filter exclusion test chạy với `min_score=0` hoặc kiểm tra `total_after_filter` để không nhầm với score threshold.<br>3. Strong match đứng trên good match trong expectation chính.<br>4. Good match đứng trên noisy pass trong expectation chính.<br>5. Fail hard-filter CV không xuất hiện trong matches vì filter, không phải vì `min_score`.<br>6. Có expected top cho 6 JD scenario anchors, và thêm CV -> JD representative anchors theo scenario matrix.<br>7. Không hard-code exact `final_score` toàn dataset; nếu cần dùng score range.<br>8. JD -> CV endpoint chạy được trên scenario dataset.<br>9. CV -> JD endpoint chạy được trên scenario dataset.<br>10. Response có đủ score fields: `final_score`, `title_score`, `skills_score`, `req_exp_score`, `req_summary_score`, `reasoning`, và runtime metrics.<br>11. Ranking deterministic khi chạy lại cùng seed.<br>12. Tests pass.<br>13. OpenAPI check ghi rõ chỉ áp dụng namespace V2 prototype, gồm đúng 2 endpoint: `/api/v2/prototype/matching/job/{job_id}/run` và `/api/v2/prototype/matching/cv/{cv_id}/run`.<br>14. Legacy endpoints ngoài namespace V2 không tính là vi phạm Slice 6. |

## Executed Baseline Report

Execution date: 2026-05-08.

Environment:

| Thành phần | Chi tiết |
|---|---|
| Branch | `v2` |
| Backend | FastAPI + uvicorn, `http://localhost:8000` |
| Database | PostgreSQL 16 + pgvector, port `5433` |
| Data after extra seed | 10 CV, 10 JD, 9 CV embeddings, 10 JD embeddings |

Reproduction commands:

```bash
docker compose up -d postgres mongo backend
until curl -sf http://localhost:8000/api/health > /dev/null; do sleep 3; done && echo "Backend ready"
docker compose exec backend python db_v2/reset.py
docker compose cp backend/db_v2/seeds/002_extra_test_data.sql postgres:/tmp/002.sql
docker exec jobmatcher-postgres sh -c "psql -U jobmatcher -d jobmatcher_v2 -f /tmp/002.sql"
```

Count check:

```bash
docker exec jobmatcher-postgres sh -c "psql -U jobmatcher -d jobmatcher_v2 -c \"
  SELECT 'candidate_profiles_v2' AS tbl, COUNT(*) FROM candidate_profiles_v2
  UNION ALL SELECT 'job_posts_v2',            COUNT(*) FROM job_posts_v2
  UNION ALL SELECT 'candidate_embeddings_v2', COUNT(*) FROM candidate_embeddings_v2
  UNION ALL SELECT 'job_embeddings_v2',       COUNT(*) FROM job_embeddings_v2;\""
```

Expected counts after base reset:

| Table | Expected count |
|---|---:|
| `candidate_profiles_v2` | 5 |
| `job_posts_v2` | 5 |
| `candidate_embeddings_v2` | 5 |
| `job_embeddings_v2` | 5 |

Expected extra seed output from `backend/db_v2/seeds/002_extra_test_data.sql`:

| Insert target | Expected output |
|---|---|
| `candidate_profiles_v2` | `INSERT 0 5` |
| `job_posts_v2` | `INSERT 0 5` |
| `candidate_embeddings_v2` | `INSERT 0 4`, because CV `1010` intentionally has no embedding row |
| `job_embeddings_v2` | `INSERT 0 5` |

Expected counts after extra seed:

| Table | Expected count |
|---|---:|
| `candidate_profiles_v2` | 10 |
| `job_posts_v2` | 10 |
| `candidate_embeddings_v2` | 9 |
| `job_embeddings_v2` | 10 |

Backend data visibility smoke:

```bash
curl -s "http://localhost:8000/api/v2/prototype/matching/job/2006/run" | python -m json.tool
```

Expected visibility signal: `total_candidates=10`.

Determinism note:
- Existing baseline seed used `array_fill(value, ARRAY[384])` placeholder embeddings.
- Constant vectors make cosine similarity equal to `1.0` for any non-missing pair.
- Baseline ranking is deterministic, but semantic ranking is not meaningful.
- Only exact skill overlap creates score differences in the baseline cases.

### Baseline Extra Test Data

CV rows added by `002_extra_test_data.sql`:

| cv_id | title | location | job_type | seniority | education | certifications | purpose |
|---:|---|---|---|---|---|---|---|
| 1006 | Senior DevOps Engineer | ha_noi | remote | senior | dai_hoc | cka, aws_saa | main match for JD 2006 |
| 1007 | Mid ML Engineer | tp_hcm | fulltime | mid | thac_si | none | main match for JD 2007 |
| 1008 | Frontend Lead | ha_noi | fulltime | lead | dai_hoc | none | main match for JD 2008 |
| 1009 | Intern Backend Developer | ha_noi | fulltime | intern | lop_12 | none | main match for JD 2009 |
| 1010 | Mid Data Scientist | da_nang | parttime | mid | tien_si | google_ml | no embedding row by design |

JD rows added by `002_extra_test_data.sql`:

| job_id | title | location | job_type | seniority | education | required_certifications | purpose |
|---:|---|---|---|---|---|---|---|
| 2006 | Senior DevOps Engineer | ha_noi | remote | senior | dai_hoc | cka | cert filter + skills ranking |
| 2007 | Mid ML Engineer | tp_hcm | fulltime | mid | dai_hoc | none | location + education hierarchy |
| 2008 | Frontend Lead | ha_noi | fulltime | lead | dai_hoc | none | seniority filter |
| 2009 | Intern Backend Developer | ha_noi | fulltime | intern | lop_9 | none | strict intern seniority |
| 2010 | Mid Data Scientist | da_nang | parttime | mid | thac_si | google_ml | missing embeddings path |

### Baseline Covered Cases

| Kịch bản | Filter | Kết quả | Trạng thái |
|---|---|---|---|
| 1. JD 2006 cert filter + skills ranking | `job_type=remote`, `cka` required | 2 pass, rank by exact skill overlap | Covered |
| 2. JD 2007 location + education hierarchy | `tp_hcm`, `fulltime`, `mid`, `thac_si>=dai_hoc` | 1 pass | Covered |
| 3. JD 2008 seniority exact | `lead`; junior excluded | 2 pass, CV 1008 rank 1 | Covered |
| 4. JD 2009 intern strict seniority | `intern` only | 1 pass | Covered |
| 5a. JD 2010 missing embeddings default threshold | hard filter pass, score below `0.7` | 0 returned | Covered |
| 5b. JD 2010 missing embeddings with `min_score=0` | hard filter pass | CV 1010 returned with low score and missing-embedding reasoning | Covered |
| 6. CV 1006 -> JD reverse match | `remote`, `senior`, `dai_hoc`, cert compatible | JD 2006 rank 1, JD 2003 rank 2 | Covered |

#### Baseline Case 1: JD 2006 required certification + skills ranking

Request:

```bash
curl -s -X POST "http://localhost:8000/api/v2/prototype/matching/job/2006/run" \
  -H "Content-Type: application/json" \
  -d '{"top_k":10,"min_score":0.7}' | python -m json.tool
```

Expected totals:

| Metric | Value |
|---|---:|
| `total_candidates` | 10 |
| `total_after_filter` | 2 |
| `total_returned` | 2 |

Expected matches:

| rank | cv_id | final_score | skills_score | exact skill matches |
|---:|---:|---:|---:|---|
| 1 | 1006 | 1.000 | 1.000 | aws, docker, kubernetes, terraform |
| 2 | 1003 | 0.895 | 0.700 | docker |

Expected reasoning:
- CV `1006` has all 4 matching skills, so `exact_overlap=4/max(4,4)=1.0`.
- CV `1003` has only `docker`, so `exact_overlap=1/max(4,4)=0.25`.
- Other CVs are excluded by hard filter because they are not `remote` or do not have required cert `cka`.

#### Baseline Case 2: JD 2007 location + education hierarchy

Request:

```bash
curl -s -X POST "http://localhost:8000/api/v2/prototype/matching/job/2007/run" \
  -H "Content-Type: application/json" \
  -d '{"top_k":10,"min_score":0.7}' | python -m json.tool
```

Expected totals:

| Metric | Value |
|---|---:|
| `total_candidates` | 10 |
| `total_after_filter` | 1 |
| `total_returned` | 1 |

Expected matches:

| rank | cv_id | final_score | exact skill matches |
|---:|---:|---:|---|
| 1 | 1007 | 0.965 | ml, python, tensorflow |

Expected hard-filter exclusions:

| cv_id | expected exclusion |
|---:|---|
| 1001 | location + seniority |
| 1002 | seniority |
| 1003 | job_type |
| 1004 | job_type |
| 1005 | location |
| 1006 | job_type |
| 1008 | location |
| 1009 | location |
| 1010 | job_type |

Education check: CV `1007` has `thac_si`, which passes JD `dai_hoc` because `lop_9 < lop_12 < dai_hoc < thac_si < tien_si`.

#### Baseline Case 3: JD 2008 seniority exact

Request:

```bash
curl -s -X POST "http://localhost:8000/api/v2/prototype/matching/job/2008/run" \
  -H "Content-Type: application/json" \
  -d '{"top_k":10,"min_score":0.7}' | python -m json.tool
```

Expected totals:

| Metric | Value |
|---|---:|
| `total_candidates` | 10 |
| `total_after_filter` | 2 |
| `total_returned` | 2 |

Expected matches:

| rank | cv_id | final_score | skills_score | note |
|---:|---:|---:|---:|---|
| 1 | 1008 | 1.000 | 1.000 | 4 exact frontend skill matches |
| 2 | 1005 | 0.860 | 0.600 | 0 exact overlap; inflated by constant semantic vectors |

Expected reasoning:
- CV `1002` is excluded because `junior != lead`.
- CV `1008` ranks first because skills match fully.
- CV `1005` demonstrates the limitation of constant embeddings: semantic components are `1.0`, so a wrong-domain CV can still score `0.860`.

#### Baseline Case 4: JD 2009 intern strict seniority

Request:

```bash
curl -s -X POST "http://localhost:8000/api/v2/prototype/matching/job/2009/run" \
  -H "Content-Type: application/json" \
  -d '{"top_k":10,"min_score":0.7}' | python -m json.tool
```

Expected totals:

| Metric | Value |
|---|---:|
| `total_candidates` | 10 |
| `total_after_filter` | 1 |
| `total_returned` | 1 |

Expected matches:

| rank | cv_id | final_score | exact skill matches |
|---:|---:|---:|---|
| 1 | 1009 | 1.000 | python, sql |

Expected reasoning:
- Only `intern` seniority passes.
- CV `1009` education `lop_12` passes JD requirement `lop_9`.

#### Baseline Case 5: JD 2010 missing embeddings

Default threshold request:

```bash
curl -s -X POST "http://localhost:8000/api/v2/prototype/matching/job/2010/run" \
  -H "Content-Type: application/json" \
  -d '{"top_k":10,"min_score":0.7}' | python -m json.tool
```

Expected default-threshold result:

| Metric | Value |
|---|---:|
| `total_after_filter` | 1 |
| `total_returned` | 0 |

Low-threshold request:

```bash
curl -s -X POST "http://localhost:8000/api/v2/prototype/matching/job/2010/run" \
  -H "Content-Type: application/json" \
  -d '{"top_k":10,"min_score":0.0}' | python -m json.tool
```

Expected low-threshold match:

| rank | cv_id | final_score | skills_score | note |
|---:|---:|---:|---:|---|
| 1 | 1010 | 0.140 | 0.400 | title, requirement/experience, and requirement/summary semantic scores are `0` |

Expected reasoning:
- CV `1010` passes hard filters: `parttime`, `da_nang`, `mid`, `tien_si >= thac_si`, has `google_ml`.
- CV `1010` has no row in `candidate_embeddings_v2`, so semantic components are `0`.
- Exact skills match `python`, `ml`, `statistics`, so `skills_score=0.4` from exact overlap only.
- Final score is `0.14`, below the default `min_score=0.7`.

#### Baseline Case 6: CV 1006 -> JD reverse match

Request:

```bash
curl -s -X POST "http://localhost:8000/api/v2/prototype/matching/cv/1006/run" \
  -H "Content-Type: application/json" \
  -d '{"top_k":10,"min_score":0.7}' | python -m json.tool
```

Expected matches:

| rank | job_id | final_score | exact skill matches |
|---:|---:|---:|---|
| 1 | 2006 | 1.000 | aws, docker, kubernetes, terraform |
| 2 | 2003 | 0.860 | none |

Expected reasoning:
- JD `2006` is the best match for CV `1006`.
- JD `2003` passes hard filters because it is `remote`, `senior`, requires `dai_hoc`, and has no missing required certification.
- JD `2003` has 0 exact skill overlap with CV `1006`; its score is inflated by constant semantic vectors.

Baseline unit test evidence:

| Suite | Result |
|---|---|
| `tests/test_matching_v2_core.py` + `tests/test_match_v2_router.py` | 26/26 PASS |

Baseline observations:
- Hard filters worked for seniority exact, education hierarchy, certification subset, job type, and non-remote location.
- Ranking in baseline data was driven mostly by exact skill overlap.
- Missing embedding rows were handled safely.
- Constant vectors make the baseline unsuitable for real semantic ranking tests.

Do not recreate these exact scenarios one-for-one. Keep only minimal regression smoke where needed.

## Gaps To Cover

The scenario dataset should focus on these uncovered or weakly covered cases:

| Gap | Expected coverage |
|---|---|
| Remote ignores location | JD remote should allow CVs with different `location` when other hard filters pass. |
| Isolated non-remote location fail | Same fields except `location` must fail only by location. |
| Isolated job type fail | Same fields except `job_type` must fail only by job type. |
| Education lower-than-required fail | Same fields except lower education must fail only by education. |
| Multi-cert subset fail | JD requires multiple certs; CV missing one required cert must fail. |
| Title trap | Similar title but wrong skills/domain must not outrank strong/good matches. |
| Skill trap | Similar skills but wrong seniority/location/job_type must fail hard filter. |
| Strong > good > noisy | At least 3 anchors must prove ranking order with non-constant embeddings. |
| Tie-break deterministic | Same score should sort by `cv_id asc` for JD -> CV and `job_id asc` for CV -> JD where feasible. |
| `top_k` truncation | More candidates pass filter than `top_k`; only `top_k` returned. |
| `total_after_filter=0` | A request should show no candidates survive hard filters. |
| Partial missing embeddings | Missing one semantic field should not crash; affected score field is `0`. |
| Reverse CV -> JD beyond happy path | At least one reverse expectation should include `expected_top_id` and `must_rank_above`. |
| Normalization | Skills/certifications are lowercase, trimmed, unique. |

## Planned Scenario Matrix

Use deterministic IDs when implementing, for example JD `4001..4006` and CV `3001..3036`.

| Kịch bản | Anchor | Filter / Setup | Expected | Trạng thái |
|---|---:|---|---|---|
| 1. Remote ignores location + multi-cert + ranking | JD-1 Backend/DevOps remote senior | `job_type=remote`, `seniority=senior`, required certs `[cka, aws_saa]`; passing CVs may have a different `location` | `total_after_filter=3`; strong > good > noisy; missing `aws_saa` is excluded by cert; different location is allowed | Planned |
| 1a. Strong DevOps pass | JD-1 -> CV-1 | remote, senior, different location, has all required certs, high title/skills/experience fit | CV-1 rank 1, `expected_top_id=CV-1` | Planned |
| 1b. Good DevOps pass | JD-1 -> CV-2 | remote, senior, different location, all required certs, weaker requirement/summary fit | CV-2 ranks below CV-1 and above CV-3 | Planned |
| 1c. Noisy DevOps pass | JD-1 -> CV-3 | remote, senior, different location, all required certs, partial skill overlap | CV-3 passes hard filter but ranks below CV-1/CV-2 | Planned |
| 1d. Multi-cert subset fail | JD-1 -> CV-4 | all hard-filter fields pass, but CV has `cka` and misses `aws_saa` | CV-4 is absent from matches; expected reason `missing_required_certification` | Planned |
| 1e. Title trap | JD-1 -> CV-5 | title resembles DevOps, but skills/domain are wrong | If hard filter passes, CV-5 must not rank above CV-2/CV-3 | Planned |
| 1f. Skill trap fail | JD-1 -> CV-6 | DevOps-like skills, but seniority or job type is wrong | CV-6 is absent by hard filter, not by `min_score` | Planned |
| 2. Frontend lead seniority exact | JD-2 Frontend fulltime ha_noi lead | `job_type=fulltime`, `location=ha_noi`, `seniority=lead` | seniority mismatch excluded; strong > good > noisy | Planned |
| 2a. Strong Frontend pass | JD-2 -> CV-7 | lead, fulltime, ha_noi, frontend skills full overlap | CV-7 rank 1 | Planned |
| 2b. Good Frontend pass | JD-2 -> CV-8 | lead, fulltime, ha_noi, good frontend overlap | CV-8 ranks below CV-7 | Planned |
| 2c. Noisy Frontend pass | JD-2 -> CV-9 | lead, fulltime, ha_noi, adjacent UI/web profile | CV-9 passes but ranks lower | Planned |
| 2d. Seniority isolated fail | JD-2 -> CV-10 | same location/job_type/skills, but `seniority=senior` instead of `lead` | CV-10 excluded by seniority only | Planned |
| 2e. Job type isolated fail | JD-2 -> CV-11 | same location/seniority/skills, but wrong `job_type` | CV-11 excluded by job type only | Planned |
| 2f. Frontend title trap | JD-2 -> CV-12 | frontend-like title, mostly backend/data skills | If hard filter passes, score stays below CV-7/CV-8 | Planned |
| 3. AI/Data education hierarchy + partial embedding | JD-3 AI/Data fulltime tp_hcm mid | `job_type=fulltime`, `location=tp_hcm`, `seniority=mid`, `education>=dai_hoc` | higher education passes, lower education fails, partial embedding safe | Planned |
| 3a. Strong AI/Data pass | JD-3 -> CV-13 | mid, fulltime, tp_hcm, `thac_si`, strong ML/data fit | CV-13 rank 1; higher education passes | Planned |
| 3b. Good AI/Data pass | JD-3 -> CV-14 | mid, fulltime, tp_hcm, `dai_hoc`, good skill fit | CV-14 passes and ranks below CV-13 | Planned |
| 3c. Noisy analytics pass | JD-3 -> CV-15 | mid, fulltime, tp_hcm, `thac_si`, adjacent analytics profile | CV-15 passes but ranks below CV-13/CV-14 | Planned |
| 3d. Education lower fail | JD-3 -> CV-16 | all hard-filter fields match, but `education=lop_12` | CV-16 excluded by education only | Planned |
| 3e. Low skill overlap pass | JD-3 -> CV-17 | hard filters pass, very low skill overlap | With `min_score=0`, visible low score; otherwise may be thresholded out | Planned |
| 3f. Partial missing embedding | JD-3 -> CV-18 | hard filters pass, one semantic embedding field missing or zeroed | No crash; affected score field is `0`; reasoning mentions missing embedding | Planned |
| 4. Product/BA non-remote strict location/job type | JD-4 Product/BA fulltime da_nang mid | `job_type=fulltime`, `location=da_nang`, `seniority=mid` | isolated location and job type failures are distinguishable | Planned |
| 4a. Strong Product/BA pass | JD-4 -> CV-19 | fulltime, da_nang, mid, strong BA/product skills | CV-19 rank 1 | Planned |
| 4b. Good Product/BA pass | JD-4 -> CV-20 | fulltime, da_nang, mid, good product analyst profile | CV-20 ranks below CV-19 | Planned |
| 4c. Noisy Product/BA pass | JD-4 -> CV-21 | fulltime, da_nang, mid, adjacent project/ops analyst | CV-21 passes but ranks below good | Planned |
| 4d. Location isolated fail | JD-4 -> CV-22 | same as strong but `location=ha_noi` | CV-22 excluded by location only | Planned |
| 4e. Job type isolated fail | JD-4 -> CV-23 | same as strong but wrong `job_type` | CV-23 excluded by job type only | Planned |
| 4f. Business title trap | JD-4 -> CV-24 | BA/Product-like title, sales/marketing skills | If hard filter passes, score lower than noisy; not top result | Planned |
| 5. Sales/Marketing parttime + normalization | JD-5 Sales/Marketing parttime ha_noi junior | `job_type=parttime`, `location=ha_noi`, `seniority=junior` | parttime strict; low overlap ranks low; normalization verified | Planned |
| 5a. Strong Sales/Marketing pass | JD-5 -> CV-25 | parttime, ha_noi, junior, strong matching skills | CV-25 rank 1 | Planned |
| 5b. Good Growth pass | JD-5 -> CV-26 | parttime, ha_noi, junior, good growth/marketing overlap | CV-26 ranks below CV-25 | Planned |
| 5c. Noisy CS pass | JD-5 -> CV-27 | parttime, ha_noi, junior, customer-success adjacent profile | CV-27 passes but ranks lower | Planned |
| 5d. Parttime strict fail | JD-5 -> CV-28 | same fields but `job_type=fulltime` | CV-28 excluded by job type only | Planned |
| 5e. Low overlap pass | JD-5 -> CV-29 | hard filters pass, low sales/marketing skill overlap | Visible with low threshold or ranks last | Planned |
| 5f. Normalization case | JD-5 -> CV-30 | source JSON contains duplicated/spaced/mixed-case skills or certs before validation | inserted/validated skills and certs are lowercase, trimmed, unique | Planned |
| 6. Finance/HR/Admin top_k + tie-break + reverse | JD-6 Finance/HR/Admin fulltime tp_hcm mid | many candidates pass filter; a pair has identical expected score | `top_k` truncates; tie-break by ID; reverse CV -> JD expected ranking | Planned |
| 6a. Strong Finance/Admin pass | JD-6 -> CV-31 | fulltime, tp_hcm, mid, strong finance/admin skills | CV-31 rank 1 | Planned |
| 6b. Tie candidate A | JD-6 -> CV-32 | hard filters pass, designed score equal to CV-33, lower `cv_id` | CV-32 ranks above CV-33 by `cv_id asc` | Planned |
| 6c. Tie candidate B | JD-6 -> CV-33 | hard filters pass, designed score equal to CV-32, higher `cv_id` | CV-33 ranks below CV-32 | Planned |
| 6d. Extra pass for top_k | JD-6 -> CV-34 | hard filters pass, plausible score | With `top_k=3`, CV-34 is not returned if ranked 4+ | Planned |
| 6e. Noisy pass | JD-6 -> CV-35 | hard filters pass, low but valid score | Ensures pass pool is larger than `top_k` | Planned |
| 6f. No-pass variant | JD-6 -> CV-36 | wrong hard-filter field or used with secondary anchor | Used for `total_after_filter=0` expectation if needed | Planned |
| 7. `min_score=0` separation | selected JD with fail and low-score candidates | run with `min_score=0` | hard-filter failures remain absent; low-score pass candidates become visible | Planned |
| 8. `total_after_filter=0` | dedicated JD request or secondary expectation | anchor has no candidates passing hard filters | `total_after_filter=0`, `total_returned=0`; not confused with thresholding | Planned |
| 9. CV -> JD reverse strong path | selected strong CV, likely CV-1 or CV-31 | reverse endpoint `/cv/{cv_id}/run` | expected top JD is its designed anchor; includes `must_rank_above` | Planned |
| 10. CV -> JD reverse tie-break | selected tie CV if feasible | two JD candidates have same score | lower `job_id` ranks first by deterministic tie-break | Planned |

## Expected Output Shape

For JD -> CV expectations:

```json
{
  "anchor_type": "job",
  "anchor_id": 4001,
  "top_k": 10,
  "min_score": 0.7,
  "expected_top_id": 3001,
  "must_include": [3001, 3002, 3003],
  "must_exclude": [3004, 3006],
  "must_exclude_reason": {
    "3004": "missing_required_certification",
    "3006": "hard_filter"
  },
  "must_rank_above": [
    [3001, 3002],
    [3002, 3003]
  ]
}
```

For hard-filter separation expectations:

```json
{
  "anchor_type": "job",
  "anchor_id": 4001,
  "top_k": 10,
  "min_score": 0.0,
  "must_exclude": [3004, 3006],
  "must_exclude_reason": {
    "3004": "missing_required_certification",
    "3006": "hard_filter"
  }
}
```

## Definition Of Done For Scenario Dataset

1. Scenario reset does not accumulate old seed data.
2. After reset, DB has exactly 6 JD and 36 CV.
3. Each JD has exactly 6 designed CV.
4. Dataset contains only JD/CV prototype data and embeddings.
5. There are exactly 6 `job_embeddings_v2` rows.
6. There are exactly 36 `candidate_embeddings_v2` rows unless a documented field-level missing embedding case is represented differently.
7. JSON schema validation passes for `location`, `job_type`, `seniority`, and `education`.
8. Skills/certifications are lowercase, trimmed, and unique.
9. All gaps listed above are covered.
10. Scenario matrix documents every CV purpose.
11. Embeddings are deterministic, local, normalized, 384-dimensional, and non-constant.
12. Reset + seed runs cleanly on an empty DB.
13. Broad 40/240 dataset is explicitly deferred to a later slice.
