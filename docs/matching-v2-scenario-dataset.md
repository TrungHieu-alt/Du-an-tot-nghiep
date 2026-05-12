# Matching V2 Slice 6B Scenario Dataset

Purpose: compact scenario dataset for Matching V2 run-only prototype coverage.
This is not the broad 40 JD / 240 CV dataset. The broad dataset is deferred to a
later slice.

Source files:
- `backend/db_v2/scenarios/matching_v2_slice_6b.json`
- `backend/db_v2/scenarios/matching_v2_slice_6b.schema.json`
- `backend/db_v2/scenario_embeddings.py`
- `backend/db_v2/seed_scenario.py`
- `backend/db_v2/validate_scenario_dataset.py`

The previously requested report path `docs/matching-v2-test-report.md` is not present.
The current baseline source is `docs/matching-v2-scenario-test-cases.md`, which
contains the executed baseline report and says it replaces the prior standalone
report. This Slice 6B dataset avoids recreating those exact baseline IDs/data.

## Dataset Shape

| Item | Count |
|---|---:|
| JD rows in `job_posts_v2` | 6 |
| CV rows in `candidate_profiles_v2` | 36 |
| CV per JD design group | 6 |
| Job embedding rows | 6 |
| Candidate embedding rows | 35 |

Candidate `3018` intentionally has no row in `candidate_embeddings_v2`. This
exercises missing embedding-row handling: semantic score components default to
`0` and reasoning mentions the missing CV embedding fields, including
`cv.emb_summary`.

## Reset And Validate

Use Docker Compose for runtime execution:

```bash
docker compose up -d postgres backend
docker compose exec backend python db_v2/reset.py --profile scenario
docker compose exec backend python db_v2/validate_scenario_dataset.py --db
```

Read-only local JSON/embedding validation:

```bash
python backend/db_v2/validate_scenario_dataset.py
```

The scenario profile is non-additive. It truncates only the four V2 prototype
tables before insert and does not create or seed user, recruiter, candidate,
application, or match result data.

## Embedding Workflow

Embeddings are generated locally by `backend/db_v2/scenario_embeddings.py`.

Properties:
- deterministic for the same JSON input;
- no network calls;
- 384 dimensions;
- L2-normalized for every non-null vector;
- non-constant vectors, with field-specific feature spaces;
- `title` vectors use title text;
- `skills` vectors use skill tokens;
- `requirement`, `summary`, and `experience` vectors use their own narrative text
  in a shared comparable semantic space;
- token and local concept features make related texts score higher than unrelated
  texts without external APIs.

## Scenario Matrix

### JD-1: Backend/DevOps Remote Senior

Job ID: `4001`. Remote JD, senior, requires `cka` and `aws_saa`.

| CV | Role | Expected |
|---:|---|---|
| 3001 | Strong pass | Passes hard filter despite `tp_hcm` location; expected top. |
| 3002 | Good pass | Passes despite `da_nang`; ranks below 3001 and above 3003. |
| 3003 | Noisy pass | Passes with partial cloud overlap; ranks below 3002. |
| 3004 | Hard fail | Fails only required certification subset: missing `aws_saa`. |
| 3005 | Semantic trap | Passes hard filter, similar title shape, wrong sales/marketing domain; ranks below 3003. |
| 3006 | Skill trap | Similar DevOps skills but `seniority=mid`; fails hard filter. |

Expected JD run: `3001 > 3002 > 3003 > 3005`; exclude `3004`, `3006`.

### JD-2: Frontend Fulltime Ha Noi Lead

Job ID: `4002`. Fulltime, `ha_noi`, lead.

| CV | Role | Expected |
|---:|---|---|
| 3007 | Strong pass | Lead frontend with full skill fit; expected top. |
| 3008 | Good pass | Lead frontend with partial skill fit; ranks below 3007. |
| 3009 | Noisy pass | Lead UI/web adjacent profile; ranks below 3008. |
| 3010 | Hard fail | Same location/job_type/skills but `seniority=senior`; fails seniority only. |
| 3011 | Hard fail | Same title/seniority/job_type/skills but `location=da_nang`; fails location only. |
| 3012 | Semantic trap | Frontend-like title, backend/data skills; passes hard filter but ranks below 3009. |

Expected JD run: `3007 > 3008 > 3009 > 3012`; exclude `3010`, `3011`.

### JD-3: AI/Data Fulltime TP HCM Mid

Job ID: `4003`. Fulltime, `tp_hcm`, mid, requires `dai_hoc`.

