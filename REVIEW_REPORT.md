# Student Success Coach Project Review

## Executive Summary

**Overall Score: 60 / 100**

- **Milestones Achieved:** 1 / 9 (M5)
- **Milestones Partially Achieved:** 5 / 9 (M1, M4, M6, M8, M9)
- **Milestones Not Achieved:** 3 / 9 (M2, M3, M7)

**Overall Verdict: Needs Improvement** (50 ≤ 60 < 75)

The project demonstrates a working end-to-end flow (student chat → memory → signals → coach planner → calendar) and a genuinely strong memory layer. However, several **mandated learning objectives were bypassed with shortcuts**: the morning planner and re-planner are single LLM calls instead of a **LangGraph StateGraph** / **LangChain Chain** (Orchestrator-Workers absent), student academic data is **pre-injected into the prompt instead of fetched via per-message Tool Calling**, the RAG corpus is **platform/product docs instead of course/study content**, there is **no Concern Resolution Agent** and **no manager notification**, and the **post-session "chain" / briefing "chain" are actually agents**, not chains. A one-character typo (`Non` instead of `None`) currently crashes the app at startup.

---

## Milestone 1 Review — Basic conversation

**Status: PARTIALLY ACHIEVED**

### Evidence
- Conversation Agent built with a LangGraph ReAct agent via `create_agent(...)` in `app/services/student_chat_service.py` (`chatResponse`, lines 225–237). This is acceptable as the mandated ReAct pattern.
- Working Streamlit student chat loop in `streamlit_pages/student_chat_ui.py` (chat history render + `st.chat_input`).

### Missing Functionality
- **No streaming to the UI.** `chatResponse` uses `agent.invoke(...)` and returns the final text; `student_chat_ui.py` does `stream = chatResponse(...)` then `st.write(stream)` — there is no token streaming.
- **No single `get_llm()` factory.** `init_chat_model(...)` is instantiated independently in `student_chat_service.py`, `coach_chat_service.py`, and `mem0_upload_service.py`. There is no `config/llm.py`.

### Recommended Approach Violations
- LLM access is not centralised through one `get_llm()` factory (canonical tech-stack requirement).
- Streaming on the Conversation Agent is required and absent.

### Severity
- Critical: `streamlit_app.py` line 15 sets `st.session_state.student_id = Non` (NameError — should be `None`). This crashes the app on first load. Reported under Functional Gaps.
- Major: no streaming, no `get_llm()` factory.

---

## Milestone 2 Review — Student data in the conversation

**Status: NOT ACHIEVED**

### Evidence
- Real student data is read from Google Sheets in `app/services/google_sheet_service.py` (`googleStudentData`, lines 76–105) across all worksheets, filtered by `student_id`.

### Missing Functionality
- **No per-message Tool Calling for student data.** The conversation agent's tools are only `search_knowledge_base` and `retrieve_memories`. Academic data (scores, attendance, exams) is fetched **once** at profile-save time and **baked into the system prompt** via `build_system_prompt(...)` (`student_chat_service.py`, lines 14–22). The LLM never decides per message to fetch data — the core M2 learning objective (Tool Calling) is bypassed.
- **No attention-highlighting.** Nothing instructs or implements callouts for a dropping score, low attendance, or an upcoming exam; raw data is dumped into the prompt as `{student_data}`.
- No `data/` CSV fallback exists.

### Recommended Approach Violations
- Data injected into the prompt instead of fetched via a Sheets tool the agent calls per message.

### Severity
- Major: tool-calling decision bypassed; no attention-highlighting.

---

## Milestone 3 Review — Questions answered from knowledge base

**Status: NOT ACHIEVED**

### Evidence
- ChromaDB indexer + retriever implemented and persisted in `chroma_db/chroma_client.py`: `upload_chromadb()` (indexer) and `search_knowledge_base()` (retriever), `persist_directory="./chroma_data"`. Markdown header + recursive chunking is sensible.

### Missing Functionality / Wrong Corpus
- **Wrong knowledge-base corpus.** `RAG_Document.md` is **"Product Features"** — platform/portal documentation (Login, Home Page, My Journey, Growth Cycles, Course Exams, Certificates, Placements). The milestone requires **course/study content** (e.g. ML/DSA notes for Arjun STU001). Per the scoring rubric, the wrong data source scores 0 on grounding.

