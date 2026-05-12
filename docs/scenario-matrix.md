# Matching V2 Slice 6B — Scenario Matrix

Generated from `backend/db_v2/scenario/dataset.json`.  
Seed script: `python -m db_v2.scenario.reset_scenario`  
Validation: `python -m db_v2.scenario.validate` (15 checks)

---

## JD-1 · job_id=4001 — Senior Backend DevOps Engineer

| Field | Value |
|-------|-------|
| job_type | remote |
| seniority | senior |
| education | dai_hoc |
| location | ha_noi |
| required_certifications | cka, aws_saa |

### Hard-filter rules
- `job_type == "remote"` → location bypass (any location allowed)
- `seniority == "senior"` (exact)
- `education >= dai_hoc`
- certifications ⊇ {cka, aws_saa}

### CV roster

| cv_id | role | job_type | seniority | education | location | certifications | filter result | notes |
|-------|------|----------|-----------|-----------|----------|---------------|---------------|-------|
| 3001 | perfect_match | remote | senior | dai_hoc | ha_noi | cka, aws_saa | **PASS** | rank 1 |
| 3002 | above_seniority | remote | lead | thac_si | ha_noi | cka, aws_saa | **FAIL** | seniority lead ≠ senior (exact match required) |
| 3003 | missing_one_cert | remote | senior | dai_hoc | ha_noi | aws_saa | **FAIL** | missing cka → cert filter |
| 3004 | below_seniority | remote | mid | dai_hoc | ha_noi | aws_saa | **FAIL** | seniority mismatch |
| 3005 | wrong_job_type | fulltime | senior | dai_hoc | ha_noi | cka, aws_saa | **FAIL** | job_type fulltime ≠ remote |
| 3006 | wrong_location_non_remote | fulltime | senior | dai_hoc | tp_hcm | cka, aws_saa | **FAIL** | job_type fulltime + wrong location |

**Test cases covered:** T01 (perfect match), T02 (above seniority filtered), T03 (cert subset fail), T07 (job_type mismatch), T09 (location bypass for remote JD)

---

## JD-2 · job_id=4002 — Lead Frontend Engineer

| Field | Value |
|-------|-------|
| job_type | fulltime |
| seniority | lead |
| education | dai_hoc |
| location | ha_noi |
| required_certifications | (none) |

### CV roster

| cv_id | role | job_type | seniority | education | location | filter result | notes |
|-------|------|----------|-----------|-----------|----------|---------------|-------|
| 3007 | perfect_match | fulltime | lead | dai_hoc | ha_noi | **PASS** | rank 1 |
| 3008 | higher_education | fulltime | lead | thac_si | ha_noi | **PASS** | higher edu; ranks by score |
| 3009 | lower_education_filtered | fulltime | lead | lop_12 | ha_noi | **FAIL** | education < dai_hoc |
| 3010 | senior_not_lead_filtered | fulltime | senior | dai_hoc | ha_noi | **FAIL** | seniority mismatch |
| 3011 | wrong_location_filtered | fulltime | lead | dai_hoc | da_nang | **FAIL** | location mismatch |
| 3012 | remote_type_filtered | remote | lead | dai_hoc | ha_noi | **FAIL** | job_type mismatch |

**Test cases covered:** T04 (education threshold), T05 (seniority exact), T06 (location filter), T07 (job_type filter)

---

## JD-3 · job_id=4003 — Mid AI Data Scientist

| Field | Value |
|-------|-------|
| job_type | fulltime |
| seniority | mid |
| education | dai_hoc |
| location | tp_hcm |
| required_certifications | (none) |

### CV roster