| CV | Role | Expected |
|---:|---|---|
| 3013 | Strong pass | `thac_si` education passes; strong ML/data fit; expected top. |
| 3014 | Good pass | `dai_hoc` equals requirement; good ML/data fit. |
| 3015 | Noisy pass | Adjacent analytics profile; ranks below 3014. |
| 3016 | Hard fail | All fields match but `education=lop_12`; fails education only. |
| 3017 | Low overlap pass | Hard filters pass with low skill overlap; ranks below 3015 with `min_score=0`. |
| 3018 | Missing embedding row | Hard filters pass; no `candidate_embeddings_v2` row and no exact skill overlap; score fields are `0` and deterministic missing-embedding reasoning is returned. |

Expected JD run with `min_score=0`: top `3013`, include `3018`, exclude `3016`,
and require `3013 > 3014 > 3015 > 3017`.

### JD-4: Product/BA Fulltime Da Nang Mid

Job ID: `4004`. Fulltime, `da_nang`, mid.

| CV | Role | Expected |
|---:|---|---|
| 3019 | Strong pass | Product/BA strong fit; expected top. |
| 3020 | Good pass | Product analyst with good partial BA fit. |
| 3021 | Noisy pass | Project/operations analyst adjacent to Product/BA. |
| 3022 | Hard fail | Same as strong but `location=ha_noi`; fails location only. |
| 3023 | Hard fail | Same as strong but `job_type=remote`; fails job_type only. |
| 3024 | Semantic trap | Business/growth title with sales/marketing skills; passes hard filter but ranks below 3021. |

Expected JD run: `3019 > 3020 > 3021 > 3024`; exclude `3022`, `3023`.

### JD-5: Sales/Marketing Parttime Ha Noi Junior

Job ID: `4005`. Parttime, `ha_noi`, junior, requires `google_ads`.

| CV | Role | Expected |
|---:|---|---|
| 3025 | Strong pass | Normalized lowercase skills/cert; expected top. |
| 3026 | Good pass | Growth/marketing parttime fit; ranks below 3025. |
| 3027 | Noisy pass | Customer success adjacent profile; ranks below 3026. |
| 3028 | Hard fail | Fulltime instead of parttime; fails job_type only. |
| 3029 | Low overlap pass | Hard filters pass but low relevant overlap; ranks below 3027. |
| 3030 | Normalization case | Source JSON has duplicated/spaced/mixed-case skills/certs; seed inserts lowercase, trimmed, unique arrays. |

Expected JD run: top `3025`; exclude `3028`; require `3025 > 3026 > 3027 > 3029`.

### JD-6: Finance/HR/Admin Fulltime TP HCM Mid

Job ID: `4006`. Fulltime, `tp_hcm`, mid.

| CV | Role | Expected |
|---:|---|---|
| 3031 | Strong pass | Finance/HR/Admin strong fit; expected top. |
| 3032 | Good pass A | Same expected score as 3033, lower `cv_id`; ranks first by tie-break. |
| 3033 | Good pass B | Same expected score as 3032, higher `cv_id`; ranks below 3032. |
| 3034 | Noisy pass | Lower-overlap finance/admin pass. |
| 3035 | Extra pass | Passes hard filter and supports top_k truncation. |
| 3036 | No-pass variant | Fails JD-6 and is used as reverse anchor for `total_after_filter=0`. |

Expected JD run with `top_k=3`, `min_score=0`: more than 3 candidates pass hard
filter, but only `3031`, `3032`, `3033` are returned; require `3032 > 3033`.

## Reverse Expectations

| Anchor | Expected |
|---:|---|
| CV 3031 | CV -> JD ranks JD `4006` above JD `4003`. |
| CV 3036 | CV -> JD returns `total_after_filter=0` and no matches. |

CV -> JD tie-break by `job_id` is already covered by the core runtime unit test.
The compact 6 JD business scenario does not force two realistic JD anchors to
have identical reverse scores, so the scenario JSON records that case as
`if_feasible` rather than manufacturing duplicate JD semantics.

## Global Coverage

Covered by this dataset:
- remote JD ignores location;
- non-remote location strict fail;
- job_type strict fail;
- seniority exact fail;
- education higher pass;
- education lower fail;
- required certification and multi-cert subset fail;
- low skill overlap pass ranks low;
- title-similar wrong-domain traps;
- skill-similar hard-filter traps;
- strong > good > noisy for all 6 JD anchors;
- JD -> CV tie-break by `cv_id`;
- top_k truncation;
- `total_after_filter=0`;
- `min_score=0` hard-filter separation;
- partial missing embedding does not crash;
- deterministic score fields and reasoning;
- reverse CV -> JD ranking beyond a single happy path;
- skills/certifications normalization.
