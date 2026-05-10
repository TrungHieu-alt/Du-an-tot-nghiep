<div align="center">
<img width="1200" height="475" alt="GHBanner" src="https://github.com/user-attachments/assets/0aa67016-6eaf-458a-adb2-6e31a0763ed6" />
</div>

# Run and deploy your AI Studio app

This contains everything you need to run your app locally.

View your app in AI Studio: https://ai.studio/apps/drive/1il1OBAX46PJ-OxGjNkU_cOaMP95KKwIK

## Run Locally

**Prerequisites:**  Node.js


1. Install dependencies:
   `npm install`
2. Set the `GEMINI_API_KEY` in [.env.local](.env.local) to your Gemini API key
3. Run the app:
   `npm run dev`

---

## V2 Search & Matching (prototype)

The frontend ships with a parallel **V2** flow backed by the Postgres + pgvector
prototype API. It coexists with the legacy v1 mock pages (`/jobs`, `/candidates`)
which now show a deprecation banner pointing here.

### User flow

```
Home search bar  ──►  /v2/search?q=&type=job|cv&location=&job_type=&seniority=
                              │
                              │  click result card
                              ▼
                       /v2/jobs/:id   or   /v2/cvs/:id    (full detail)
                              │
                              │  click "Run Matching V2"
                              ▼
                       /v2/matching?anchor=job|cv&id=:id
                              │
                              ▼
                       Top-K matches with score breakdown
```

### Pages & components

| Path | Component | Notes |
|---|---|---|
| `/` | `pages/Home.tsx` | Search bar redirects to `/v2/search` (toggle Job/CV persisted in `localStorage:v2_search_type`) |
| `/v2/search` | `pages/V2Search.tsx` | Sticky filter bar + sidebar chips + result grid. Score < 0.2 collapses behind "Xem thêm" button |
| `/v2/jobs/:id` | `pages/V2JobDetail.tsx` | Full detail with sticky "Run Matching V2" CTA |
| `/v2/cvs/:id` | `pages/V2CvDetail.tsx` | Same shape for CV |
| `/v2/matching` | `pages/V2Matching.tsx` | 3-column workbench; supports `?anchor=&id=` deep-link |

### Search internals

* **Endpoint**: `POST /api/v2/prototype/catalog/{jobs|cvs}/search`
* **Embedder**: hash-based deterministic (SHA-256 per token, L2 normalize) — same
  algorithm that seeded `job_embeddings_v2.emb_title/emb_skills`. Pure Python,
  no model download, no GPU. Source: `backend/v2_search/embedder.py`.
* **Score blend**: `(1 - blend_skills) * cosine(emb_title) + blend_skills * cosine(emb_skills)`,
  default `blend_skills = 0.3`.
* **Limitations**:
  * Token-only matching: gõ `"java"` không match `"javascript"`.
  * No synonym understanding: `"DevOps"` ≠ `"infra cloud"`.
  * Score is cosine-blend in hash space, **not** a calibrated relevance %.

### Filters supported

| Filter | Values |
|---|---|
| `location` | `ha_noi`, `tp_hcm`, `da_nang` |
| `job_type` | `remote`, `fulltime`, `parttime` |
| `seniority` | `intern`, `fresher`, `junior`, `mid`, `senior`, `lead` |

### Routing note

`App.tsx` uses `BrowserRouter`. Deep-links work: paste
`http://localhost:5173/v2/search?q=backend&type=job&location=ha_noi` and the
page hydrates from URL. F5 / back / forward all behave like normal SPA.