| cv_id | role | job_type | seniority | education | location | filter result | notes |
|-------|------|----------|-----------|-----------|----------|---------------|-------|
| 3013 | perfect_match | fulltime | mid | dai_hoc | tp_hcm | **PASS** | rank 1 |
| 3014 | higher_education | fulltime | mid | thac_si | tp_hcm | **PASS** | higher edu passes |
| 3015 | partial_skills | fulltime | mid | dai_hoc | tp_hcm | **PASS** | lower score than 3013/3014 |
| 3016 | below_seniority_filtered | fulltime | junior | dai_hoc | tp_hcm | **FAIL** | seniority mismatch |
| 3017 | wrong_location_filtered | fulltime | mid | dai_hoc | ha_noi | **FAIL** | location mismatch |
| 3018 | missing_embedding | fulltime | mid | thac_si | tp_hcm | **PASS** (profile only) | no embedding row → all semantic scores=0; reasoning notes missing emb |

**Test cases covered:** T08 (missing embedding graceful handling), T10 (semantic scoring with partial skills), T05 (seniority filter), T06 (location filter)

---

## JD-4 · job_id=4004 — Mid Product Business Analyst

| Field | Value |
|-------|-------|
| job_type | fulltime |
| seniority | mid |
| education | dai_hoc |
| location | da_nang |
| required_certifications | (none) |

### CV roster

| cv_id | role | job_type | seniority | education | location | certifications | filter result | notes |
|-------|------|----------|-----------|-----------|----------|---------------|---------------|-------|
| 3019 | perfect_match | fulltime | mid | dai_hoc | da_nang | — | **PASS** | rank 1 |
| 3020 | extra_certifications | fulltime | mid | dai_hoc | da_nang | cbap | **PASS** | extra certs don't hurt |
| 3021 | partial_skills_lower_score | fulltime | mid | dai_hoc | da_nang | — | **PASS** | lower semantic score |
| 3022 | wrong_seniority_filtered | fulltime | junior | dai_hoc | da_nang | — | **FAIL** | seniority mismatch |
| 3023 | wrong_location_filtered | fulltime | mid | dai_hoc | tp_hcm | — | **FAIL** | location mismatch |
| 3024 | wrong_job_type_filtered | remote | mid | dai_hoc | da_nang | — | **FAIL** | job_type mismatch |

**Test cases covered:** T11 (extra certifications still pass), T12 (partial skills → lower rank), T05 (seniority filter), T06 (location filter), T07 (job_type filter)

---

## JD-5 · job_id=4005 — Junior Sales Marketing Executive

| Field | Value |
|-------|-------|
| job_type | parttime |
| seniority | junior |
| education | lop_12 |
| location | ha_noi |
| required_certifications | (none) |

### CV roster

| cv_id | role | job_type | seniority | education | location | filter result | notes |
|-------|------|----------|-----------|-----------|----------|---------------|-------|
| 3025 | perfect_match | parttime | junior | lop_12 | ha_noi | **PASS** | rank 1 |
| 3026 | university_degree_higher_edu | parttime | junior | dai_hoc | ha_noi | **PASS** | education > lop_12 passes |
| 3027 | partial_skills | parttime | junior | lop_12 | ha_noi | **PASS** | fewer skills → lower score |
| 3028 | below_education_filtered | parttime | junior | lop_9 | ha_noi | **FAIL** | education < lop_12 |
| 3029 | wrong_seniority_filtered | parttime | mid | dai_hoc | ha_noi | **FAIL** | seniority mismatch |
| 3030 | normalization_case | parttime | junior | lop_12 | ha_noi | **PASS** | raw skills have mixed case/spaces/dups; normalized on insert |

**Test cases covered:** T13 (education hierarchy lop_9 fail), T14 (normalization: skills deduplicated/lowercased), T04 (education threshold), T05 (seniority filter)

---

## JD-6 · job_id=4006 — Finance HR Administrator

| Field | Value |
|-------|-------|
| job_type | fulltime |
| seniority | mid |
| education | dai_hoc |
| location | tp_hcm |
| required_certifications | (none) |

### CV roster

