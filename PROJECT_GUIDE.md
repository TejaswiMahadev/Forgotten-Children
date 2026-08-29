# Forgotten Children of Aadhaar — Project Guide

> A working guide to what this repo is, how to run it, how every metric is actually
> computed, and what's broken. Written after reading all 3,279 lines of source and
> executing the pipeline end-to-end against synthetic UIDAI-shaped data.
>
> **Status:** findings F1, F2, F3 and F10 are fixed and re-verified; F9 is partly
> mitigated. The AI layer has been migrated from Vertex AI / Gemini to **OpenRouter**
> (see §4.3). Everything else below is outstanding.
>
> Verified on: Python 3.14.7 · pandas 3.0.5 · plotly 7.0.0 · dash 4.4.1 · numpy 2.5.1

---

## 1. What this project is

A **Dash analytics dashboard** for UIDAI Hackathon 2026 (Team `UIDAI_3133`).

The thesis: children aged 5–17 must complete a mandatory Aadhaar biometric update.
Missed updates are invisible until an authentication failure years later. This project
estimates, per PIN code, how many children *should* have updated but haven't — the
**biometric update gap** — then ranks PIN codes for intervention and attaches a
model-generated explanation to each chart hover.

Everything runs on **aggregated counts only**. No PII, no individual records. That
privacy claim holds up in the code.