### Recommended Approach Violations
- **RAG is not wired only into the Conversation Agent.** `search_knowledge_base` is also given to the Coach agent (`coach_chat_service.py`, line 18). M3 requires RAG only on the Conversation Agent.

### Severity
- Major: wrong corpus; RAG leaked into coach agent.

---

## Milestone 4 Review — Session is stored after it ends

**Status: PARTIALLY ACHIEVED**

### Evidence
- "End Session" action: `streamlit_pages/student_chat_ui.py` sidebar "🧹 Clear Chat" button (under an "End Session" header) calls `session_summary()` then `googleSummaryUpdate(summary)`.
- Mem0 persistence via `add`: factual facts in `auto_save_factual_memories()` and the summary in `session_summary()` (`mem0_upload_service.py`, lines 49–52, 83–87).
- `flag → Sheets`: `googleSummaryUpdate(...)` writes the signal to the `signal_sheet` tab (`google_sheet_service.py`, lines 108–218).

### Missing Functionality
- None of the four core steps are missing functionally.

### Recommended Approach Violations
- **Not a LangChain Post-Session Chain.** The pipeline is plain Python orchestration; `call_llm` even builds a `create_agent` (an agent), not an LCEL chain. The fixed-step chain pattern (`extract → Mem0 → flag → Sheets`) is not expressed as a LangChain Chain.
- No `students/<id>/sessions/*.json` audit archive is written.

### Severity
- Major: chain approach bypassed.

---

## Milestone 5 Review — AI knows the student's history

**Status: ACHIEVED**

### Evidence
- A new session loads history from Mem0: `retrieve_profile_memories()` (`mem0_retrieval_service.py`, lines 97–117) is called in `student_details.py` at profile setup and injected into the system prompt (factual memory loaded at conversation startup).
- **Two memory types, both populated and separated at storage:**
  - Factual memories — `auto_save_factual_memories()` adds discrete facts via `mem0_client.add(...)`.
  - Session summaries — `session_summary()` adds with `metadata={"category": "session_summaries"}`.
- Mem0 custom categories + custom instructions explicitly define the factual-vs-summary split (`mem0_setup()`).
- Per-user isolation via `user_id=STUDENT_ID` / `filters={"user_id": ...}`.

### Missing Functionality
- Minor: `retrieve_profile_memories()` does not filter by category, so a factual-memory load can also surface summaries — the separation is clean at write time but blurred at read time.

### Recommended Approach Violations
- None material.

### Severity
- Minor: retrieval-side category filtering.

---

## Milestone 6 Review — Signals detected and coach alerted

**Status: PARTIALLY ACHIEVED**

### Evidence
- A signal is written after every session via `googleSummaryUpdate(...)` on End Session.
- Severity **and** urgency are LLM-assessed (`SESSION_SUMMARY_PROMPT` produces `severity`, `urgency`, `severity_score`, `urgency_score`).
- Persisted to `signal_sheet` with `severity`, `urgency`, `actioned` columns (row built in `google_sheet_service.py`, lines 193–217). Duplicate-signal accumulation via `merge_signals_with_llm`.

### Missing Functionality
- **No Concern Resolution Agent.** There is no `concern_resolution_agent.py` and no LangGraph ReAct deeper-reasoning chain triggered on serious signals.
- **No manager notification.** Critical severity does not auto-notify the student's manager with a contextual summary.

### Recommended Approach Violations
- Multi-step orchestration (flagging → concern-resolution agent) is absent.

### Severity
- Major: no concern-resolution agent; no critical-severity manager alert.

---

## Milestone 7 Review — Daily plan generated from signals

**Status: NOT ACHIEVED** (hard rule: planner is not a LangGraph StateGraph)

### Evidence
- Coach-triggered structured day with session type + reason and defer-to-tomorrow with reason: `streamlit_pages/coach_ui.py` "Generate My Day" → `call_llm(COACH_DAILY_PLAN_PROMPT, ...)` returns `today[]` (session_type, reason) and `deferred[]` (reason).
- Coach-account calendar invites: `create_google_calendar_events(today)` on "Confirm Plan" (`google_calendar_service.py`).

### Missing Functionality
- **Plan is never written to `runtime/daily_plan.md`** — it lives only in `st.session_state.plan`.