| cv_id | role | job_type | seniority | education | location | certifications | filter result | notes |
|-------|------|----------|-----------|-----------|----------|---------------|---------------|-------|
| 3031 | perfect_match | fulltime | mid | dai_hoc | tp_hcm | — | **PASS** | rank 1; exact title + full skills match |
| 3032 | tie_pair_a | fulltime | mid | dai_hoc | tp_hcm | — | **PASS** | tie with 3033 on final_score; cv_id 3032 < 3033 → rank 2 |
| 3033 | tie_pair_b | fulltime | mid | thac_si | tp_hcm | hrci | **PASS** | same title tokens as 3032 → identical title embedding → tie; rank 3 |
| 3034 | partial_skills | fulltime | mid | dai_hoc | tp_hcm | — | **PASS** | lower score (HR generalist, no finance/payroll) |
| 3035 | wrong_seniority_filtered | fulltime | junior | dai_hoc | tp_hcm | — | **FAIL** | seniority mismatch |
| 3036 | total_after_filter_zero | fulltime | mid | dai_hoc | ha_noi | — | **FAIL** | ha_noi ≠ tp_hcm; also fails all other 5 JDs → total_after_filter=0 |

**Test cases covered:** T15 (tie-pair: same embedding → identical score → sort by cv_id), T16 (total_after_filter=0), T17 (extra certs/edu don't block pass), T18 (partial skills lower rank)

---

## Global test case → scenario mapping

| Test | Description | Primary CVs | JD |
|------|-------------|-------------|-----|
| T01 | Perfect match ranks first | 3001 | 4001 |
| T02 | Above-seniority candidate filtered (seniority is exact match) | 3002 | 4001 |
| T03 | Missing required cert → hard filtered | 3003 | 4001 |
| T04 | Education below threshold → hard filtered | 3009, 3028 | 4002, 4005 |
| T05 | Seniority mismatch → hard filtered | 3004, 3010, 3016, 3022, 3029, 3035 | multiple |
| T06 | Location mismatch → hard filtered (non-remote) | 3011, 3017, 3023 | multiple |
| T07 | job_type mismatch → hard filtered | 3005, 3012, 3024 | multiple |
| T08 | Missing embedding → semantic score=0, no crash | 3018 | 4003 |
| T09 | Remote JD → location bypass (any location passes) | 3001, 3002 | 4001 |
| T10 | Partial skill overlap → lower semantic score | 3015 | 4003 |
| T11 | Extra certifications do not block filter pass | 3020 | 4004 |
| T12 | Partial skills lower rank vs full-match | 3021 vs 3019 | 4004 |
| T13 | Education hierarchy: lop_9 < lop_12 boundary | 3028 | 4005 |
| T14 | Skills normalization (case/spaces/dedup) | 3030 | 4005 |
| T15 | Tie-pair: identical embedding → sort by cv_id asc | 3032, 3033 | 4006 |
| T16 | total_after_filter=0 for unmatched CV | 3036 | all |
| T17 | Extra certs + higher edu do not block | 3033 | 4006 |
| T18 | Partial skills → lower rank | 3034 | 4006 |
| T19 | above_seniority (lead vs senior JD req) | 3002 | 4001 |
| T20 | Non-remote JD job_type + location both required | 3005, 3006 | 4001 |

---

## Embedding strategy

Historical fixture embeddings are generated by `db_v2/scenario/embedder.py`
only when `DB_V2_USE_DETERMINISTIC_FIXTURE_EMBEDDINGS=1`:

1. Tokenize by whitespace, lowercase, deduplicate (first-occurrence order), drop single-char tokens.
2. For each token, seed a 384-dim standard-normal vector from SHA-256 hash of the token bytes.
3. Sum token vectors, L2-normalize the result.
4. Return `float32` array. Zero vector if no tokens.

**Tie-pair invariant:** CVs 3032 ("Payroll HR Administrator") and 3033 ("HR Payroll Administrator") share the same token set `{payroll, hr, administrator}`. Because bag-of-words summation is commutative, both titles produce the **identical** normalized embedding, guaranteeing identical `title_score` vs JD-6 and thus identical `final_score`. Tie is broken by `ORDER BY final_score DESC, cv_id ASC` → 3032 ranks before 3033.