**What it is not:** it is not a validated statistical model. The central quantity
(`total_expected`) is a hand-tuned heuristic, and as written it is dominated by an
artifact of the input date range — see [§6](#6-findings).

---

## 2. Repository map

```
Forgotten-Children-main/
├── dash_app.py                     # 496 lines — the entire application
├── requirements.txt
├── README.md                       # concept overview (no run instructions)
├── SUBMISSION_UIDAI_3133.md        # hackathon submission document
├── assets/
│   └── dash_style.css              # dark "neon" theme
└── src/
    ├── data_loader.py              # glob CSVs -> validate -> clean
    ├── data_validator.py           # schema / null / negative / date checks
    ├── data_cleaner.py             # dates, PIN codes, geography, dedupe
    ├── data_integrator.py          # merge 3 datasets on pincode
    ├── processor.py                # [!] broken standalone script
    ├── insight_engine.py           # [!] dead code (unused AI path)
    ├── visualizations.py           # 13 Plotly builders (5 used)
    ├── analytics/
    │   ├── gap_calculator.py       # [OK] core metric
    │   ├── priority_scorer.py      # [OK] ranking + van estimate
    │   ├── forecasting.py          # [OK] horizon risk
    │   ├── anomaly_detector.py     # [OK] 3 rule-based detectors
    │   ├── temporal_analyzer.py    # [OK] monthly / seasonal trend
    │   ├── report_generator.py     # [OK] priority table
    │   ├── ai_analyzer.py          # [OK] OpenRouter narrative layer
    │   ├── biometrics.py           # [!] dead code
    │   ├── demographics.py         # [!] dead code
    │   ├── enrollment.py           # [!] dead code
    │   └── migration.py            # [!] dead code
    └── intelligence/
        ├── anomaly_detector.py     # [!] dead code
        ├── forecasting.py          # [!] dead code
        └── fusion.py               # [!] dead code
```

`[OK]` = reachable from the dashboard. `[!]` = never imported by anything.
**Roughly 1,200 of 3,279 lines (≈37%) are unreachable.**

---

## 3. Architecture

```
Aadhar_Enrollment_Data/*.csv ─┐
Aadhar_Biometric_Data/*.csv  ─┼─► UIDAIDataLoader ─► DataValidator ─► DataCleaner
Aadhar_Demographic_Data/*.csv─┘        (glob)         (report only)    (mutating)
                                                                          │
                                        ┌─────────────────────────────────┘
                                        ▼
                              DataIntegrator.integrate()
                              groupby(pincode) — TIME IS DROPPED HERE
                                        │
              ┌─────────────────────────┼──────────────────────────┐
              ▼                         ▼                          ▼
      GapCalculator            ForecastingEngine           AnomalyDetector
   expected vs actual          horizon risk (3yr)          3 rule-based flags
              │
              ▼
      PriorityScorer  ──► MinMaxScaler -> weighted score -> rank -> van estimate
              │
              ▼
      dash_app.load_all_data()  ──► dcc.Store (browser JSON)
              │
              ▼
      populate_dashboard()  ──► KPIs · map · table · 4 charts · anomaly feed
              │
              ▼
      hoverData callbacks  ──► AIAnalyzer (OpenRouter, one call per hover)
```

Two things worth noting about this shape:

1. **`DataIntegrator` collapses the time axis.** It does `groupby(['pincode', ...]).sum()`
   over the entire history. Every downstream metric — gap, risk level, priority, van
   count, anomalies — is therefore a single all-time number per PIN, not a time series.
   Only the trend line chart retains dates. The "time-series analysis" framing in the
   README describes one chart, not the analytical core.

2. **The merge is `how='left'` from enrollment.** PIN codes that appear in the biometric
   or demographic files but not in enrollment are silently dropped from all analysis.

---

## 4. Getting it running

### 4.1 The data is not in the repo

This is the first blocker. `UIDAIDataLoader` globs three directories that **do not
exist** in this checkout and are not documented or downloadable from anywhere in the
repo:

| Directory | Required columns |
| :--- | :--- |
| `Aadhar_Enrollment_Data/` | `date, state, district, pincode, age_0_5, age_5_17, age_18_greater` |
| `Aadhar_Biometric_Data/` | `date, state, district, pincode, bio_age_5_17, bio_age_17_` |
| `Aadhar_Demographic_Data/` | `date, state, district, pincode, demo_age_5_17, demo_age_17_` |

Place them at the repo root, alongside `dash_app.py`. Any number of `*.csv` files per
directory; the loader concatenates them all and tags each row with a `file_district`
column taken from the filename.

Note the trailing underscore in `bio_age_17_` and `demo_age_17_` — that is the literal
column name the code expects, not a typo in this guide.

### 4.2 Environment

```bash
python -m venv .venv
.venv\Scripts\activate          # PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

`requirements.txt` pins no versions, so a fresh install today gives you plotly 7 /
pandas 3. That used to crash the map (**F1**); the code now handles both generations, and
the pipeline is verified on plotly 7.0.0 / pandas 3.0.5. Pinning is still worth doing —
see fix **10** — but it is no longer a prerequisite for running.

### 4.3 OpenRouter credentials (optional)

The AI layer runs on **OpenRouter**, not Vertex AI. The dashboard renders fully without
it; only the hover overlays go dark. Copy `.env.example` to `.env` and fill in:

```env
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_MODEL=minimax/minimax-m3:free
```

`AIAnalyzer` reads both at construction. No key means `enabled = False` and hovers return
`"AI Insight Unavailable"` — the dashboard is otherwise unaffected.

OpenRouter's chat-completions endpoint is OpenAI-compatible, so this needs **no SDK**;
the module talks to it over stdlib `urllib`. `google-generativeai` and
`google-cloud-aiplatform` have been dropped from `requirements.txt`.

**Free-tier accounts matter here.** They can only call model ids ending in `:free`, and
are capped at a few dozen requests per day. `minimax/minimax-m3:free` is the default
because it answers the point-insight prompt in ~4s without leaking a reasoning trace into
the output, which several other free models do. To use a paid model id, add credit to the
OpenRouter account first.

Because every hover costs a request (**F9**), `ai_analyzer.py` enforces
`MAX_CALLS_PER_PROCESS = 40` per run as a backstop against burning the daily quota in one
mouse sweep. Raise it once F9 is properly fixed.

### 4.4 Launch

```bash
python dash_app.py
```

Opens on <http://127.0.0.1:8050>. `debug=True` is hardcoded — fine for a demo, not for
anything exposed.

### 4.5 Reading the dashboard

| Panel | Source |
| :--- | :--- |
| 4 top KPIs | `GapCalculator.get_summary_stats` + forecast sum |
| Urgency / Awareness / Van KPIs | means over `priority_df` |
| Geographic Risk Distribution | `create_geographic_mapbox` — **click a point** for the tactical scorecard |
| Priority Action List | `ReportGenerator.get_priority_list`, top 10 |
| Temporal Update Trends | `TemporalAnalyzer.analyze_trends` monthly sum |
| Risk Hierarchy sunburst | state -> district -> risk, area = gap |
| Anomaly Detection Feed | top 5 rows of `AnomalyDetector` output |
| District Performance Matrix | rate vs. gap scatter with median quadrant lines |
| Gap Hierarchy TreeMap | All India -> district -> risk -> PIN |

Hovering any chart fires an OpenRouter call. Clicking a map point is the only other
interaction.

---

## 5. What every metric actually computes

Formulas below are transcribed from the code, not from the submission document.
Where the two disagree, the code is authoritative and the disagreement is flagged.

### Baseline Gap — `gap_calculator.py:24-40`

```python
total_expected      = age_0_5_summed_over_all_time * 12.0
# fallback if that lands below observed updates:
total_expected      = bio_age_5_17 * 1.2
actual_bio_updates  = bio_age_5_17
update_gap          = total_expected - actual_bio_updates
update_rate         = actual / expected * 100      # clipped to [0, 100]
gap_percentage      = 100 - update_rate
```

Risk bands: `Critical >= 70%`, `High >= 50%`, `Medium >= 30%`, else `Low`.

The `12.0` is documented in the code as "a stable population plus the PRD's *forgotten*
cohort multiplier" — nominally 12 years of the 5–17 window against a 5-year 0–5 window.
See **F4** for why this doesn't survive contact with the actual input.

### System Efficiency

`sum(actual) / sum(expected) * 100` across all PIN codes. Reported as 79.1% in the
submission.

### Awareness / Saturation Index — `gap_calculator.py:57`

```python
saturation_index = bio_age_5_17 / max(demo_age_5_17, 1) * 100   # clipped to [0, 100]
```

The share of demographic-updating families who also updated biometrics. The clip at 100
means any PIN where biometric >= demographic reads as a flat 100% — in the synthetic run,
values bunched at 88–99%, so the KPI has very little dynamic range.

### Priority Score — `priority_scorer.py:26-53`

Min-max normalize `update_gap`, `gap_percentage`, `total_expected` across all PINs, then:

```python
priority_score = (0.4*gap_norm + 0.4*gap_pct_norm + 0.2*volume_norm) * 100
```

Rank descending. Action: rank <= 10 -> `Deploy Unit`; else Critical -> `Intensive Drive`;
High -> `Awareness Drive`; else `Monitor`.

### Van estimate & Urgency — `priority_scorer.py:55-70`

```python
estimated_vans_needed = update_gap / (50 * 180)          # 50 children/day, 180 days
urgency_index         = priority_score * (1 + vans/10)   # clipped to [0, 100]
```

### Horizon Risk — `analytics/forecasting.py`

```python
recent            = enrollment where date >= 2025-12-31 minus 5 years   # hardcoded date
predicted_updates = recent_age_0_5_sum * current_update_rate / 100
predicted_gap     = recent_age_0_5_sum - predicted_updates
conf_low/high     = predicted_gap * 0.9 / 1.1
```

### Anomalies — `analytics/anomaly_detector.py`

| Type | Rule | Severity |
| :--- | :--- | :--- |
| Bio-Demo Mismatch | `demo > 2*bio` and `demo > 50` | High |
| Statistical Outlier | `update_rate < Q1 - 1.5*IQR` | Critical |
| Potential High In-Migration | `bio_age_5_17 > age_0_5` and `age_0_5 > 0` | Medium |

---

## 6. Findings

Severity: **P0** breaks the app · **P1** distorts the numbers · **P2** quality/cost.
"Reproduced" means I triggered it by executing the code.

### F1 · P0 · The map crashes on any current Plotly — *reproduced* — **FIXED**

[`visualizations.py:57`](src/visualizations.py#L57) calls `px.scatter_mapbox` and
`mapbox_style="carto-darkmatter"`. Both were deprecated in Plotly 5.24 and **removed in
Plotly 6.0**. On the installed Plotly 7.0.0:

```
AttributeError: module 'plotly.express' has no attribute 'scatter_mapbox'
```

Because `create_geographic_mapbox` is called inside `populate_dashboard` — the single
callback that fills twelve outputs — this one exception blanks the *entire* dashboard,
not just the map. Nothing renders.

**Fixed:** `create_geographic_mapbox` now resolves `px.scatter_map` at call time and
falls back to `px.scatter_mapbox`, keying the layout style argument to match. Renders on
both Plotly 5 and Plotly 7.

### F2 · P0 · Empty biometric data raises a tuple-unpacking error — *reproduced* — **FIXED**

`TemporalAnalyzer.analyze_trends` returns **three** values on the happy path but only
**two** on the empty guard ([`temporal_analyzer.py:16`](src/analytics/temporal_analyzer.py#L16)).
`dash_app.py:60` unpacks three:

```
ValueError: not enough values to unpack (expected 3, got 2)
```

So a missing or unreadable biometric directory — the exact state of this checkout —
crashes at load rather than degrading.

**Fixed:** the empty guard now returns `pd.DataFrame(), pd.DataFrame(), {}`.

### F3 · P0 · One malformed PIN code kills the whole load — *reproduced* — **FIXED**

[`data_cleaner.py:29`](src/data_cleaner.py#L29):

```python
df['pincode'].apply(lambda x: str(int(float(x))).zfill(6) if pd.notnull(x) else x)
```

A non-numeric PIN raises `ValueError: could not convert string to float: 'ABC123'` and
aborts the run. Two further problems in the same line: `int(float(x))` silently truncates
`110059.7` to `110059`, and there is no length check, so a 5- or 7-digit value is
zero-padded or passed through as if valid.

`DataValidator` has the same shape of problem — a non-numeric count column raises
`TypeError: Invalid comparison between dtype=str and int` at
[`data_validator.py:57`](src/data_validator.py#L57) *before* any of its checks can report
the bad data.

**Fixed:** `DataCleaner` now coerces with `pd.to_numeric(..., errors='coerce')`, rejects
non-integral values instead of truncating them, keeps only PINs matching `[1-9]\d{5}`,
and prints a count of what it dropped. Count columns are coerced the same way.
`DataValidator` compares numerically and reports non-numeric values as a warning rather
than raising.

### F4 · P1 · `total_expected` scales with the length of your date range — *reproduced*

This is the most consequential finding, because every headline number depends on it.

`DataIntegrator` sums `age_0_5` across **every row in the dataset** — that is a sum of
monthly enrollment *flows*, not a population *stock*. `GapCalculator` then multiplies
that sum by 12.

Consequence: **feed the same PIN 24 months of data instead of 12 and `total_expected`
doubles**, the gap roughly doubles, and System Efficiency halves. The metric measures
your file's time span as much as it measures exclusion.

In the synthetic run (24 months, ~1000 mean monthly enrollments) this produced
`total_expected` around 350,000 per PIN and update rates of 5–10%, classifying **all four**
PIN codes as Critical. The submission's 79.1% efficiency is not wrong given its inputs —
it is simply not a stable quantity, and it isn't comparable across regions whose files
cover different periods.

**Fix:** derive expected updates from a cohort *stock* — a single period's enrollment, or
a per-year average — and state the cohort assumption explicitly. Whatever you choose,
normalize by the number of months in the window so the metric is span-invariant.

### F5 · P1 · The forecast uses a different cohort definition than the gap

`ForecastingEngine` builds its eligible base from `recent_enrollments_0_5` — a 5-year
sum with **no ×12 multiplier** — while `GapCalculator` applies ×12 to the all-time sum.
The two "gap" numbers on the dashboard therefore aren't on the same scale, but sit side
by side as "Baseline Gap" and "Horizon Risk" as though they were.

Also in this module:

- `forecast_horizon_years=3` is a parameter that is **never used** in the body. The
  "3-Year Forecast" label is decorative.
- `current_date = pd.Timestamp('2025-12-31')` is hardcoded. The cutoff is frozen; the
  window silently widens as real data ages past that date.
- The ±10% confidence band is a fixed multiplier, not an interval derived from anything.
  Calling it a confidence interval overstates it.

### F6 · P1 · Priority and urgency scores degenerate — *reproduced*

Two independent problems in `priority_scorer.py`:

**Min-max normalization is purely relative.** The lowest-scoring PIN always receives
exactly `0.0`, no matter how bad it is in absolute terms. In the synthetic run Hyderabad
scored `priority_score = 0.0` and `urgency_index = 0.0` while carrying a 255,417-child
gap and a `Critical` risk label — because it happened to be the least-bad of four. Scores
are also not comparable between runs, or between a filtered and unfiltered view.

**Urgency saturates immediately.** `priority_score` is already 0–100, so
`priority_score * (1 + vans/10)` clipped to `[0, 100]` pins to 100 for anything above
~90. Three of four synthetic PINs read exactly `100.0`. The index carries no information
at the top of the range, which is the only range anyone looks at.

The submission document describes urgency as a **0–10** index; the code produces 0–100.

**Fix:** score against fixed absolute thresholds rather than the batch min/max, and let
urgency use a bounded combining function (a weighted geometric mean, or a logistic) that
doesn't clip.

### F7 · P1 · Documented figures don't match the code

| Submission says | Code does |
| :--- | :--- |
| "56 units to close the current gap **within 12 months**" | `gap / (50 × **180 days**)` — a 6-month target |
| "Average Urgency Index (**0–10**)" | clipped to **0–100** |
| "Statistical Modeling (**Prophet/Statsmodels**)" | neither is imported anywhere; forecasting is arithmetic |
| "**Google Vertex AI** (Gemini)" for the narrative layer | **now out of date** — the live layer runs on OpenRouter. The dead `insight_engine.py` still imports the deprecated `google-generativeai` SDK |

Also: `TemporalAnalyzer.calculate_time_to_update` returns
`{"avg_years": 6.2, "median_years": 5.8}` — **hardcoded constants**, labeled in a comment
as "Representative values for Central Delhi." Nothing computes them. The function is
unused by the dashboard, so no displayed number is affected, but it should be deleted
rather than left where a reviewer can find it.

### F8 · P1 · Map coordinates are randomly jittered on every render

`create_geographic_mapbox` assigns each PIN its **district** centroid plus
`random.uniform(-0.05, 0.05)` — unseeded, recomputed on every callback. Points move
between refreshes, and a PIN's plotted position carries no information about where that
PIN actually is.

Worse, districts absent from the 21-entry `district_coords` dictionary fall back to
`[22.9734, 78.6569]` — the geographic centre of India. Scale beyond the four demo states
and every unrecognized district stacks into one meaningless pile in Madhya Pradesh, sized
by summed gap.

**Fix:** ship a PIN-code -> lat/lon table (the India Post directory is public), and seed
the jitter if you keep it.

### F9 · P2 · Every mouse hover is a billed, blocking LLM call — **PARTLY MITIGATED**

Five callbacks bind to Plotly `hoverData`, which fires continuously as the pointer moves
across a chart. Each new point triggers a synchronous chat-completion call to OpenRouter,
inside the request thread.

`AIAnalyzer._insight_cache` only helps on *repeat* hovers of the identical point. Sweeping
a mouse across the treemap can still fire dozens of calls in seconds — and on OpenRouter's
free tier that is the entire daily quota.

**Partly mitigated:** the analyzer now enforces a 30s timeout (a hung provider used to
hang the Dash worker) and a hard `MAX_CALLS_PER_PROCESS = 40` budget, and surfaces both
budget exhaustion and HTTP 429 as readable messages instead of failing opaquely.

**Still to do:** the trigger itself is unchanged. Move it to `clickData`, add a
`dcc.Interval`/debounce, or precompute insights for the top-N points at load. Any of the
three removes the problem properly; the budget cap only stops it being expensive.

### F10 · P2 · No `.gitignore`, and credentials are auto-discovered from the repo root — **FIXED**

`GeminiAnalyzer.__init__` looks for `service-account.json` **in the current working
directory** — the repo root. The repo has no `.gitignore`, so the natural way to make the
AI layer work is to drop a GCP service-account key exactly where `git add .` will commit
it. Same exposure for `.env`.

Nothing is currently leaked — the key isn't in the checkout. This is about the trap the
setup lays for the next person.

**Fixed:** added `.gitignore` (credentials, venvs, `__pycache__/`, `processed_data/`) and
`.env.example` documenting the three variables `GeminiAnalyzer` reads.

### F11 · P2 · `processor.py` cannot run

Three independent breakages in a 29-line file:

- `from data_loader import UIDAIDataLoader` — wrong path, everything else uses
  `from src.data_loader import ...`. `ImportError` on execution.
- Calls `loader.validate_dataset(df, cat)`, a method that **does not exist** on
  `UIDAIDataLoader`.
- `base_path = r'c:\Users\mahad\OneDrive\Desktop\UIDAI'` — a hardcoded path to a
  teammate's machine.

Either fix all three or delete the file.

### F12 · P2 · Dead code and dead dependencies

**~1,200 unreachable lines.** `src/intelligence/` (773 lines, the most sophisticated code
in the repo — rolling z-scores, contextual anomaly classification, trend extrapolation
with confidence bands), all four `src/analytics/{biometrics,demographics,enrollment,migration}.py`
modules, and `src/insight_engine.py` are imported by nothing.

`GeminiAnalyzer.generate_narrative_insights` is likewise never called — no UI element
renders a narrative report — and `ai_prompt_instructions` is assembled in
`load_all_data`, shipped to the browser store, and never read.

8 of 13 functions in `visualizations.py` are unused, including `create_forecast_chart`,
so the forecast is never plotted — only summed into a KPI.

**Dead dependencies:** `streamlit` and `streamlit-folium` are in `requirements.txt` but
there is no Streamlit app in the repo. `folium` is imported at the top of
`visualizations.py` and used only by the unused `create_geographic_map_markers` — so it
is a hard install requirement for a feature nobody can reach. `google-generativeai` and `google-cloud-aiplatform`
have been **removed** from `requirements.txt` as part of the OpenRouter migration; the
dead `insight_engine.py` still imports the former and would now fail on import — one more
reason to delete it.

### F13 · P2 · Smaller items

- **Anomalies double-count.** A single PIN can match two or three rules and appears once
  per match in the concatenated frame. *Reproduced:* one PIN produced two rows. The
  "anomalies detected" count in `ReportGenerator` is a count of *flags*, not of places.
  The dead-code guard `if not anomalies:` at
  [`anomaly_detector.py:50`](src/analytics/anomaly_detector.py#L50) can never be true —
  three frames are always appended.
- **The AI overlay never hides.** Callbacks set `display: block` on hover but nothing
  sets it back to `none`, because Plotly's `hoverData` retains its last value after the
  pointer leaves. The last insight stays pinned over the chart.
- **`text-neon-orange` is undefined.** Used on the anomaly feed header
  ([`dash_app.py:172`](dash_app.py#L172)) but absent from `dash_style.css`. The heading
  renders in the default color.
- **`error_y='conf_high'` is wrong.** Plotly's `error_y` expects a *delta*; passing the
  absolute upper bound draws an error bar roughly twice the size of the bar itself.
  (`create_forecast_chart`, currently unused.)
- **The whole dataset is shipped to the browser.** `load_all_data` puts `enrollment`,
  `biometric`, `demographic`, `integrated`, `gap_df`, `priority_df`, `forecast_df` and
  `anomaly_df` into a `dcc.Store` as JSON. `integrated` is assigned in
  `populate_dashboard` and never used. At national scale this is tens of MB per page load.
  Use `@lru_cache` server-side, or a `dcc.Store` holding only what the callbacks read.
- **The full pipeline re-runs on every page load,** because `update_data` is wired to
  `refresh-btn.n_clicks`, which fires once with `None` on initial render.
- **`.replace(0, 1)` in the saturation denominator** turns "no demographic updates" into
  "one demographic update", producing a 100% awareness score for PINs with no
  demographic signal at all — the opposite of the intended reading.
- **No `__init__.py` anywhere.** It works via namespace packages on Python 3.3+, but
  `dash_app.py` also does a redundant `sys.path.append('src')` alongside
  `from src.x import y`.
- **No tests, no CI, no logging** — `print()` throughout.

---

## 7. Fix order

If you're presenting this, do 1–3. They are about an hour of work and are the difference
between a dashboard that renders and one that doesn't.

| # | Finding | Change |
| :--- | :--- | :--- |
| ~~1~~ | ~~F1~~ | **Done.** `px.scatter_map` with a `scatter_mapbox` fallback. |
| ~~2~~ | ~~F2, F3~~ | **Done.** 3-tuple empty guard; PIN and count coercion in cleaner and validator. |
| ~~3~~ | ~~F10~~ | **Done.** `.gitignore` + `.env.example` added. |
| 4 | F7 | Reconcile the submission doc with the code — 180 days vs. 12 months, 0–10 vs. 0–100, Prophet/Statsmodels. Delete `calculate_time_to_update`. |
| 5 | F4 | Normalize `total_expected` by window length. Be explicit that the cohort factor is a stated assumption, not a measurement. |
| 6 | F9 | Move AI insights to `clickData`. |
| 7 | F6 | Absolute thresholds instead of batch min-max; un-clip urgency. |
| 8 | F8 | Real PIN-code coordinates. |
| 9 | F11, F12 | Delete `processor.py`, `insight_engine.py`, and the unused analytics modules — or wire `src/intelligence/` in, since it's the strongest code here. Drop `streamlit*` from requirements; make `folium` a local import. |
| 10 | — | Pin every version in `requirements.txt`. F1 exists only because nothing was pinned. |

---

## 8. What's genuinely good here

Worth saying, because the findings list is long:

- **The privacy claim is real.** Every operation is on aggregate counts. There is no path
  in this code to an individual record.
- **The framing is the strongest part of the project.** "Measure the unmet obligation,
  not the completed updates" is a genuine reframing, and it's the reason the gap metric
  is interesting despite F4.
- **The layered validate -> clean -> integrate -> analyze structure is right**, and each
  stage is a small, testable, single-purpose class. The bugs are in the details, not the
  architecture.
- **The AI layer is cleanly separated.** Swapping the entire provider from Vertex AI to
  OpenRouter touched one module and three lines of `dash_app.py`, because the analyzer
  exposes a small, stable interface. That boundary paid off.
- **`src/intelligence/` is better code than what's actually running.** Rolling z-scores,
  contextual anomaly classification, and trend extrapolation with derived confidence
  bands would materially strengthen the analysis. It's sitting right there, unwired.