### Recommended Approach Violations
- **Not a LangGraph StateGraph.** The planner is a **single LLM call** producing JSON — no fixed nodes, no shared state, nothing streamed per node. This is the documented hard-rule violation that forces NOT ACHIEVED.
- **No Orchestrator-Workers.** The single call reads raw `signal_sheet` data directly; there are no sub-agents and no orchestrator that delegates and synthesises.

### Severity
- Critical (learning objective): StateGraph + Orchestrator-Workers bypassed.

---

## Milestone 8 Review — Pre-meeting brief on any student

**Status: PARTIALLY ACHIEVED**

### Evidence
- Coach can request a brief per student: "Get Brief" button → `show_student_brief(student_id)` (`coach_ui.py`, lines 19–59), which produces the four required sections (Current Situation / What's Changed / Open Concerns / Conversation Starters) via prompt.

### Missing Functionality
- **The brief does not draw from Mem0.** `coachChatResponse` only has tools `search_knowledge_base` and `get_all_sheet_data` (`coach_chat_service.py`). There is **no Mem0 access** for the coach, so the brief cannot use the factual memory or session summaries built in M5 — despite the prompt claiming to.

### Recommended Approach Violations
- **Not a LangChain Chain.** The briefing is generated by a ReAct agent (`create_agent`), not the mandated `load data → one LLM call → markdown` chain (`agents/briefing_agent.py` does not exist).

### Severity
- Major: no Mem0 in the brief; chain approach bypassed.

---

## Milestone 9 Review — Serious concern updates the plan automatically

**Status: PARTIALLY ACHIEVED**

### Evidence
- New critical/escalating signals raise a replan alert: `should_create_replan_alert` + `create_replan_alert` write to a `replan_alerts` tab (`replan_alerts.py`). Coach View auto-refreshes (`st_autorefresh`), surfaces "N student update(s) may affect the current plan", and offers a "Refresh Plan" button.
- Each change carries a reason (`changes[]`) and a coach-facing `summary` is shown.
- **Human-in-the-loop conflict handling is present and correct:** `COACH_DAILY_PLAN_PROMPT` instructs the model **not** to auto-decide two-critical-one-slot cases; `conflicts[]` + `coach_review_required` are surfaced in the UI ("Coach Review Required").

### Missing Functionality
- **No `runtime/daily_plan.md`** is loaded or rewritten.

### Recommended Approach Violations
- **Not a LangChain Re-planning Chain, and the plan is regenerated from scratch** rather than loading and rewriting the existing `daily_plan.md`. It re-runs the full planner prompt over all signals. The re-plan is also **button-triggered**, not automatic.

### Severity
- Major: regenerate-from-scratch instead of load+rewrite; not a chain; no `daily_plan.md`.

---

## Functional Gaps Across Entire Project

### Critical
- **App crashes on startup:** `streamlit_app.py` line 15 — `st.session_state.student_id = Non` (NameError; must be `None`). The app cannot launch as committed.
- **Morning Planner (M7) and Re-planner (M9) are single LLM calls**, not a LangGraph StateGraph / LangChain Chain — two core learning objectives bypassed; no Orchestrator-Workers.

### Major
- **No per-message Tool Calling for student academic data (M2)** — data is prompt-injected.
- **Wrong RAG corpus (M3)** — platform/product docs instead of course/study content; RAG also exposed to the coach agent.
- **No Concern Resolution Agent and no critical-severity manager notification (M6).**
- **Coach brief (M8) has no Mem0 access** — cannot use M5 memory.
- **Post-session (M4) and briefing (M8) "chains" are agents**, not LangChain Chains.
- **No `runtime/daily_plan.md` persistence (M7/M9).**

### Minor
- No streaming on the Conversation Agent (M1).
- `retrieve_profile_memories` does not filter by category, blurring factual vs summary at read time (M5).
- No `students/<id>/sessions/*.json` audit archive.
- Empty `README.md`; no `.env.example`.

---

## Security Findings

- **No hardcoded secrets** — all read from env/`.env` (`OPENAI`, `MEM0_API_KEY`, `GOOGLE_CREDENTIALS`, `GOOGLE_SPREADSHEET_ID`, `CALENDAR_ID`). ✅
- **No secrets committed** — `.env` and `credentials.json` exist locally but are git-ignored and not tracked (verified against `git ls-files` and history). ✅
- **No unsafe execution of raw user input.** ✅
- **No secret values leaked via logs.** Note (minor, non-scoring): `coach_chat_ui.py` prints `st.code(traceback.format_exc())` to the UI on error — fine for a demo, but trim stack traces before production.

No critical security issues.

---

## Repository Structure & Hygiene Feedback

The repo does **not** follow the mandated layout (`config/`, `agents/`, `planner/`, `memory/`, `rag/`, `tools/`, `ui/`, `scripts/`, `data/`, `runtime/`). Responsibilities are spread across `app/services/`, `chroma_db/`, and `streamlit_pages/`.

### Expected Structure — Present / Missing
| Expected | Status | Notes |
| --- | --- | --- |
| `config/llm.py` `get_llm()` factory | ❌ Missing | LLM created ad-hoc in 3 files (M1 violation) |
| `agents/conversation_agent.py` (ReAct) | ⚠️ Present elsewhere | `app/services/student_chat_service.py` |
| `agents/concern_resolution_agent.py` (ReAct) | ❌ Missing | M6 deep reasoning absent |
| `agents/post_session_chain.py` (Chain) | ❌ Missing | M4 is plain functions/agent |
| `agents/briefing_agent.py` (Chain) | ❌ Missing | M8 is an agent |
| `agents/replanning_agent.py` (Chain) | ❌ Missing | M9 is a single LLM call |
| `planner/orchestrator.py` (StateGraph) | ❌ Missing | M7 is a single LLM call |
| `memory/mem0_client.py` | ⚠️ Present elsewhere | `app/services/mem0_*.py` |
| `rag/retriever.py` + `indexer.py` | ⚠️ Present elsewhere | `chroma_db/chroma_client.py` (both) |
| `tools/sheets_client.py` + `calendar_tools.py` | ⚠️ Present elsewhere | `app/services/google_*_service.py` |
| `ui/student_view.py` + `coach_view.py` | ⚠️ Present elsewhere | `streamlit_pages/*` |
| `scripts/setup_google_auth.py` | ❌ Missing | uses a service account instead of OAuth flow |
| `data/` CSV fallback | ❌ Missing | no Sheets fallback |
| `runtime/daily_plan.md` | ❌ Missing | M7/M9 never persist the plan |
| `students/<id>/sessions/*.json` | ❌ Missing | no audit archive |
| `requirements.txt` / `pyproject.toml` | ✅ Present | `pyproject.toml` + `uv.lock` |

### Committed-File Hygiene
- `.gitignore` **exists** and covers `__pycache__/`, `*.py[oc]`, `.venv`, `.env`, `credentials.json` (good coverage of the critical categories).
- **No** secrets, `venv/`, `__pycache__/`, or OS junk are tracked. ✅
- ⚠️ **Committed generated vector index:** `chroma_data/chroma.sqlite3` and `chroma_data/<uuid>/*.bin` are tracked. This generated ChromaDB index should normally be git-ignored and rebuilt via the indexer (Minor — judgement call; acceptable only if intentionally seeded for the demo).
- `.gitignore` does not list `chroma_data/` or `.DS_Store`.

### General Notes
- Code is readable and the service split is reasonable, but naming is inconsistent (`googleSheetData` vs `get_all_sheet_data`; `chatResponse` camelCase vs PEP8). `README.md` is empty and there is no `.env.example`. The `Non` typo and a UI traceback dump indicate the entry point was not smoke-tested before commit.

---

## Tabular Report

| Milestone | Status | Highlight |
| --- | --- | --- |
| M1 — Basic conversation | PARTIALLY | No-streaming |
| M2 — Student data in chat | NOT ACHIEVED | Prompt-injected |
| M3 — Knowledge base RAG | NOT ACHIEVED | Wrong-corpus |
| M4 — Session stored | PARTIALLY | Not-a-chain |
| M5 — Knows history | ACHIEVED | Mem0-solid |
| M6 — Signals + alert | PARTIALLY | No-manager-notify |
| M7 — Daily plan | NOT ACHIEVED | No-StateGraph |
| M8 — Pre-meeting brief | PARTIALLY | No-Mem0 |
| M9 — Auto re-plan | PARTIALLY | Regenerated |

---

## Scoring Breakdown (reproducible)

### Per-milestone MUSTs

| Milestone | MUSTs (✓/✗) | Points |
| --- | --- | --- |
| **M1** (4 × 2.25) | ReAct ✓ · working chat ✓ · `get_llm()` factory ✗ · streaming ✗ | **4.5** |
| **M2** (3 × 3) | per-msg tool calling ✗ · reads real Sheets data ✓ · highlights attention ✗ | **3.0** |
| **M3** (3 × 3) | indexer+retriever persisted ✓ · RAG only in Conversation Agent ✗ · grounded in correct course corpus ✗ | **3.0** |
| **M4** (4 × 2.25) | End-Session trigger ✓ · Mem0 `add` persist ✓ · LangChain Post-Session Chain ✗ · flag→`signal_sheet` ✓ | **6.75** |
| **M5** (3 × 3) | new session loads Mem0 ✓ · two memory types separate+populated ✓ · factual loaded at startup ✓ | **9.0** |
| **M6** (5 × 1.8) | signal every session ✓ · severity+urgency LLM ✓ · persisted to `signal_sheet` ✓ · Concern Resolution Agent ✗ · critical→manager ✗ | **5.4** |
| **M7** (6 × 1.5) | session type+reason ✓ · defer+reason ✓ · coach calendar invites ✓ · StateGraph ✗ · Orchestrator-Workers ✗ · `daily_plan.md` ✗ | **4.5** |
| **M8** (4 × 2.25) | per-student brief ✓ · LangChain Chain ✗ · all four parts ✓ · draws from Mem0 ✗ | **4.5** |
| **M9** (5 × 1.8) | auto-updates existing plan ✗ · change+reason ✓ · conflict surfaced to coach ✓ · Chain rewriting `daily_plan.md` ✗ · change summary ✓ | **5.4** |
| **Milestones subtotal** | | **46.05 / 81** |

### Security (6)
- No hardcoded secrets (2) ✓ · not committed/git-ignored (2) ✓ · no unsafe exec (1) ✓ · no secret value leaked (1) ✓ → **6 / 6**

### Repository structure (7)
- `get_llm()` factory ✗ (0) · agents present-in-form: conversation only (0.3) · planner StateGraph ✗ (0) · mem0 client (0.5) · RAG retriever+indexer (0.5) · tools sheets+calendar (0.5) · UI student+coach (0.5) · `setup_google_auth.py` ✗ (0) · `data/` ✗ (0) · `daily_plan.md` ✗ (0) · session archive ✗ (0) · deps file (0.5) → **3.3 / 7**

### Repository hygiene (6)
- `.gitignore` covers required categories (2) ✓ · tracked tree free of caches/venv/secrets/junk (2) ✓ (chroma index noted, not auto-failed) · deps declared (1) ✓ · cleanliness: `Non` typo + UI traceback + empty README + no `.env.example` (1) ✗ → **5 / 6**

### Total
**46.05 + 6 + 3.3 + 5 = 60.35 → 60 / 100**

---

## Final Verdict

**Needs Improvement (60/100).** The trainee built a coherent, demoable system and clearly understood **Memory (Mem0)** — M5 is the standout and the only fully achieved milestone. The system also wires up Sheets, Calendar, signals, and a coach planner with genuine human-in-the-loop conflict handling.

However, the most important **learning objectives were bypassed with shortcuts**, which is what holds the score back:

Must be completed before this can be considered done:
1. **Fix the startup crash** — `Non` → `None` in `streamlit_app.py` (blocks the entire app).
2. **Rebuild the Morning Planner as a LangGraph StateGraph with Orchestrator-Workers** (sub-agents fetch data; orchestrator synthesises) and write `runtime/daily_plan.md` (M7).
3. **Make the Re-planner a LangChain Chain that loads and rewrites the existing `daily_plan.md`** instead of regenerating it; trigger it automatically (M9).
4. **Convert student academic data to per-message Tool Calling** (a Sheets tool the agent calls), and add attention-highlighting (M2).
5. **Replace the RAG corpus with course/study content** and restrict RAG to the Conversation Agent (M3).
6. **Add a Concern Resolution Agent (LangGraph ReAct) and critical-severity manager notification** (M6).
7. **Give the coach brief Mem0 access** and express post-session/briefing as real **LangChain Chains** (M4, M8).
8. **Add a single `get_llm()` factory and stream Conversation Agent responses** (M1).
9. Housekeeping: git-ignore `chroma_data/`, add a populated `README.md` and `.env.example`.
