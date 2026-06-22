# Success Coach AI — Milestone Review Guidelines

These guidelines are the source of truth the reviewer uses to evaluate each milestone. They are derived directly from the project references (build milestones, components & architecture, and the capabilities showcase) and the setup guide.

For every milestone the reviewer must check **two dimensions**:

1. **Feature functionality** — does the milestone actually do what it is supposed to do?
2. **Component & approach usage** — is it built with the required framework / component, in the recommended way (not bypassed with shortcuts)?

A milestone is **ACHIEVED** only when both the functionality is correct *and* the recommended approach is followed. If the functionality works but the required component was replaced with a custom shortcut, it is at most **PARTIALLY ACHIEVED**. If the required component/framework is absent or the core functionality is missing, it is **NOT ACHIEVED**.

---

## Canonical Tech Stack (required mapping)

This is the expected technology for each concern. Replacing any of these with a hand-rolled equivalent is an approach violation.

| Concern | Required tech | Expected location | Notes |
| --- | --- | --- | --- |
| LLM access | OpenAI, via a single `get_llm()` factory | `config/llm.py` | One factory shared by every agent; one credential set. Streaming enabled on the Conversation Agent. |
| Conversation / runtime-decision agents | **LangGraph — ReAct** | `agents/conversation_agent.py`, `agents/concern_resolution_agent.py` | think → maybe call tool → think → respond. |
| Morning planner | **LangGraph — StateGraph** | `planner/orchestrator.py` | Fixed nodes with shared state (~6 nodes), each node streamed to the UI. |
| Fixed-step pipelines | **LangChain Chains** | `agents/post_session_chain.py`, `agents/briefing_agent.py`, `agents/replanning_agent.py` | Steps never change; LLM fills content, not structure. |
| Persistent memory | **Mem0** | `memory/mem0_client.py` (Mem0 cloud) | `search_memory`, `add_memory`, `get_all_memories`. Per-user isolation, auto fact extraction. |
| Knowledge base / RAG | **ChromaDB** | `rag/retriever.py`, `rag/indexer.py`, `chroma_db/` | Structured academic data | **Google Sheets** | `tools/sheets_client.py` | One sheet, 5 tabs. Read: `roster`, `exam_scores`, `attendance`, `exam_schedule`. Read+Write: `signal_sheet`. CSV fallback in `data/`. |
| Scheduling | **Google Calendar** | `tools/calendar_tools.py` | Events created in the **coach** account only. One-time OAuth via `scripts/setup_google_auth.py`. |
| UI | **Streamlit** | `main.py`, `ui/student_view.py`, `ui/coach_view.py` | Student View (chat) + Coach View (plan, alerts, briefings, calendar). Tool calls shown live via `st.status`. |
| Daily plan storage | Local file | `runtime/daily_plan.md` | Written by the planner, updated by the re-planner. |
| Session archive | Local JSON | `students/<id>/sessions/*.json` | **Audit archive only — NOT live memory.** Live continuity must come from Mem0. |

**Memory rule (important):** Live memory continuity must come from **Mem0**, not from session JSON files or in-memory variables. Session JSON is audit-only.

---

## Expected Repository Structure

The repository should broadly follow the layout below (paths come from the components & architecture reference). The reviewer must check that these files/folders are **present**, and explicitly point out any that are **missing** or placed in an unexpected location. Exact names may vary slightly, but the responsibility for each must live somewhere obvious.

```
student_success_coach_management/
├── main.py                          # Streamlit entrypoint
├── .env                             # secrets (NOT committed)
├── credentials.json                 # Google OAuth (NOT committed)
├── .gitignore
├── requirements.txt / pyproject.toml
├── config/
│   └── llm.py                       # get_llm() factory
├── agents/
│   ├── conversation_agent.py        # LangGraph ReAct
│   ├── concern_resolution_agent.py  # LangGraph ReAct
│   ├── post_session_chain.py        # LangChain chain
│   ├── briefing_agent.py            # LangChain chain
│   └── replanning_agent.py          # LangChain chain
├── planner/
│   └── orchestrator.py              # LangGraph StateGraph (morning planner)
├── memory/
│   └── mem0_client.py               # Mem0 wrapper
├── rag/
│   ├── retriever.py
│   └── indexer.py
├── tools/
│   ├── sheets_client.py
│   └── calendar_tools.py
├── ui/
│   ├── student_view.py
│   └── coach_view.py
├── scripts/
│   └── setup_google_auth.py         # one-time OAuth
├── data/                            # seed CSVs + Sheets fallback
├── runtime/
│   └── daily_plan.md                # written by planner / re-planner
├── students/<id>/sessions/*.json    # audit archive only
└── chroma_db/                       # generated vector index
```

**How to report structure:**
- For each expected area (config, agents, planner, memory, rag, tools, ui, data/runtime, scripts), state whether it is present.
- Explicitly list any **missing** required file/folder and tie it to the milestone/component it supports (e.g. "no `memory/mem0_client.py` → M4/M5 persistence likely not implemented").
- Note any responsibility that exists but lives in an unexpected place (acceptable, but call it out).

---

## Repository Hygiene (committed files)

Verify that **only relevant source/config files are committed** and that generated, secret, or environment-specific artifacts are **not** committed. A correct `.gitignore` should exist and cover these.

**Must NOT be committed (flag each occurrence found in the repo tree):**
- Python caches: `__pycache__/`, `*.pyc`, `*.pyo`, `*.pyd`
- Virtual environments: `venv/`, `.venv/`, `env/`
- Secrets / credentials: `.env`, `credentials.json`, `token.json`, any `*token*.json` / `*.pem` / key files
- OS / editor junk: `.DS_Store`, `Thumbs.db`, `.idea/`, `.vscode/` (unless intentionally shared)
- Tooling caches: `.pytest_cache/`, `.mypy_cache/`, `.ipynb_checkpoints/`, `*.log`
- Dependency dumps: `node_modules/` (not applicable here, but flag if present)

**Judgement calls (note, don't auto-fail):**
- `chroma_db/` is a **generated** vector index. It is typically rebuilt by `rag/indexer.py` and should usually be git-ignored; flag if a large binary index is committed without reason. Acceptable only if intentionally seeded for the demo.
- `students/<id>/sessions/*.json` and `runtime/daily_plan.md` are runtime outputs; committing sample/demo copies is acceptable, but bulk runtime dumps should be flagged.

**Checks to perform:**
- Confirm a `.gitignore` exists and includes the categories above.
- Scan the committed file tree for any of the "must NOT be committed" items and list each one found, with its path.
- Confirm dependencies are declared (`requirements.txt` or `pyproject.toml`).

**Severity guidance:** a committed secret (`.env`, `credentials.json`, tokens) is **Critical** (also a security finding). Committed caches/venv/OS junk are **Minor** hygiene findings but should always be listed.

---

## Milestone Guidelines

### M1 — Basic conversation  *(Phase 1: Student can have a real conversation)*

**Feature functionality**
- A student can send a message and receive a relevant response from the AI drawn from its own knowledge.
- The response is coherent and on-topic for the message sent.

**Component & approach**
- Conversation Agent is built with **LangGraph (ReAct)** — not plain Python `if/else` branching.
- All LLM calls go through the single `get_llm()` factory in `config/llm.py`.
- The chat is surfaced through the **Streamlit** student view (`ui/student_view.py`) with a working chat loop.
- Responses **stream** to the UI on the Conversation Agent.

**Marks PARTIALLY / NOT ACHIEVED**
- Canned / hardcoded responses → NOT.
- A direct one-off OpenAI call with no agent framework where an agent is expected → PARTIALLY.
- No LangGraph agent at all → NOT (the learning objective is bypassed).

---

### M2 — Student data in the conversation  *(Phase 1)*

**Feature functionality**
- Responses contain the student's **actual** subject scores, **attendance percentage**, and **upcoming exam dates** (real data, never fabricated).
- Responses **highlight anything that needs attention** — a dropping score, low attendance, or an exam coming up soon.

**Component & approach**
- Data is fetched live via **Tool Calling** — the **LLM decides per message** which tool(s) to call, not hardcoded "always fetch everything" logic.
- Tools read from **Google Sheets** through `tools/sheets_client.py`, using the `roster`, `exam_scores`, `attendance`, and `exam_schedule` tabs.
- **CSV fallback** in `data/` is acceptable when Google APIs are not configured, but the Sheets client path must exist.
- Tool calls are visible live in the Streamlit UI (`st.status`) — expected, not mandatory.

**Marks PARTIALLY / NOT ACHIEVED**
- Data hardcoded into the prompt or invented by the model → NOT.
- The agent always fetches all data regardless of the question (bypasses the tool-calling decision) → PARTIALLY.
- Real data shown but no attention-highlighting (no callout of dropping score / low attendance / upcoming exam) → PARTIALLY.

---

### M3 — Questions answered from knowledge base  *(Phase 1)*

**Feature functionality**
- When a student asks about what they are studying, the answer comes from the **knowledge base**.
- The answer is **accurate and specific** to the knowledge base (not a generic/hallucinated answer).

**Component & approach**
- Uses **ChromaDB RAG**: `rag/retriever.py` for retrieval and `rag/indexer.py` to index the course markdown once, persisted under `chroma_db/`.
- **Only the Conversation Agent** uses RAG, wired in as a retrieval step/tool.
- Demo path: Arjun (STU001) asking ML / DSA questions retrieves from indexed notes.

**Marks PARTIALLY / NOT ACHIEVED**
- The LLM answers from its own training knowledge with no retrieval → NOT.
- Knowledge base never indexed / retriever returns nothing → NOT.
- Retrieval exists but answers are not grounded in the retrieved content → PARTIALLY.

---

### M4 — Session is stored after it ends  *(Phase 2: System remembers the student)*

**Feature functionality**
- When a session ends, **what the student shared is captured and stored persistently** in memory.

**Component & approach**
- An **End Session** action in the Streamlit student view triggers post-session processing.
- Processing is a **LangChain Post-Session Chain** with fixed steps: **extract → Mem0 → flag → Sheets**.
- Persistence uses **Mem0 `add_memory`** (`memory/mem0_client.py`); Mem0 auto-extracts facts.
- A session JSON archive may be written under `students/<id>/sessions/*.json`, but this is **audit-only** and does not satisfy the persistence requirement on its own.

**Marks PARTIALLY / NOT ACHIEVED**
- Conversation kept only in a local variable / in-memory dict → NOT.
- Stored only to JSON files and treated as the live memory → PARTIALLY (Mem0 persistence is the requirement; JSON is audit-only).
- Mem0 write present but not triggered on session end → PARTIALLY.

---

### M5 — AI knows the student's history  *(Phase 2)*

**Feature functionality**
- When the **same student** starts a **new session**, the AI **already knows their history**.
- **Two types of memory maintained separately:**
  - **Factual memory** — stress triggers, what has helped, recurring patterns or user facts — shapes how the AI responds in conversation.
  - **Session summaries** — what was discussed and what was decided — used when the coach asks for a briefing.
- A student on their **fifth session** gets a **meaningfully different** response than on their first.

**Component & approach**
- **Mem0 `search_memory`** loads relevant facts at **Conversation Agent startup** (factual memory feeds the conversation).
- **Mem0 `get_all_memories`** supplies the full profile for briefing, concern resolution, and the planner.
- The **separation** between factual memory and session summaries is explicit (distinct memory types/namespaces), since they are consumed by different parts of the system.
- Per-user isolation in Mem0.

**Marks PARTIALLY / NOT ACHIEVED**
- History stored but never retrieved/used in a new session → NOT.
- A single undifferentiated memory blob with no factual-vs-summary separation → PARTIALLY.
- Memory not loaded into the Conversation Agent at startup → PARTIALLY.

---

### M6 — Signals detected and coach alerted  *(Phase 3: Problems get surfaced automatically)*

**Feature functionality**
- A **signal is written after every session** capturing what was concerning.
- Each signal has a **severity** (how serious the issue is) and an **urgency** (act today vs. can wait until tomorrow).
- The system decides at the **end of every conversation** whether anything warrants flagging.
- **Serious signals trigger a deeper reasoning chain** (concern resolution / assessment).
- If severity is **critical**, the **student's manager is automatically notified** with a full contextual summary.

**Component & approach**
- The flagging step is part of the **LangChain Post-Session Chain** (the `flag → Sheets` steps).
- Signals are written to the **Google Sheets `signal_sheet`** tab (read+write) with **severity, urgency, actioned** fields, via `tools/sheets_client.py`.
- Deeper reasoning on serious signals uses the **Concern Resolution Agent — LangGraph ReAct** (`agents/concern_resolution_agent.py`), drawing on `get_all_memories`.
- Severity/urgency are **LLM-assessed**, not purely hardcoded thresholds.

**Marks PARTIALLY / NOT ACHIEVED**
- No signal written / no flagging logic → NOT.
- Signal written without severity **and** urgency → PARTIALLY.
- Signals only printed/logged, not persisted to `signal_sheet` → PARTIALLY.
- Critical severity does not trigger manager notification → PARTIALLY.

---

### M7 — Daily plan generated from signals  *(Phase 4: Coach gets a prepared day)*

**Feature functionality**
- The coach **triggers the plan** and gets back a **structured day**.
- **Every student who needs attention** is slotted with a **session type** and a **plain reason** for why they are there today.
- Students who **cannot fit today** are **deferred to tomorrow with a reason**.
- The AI **creates calendar invites in the coach account** (no student invites in current scope).

**Component & approach**
- The Morning Planner is built with **LangGraph StateGraph** — fixed nodes with shared state (~6 nodes), each node **streamed to the UI** (`planner/orchestrator.py`).
- **Orchestrator-Workers** pattern: the orchestrator coordinates **sub-agents** that fetch data for flagged students; the orchestrator **filters, reasons about tradeoffs, and synthesises** — it never reads raw data itself.
- Reads flagged signals from `signal_sheet` and student data via the Sheets client; uses Mem0 `get_all_memories` for context.
- Writes the plan to **`runtime/daily_plan.md`**.
- Creates **Google Calendar** invites via `tools/calendar_tools.py` in the coach account.
- Triggered from the **Coach View** (Streamlit) "generate plan" action.

**Marks PARTIALLY / NOT ACHIEVED**
- Built as a plain Python sort/loop instead of a LangGraph StateGraph → NOT (learning objective bypassed).
- A sorted list with no per-student reason / no session type → PARTIALLY.
- No defer-to-tomorrow handling with reasons → PARTIALLY.
- No coach calendar invite creation → PARTIALLY.
- Orchestrator reads raw data directly instead of delegating to sub-agents → approach violation (PARTIALLY).

---

### M8 — Pre-meeting brief on any student  *(Phase 5: Coach walks into every meeting prepared)*

**Feature functionality**
- The coach **requests a brief for any student** and gets a **focused summary**.
- The brief covers all four parts: the student's **current academic situation**, **what has changed since the last session**, any **open concerns**, and **specific conversation starters for today**.
- The brief **draws from both factual memory and session summaries** built in M5.

**Component & approach**
- The Briefing Agent is a **LangChain Chain** with fixed steps: **load data → one LLM call → markdown** (`agents/briefing_agent.py`).
- Pulls from **Mem0** (factual memory via `get_all_memories` **and** session summaries), recent Sheets data, and open signals from `signal_sheet`.
- Surfaced in the **Coach View** (Streamlit). Optionally a "Create Calendar Event" after the briefing, where the event description includes the **first 500 chars** of the briefing.

**Marks PARTIALLY / NOT ACHIEVED**
- Brief missing any of the four required parts (situation / changes / open concerns / conversation starters) → PARTIALLY.
- Brief built from raw data only, ignoring Mem0 memory → PARTIALLY/NOT (it must draw from M5 memory).
- No way for the coach to request a brief per student → NOT.

---

### M9 — Serious concern updates the plan automatically  *(Phase 6: Urgency changes the plan)*

**Feature functionality**
- When a **serious concern surfaces**, the **existing daily plan updates automatically**.
- A **new slot is added** or **someone is moved to tomorrow** — **every change has a clear reason** attached.
- **Conflict handling (human-in-the-loop):** if **two students are both critical and there is only one slot**, the system **does NOT decide on its own** — it **surfaces both cases to the coach with the tradeoff clearly explained** and asks the coach to make the call.
- The coach **sees a summary of what changed in the plan and why** before they even open the app.

**Component & approach**
- The Re-planning Agent is a **LangChain Chain** — **load plan → LLM revises → write plan** (`agents/replanning_agent.py`) — performing **dynamic reasoning** over the new state.
- It **loads the current** `runtime/daily_plan.md`, reasons about who to move/defer, and **rewrites** it (does not regenerate from scratch).
- Reads the new critical signal from `signal_sheet`; uses Mem0 context.
- Writes the updated **`runtime/daily_plan.md`** and surfaces a **change summary** (Coach View alerts / notification).

**Marks PARTIALLY / NOT ACHIEVED**
- Plan regenerated from scratch instead of updating the existing plan → PARTIALLY.
- **Auto-resolving the two-critical-one-slot conflict without asking the coach** → approach violation / functional gap (this escalation is an explicit requirement).
- Changes applied without a reason for each → PARTIALLY.
- No change summary surfaced to the coach → PARTIALLY.

---

## Cross-cutting Concept Map

Each taught concept must be visible somewhere in the system. Use this to sanity-check that the learning objectives are met, not just the features.

| Concept | Where it must appear | Milestone(s) |
| --- | --- | --- |
| Tool Calling | Conversation Agent decides per message which tool to call | M2 |
| The Agent Loop | reason → act → observe → reason; no fixed termination in code | M1, M2 |
| Memory | Session 1 generic vs Session 5 specific, driven by memory extraction | M4, M5 |
| Multi-step Orchestration | Flagging agent → concern resolution agent; each receives reasoned output, state accumulates | M6 |
| Orchestrator-Workers | Daily planner orchestrator coordinates sub-agents; never reads raw data itself | M7 |
| Chain vs Agent | Post-session = chain (steps known); Re-planning = agent (steps unknown upfront) | M4, M6, M8, M9 |
| Dynamic Reasoning | Re-planning agent reasons over a changed world and justifies decisions | M9 |
| MCP Integration *(bonus)* | Tools built during the session exposed as an MCP server; agents discover & call them dynamically (no hardcoded definitions) | Cross-cutting / extra credit — not one of the 9 milestones |

---

## Security & Setup Checks (functionality-impacting only)

- Secrets are read from environment / `.env`: `OPENAI_*`, `MEM0_API_KEY`, `GOOGLE_SPREADSHEET_ID`. Mem0 is connected via `MemoryClient(api_key=MEM0_API_KEY)` in `memory/mem0_client.py`.
- `credentials.json` (Google OAuth) must **not** be committed — it must be git-ignored.
- No hardcoded API keys or secrets in source.
- No unsafe execution of raw user input.
- Do not over-report enterprise-grade security recommendations — only flag issues that affect functionality or production readiness.

---

## Scoring Rubric — STRICT (compute the score — do not estimate it)

The final `/100` score is a **sum of itemized points**, never a gut estimate. Scoring is **strict and binary**: every requirement is one of the project's **absolute MUSTs** drawn directly from the references (build milestones, components & architecture, capabilities showcase). Award a requirement its **full points only when it is fully and correctly implemented using the mandated component**. Award **0** otherwise. There is **no partial credit** within a single requirement.

A requirement scores **0** (not partial) when any of these is true:
- The mandated framework/component is **absent or replaced** with a hand-rolled equivalent (e.g. plain Python instead of LangGraph StateGraph; signals in Mem0 instead of the Sheets `signal_sheet`; no `get_llm()` factory).
- The feature is **present in code but does not actually work** — it crashes, raises, or is never reached (e.g. a re-planner that `KeyError`s).
- The feature is **designed but never exercised** — wired but never invoked, or a memory namespace that is never populated (e.g. factual memory that is imported but never written).
- The data source is **the wrong one** versus the references (e.g. a knowledge base that contains platform docs when the milestone requires course/study content).

**Point budget (totals 100):**

| Bucket | Points |
| --- | --- |
| 9 milestones (9 pts each) | 81 |
| Security | 6 |
| Repository structure | 7 |
| Repository hygiene | 6 |
| **Total** | **100** |

### Per-milestone MUSTs (9 pts each, split equally across the MUSTs; each MUST is 0 or full)

| Milestone | MUSTs (each binary) |
| --- | --- |
| **M1** (4 MUSTs × 2.25) | LangGraph ReAct agent, not if/else · working Streamlit student chat with relevant replies · **all** LLM calls via a single `get_llm()` factory · responses **stream** to the UI |
| **M2** (3 MUSTs × 3) | per-message tool calling, LLM decides · reads real data from Google Sheets (roster, exam_scores, attendance, exam_schedule) · highlights attention items (dropping score **and** low attendance **and** exam coming up soon) |
| **M3** (3 MUSTs × 3) | ChromaDB indexer + retriever, persisted · RAG wired **only** into the Conversation Agent · answers **course/study** questions grounded in indexed **course notes** (correct corpus per references) |
| **M4** (4 MUSTs × 2.25) | End-Session action triggers processing · what the student shared is persisted via Mem0 `add_memory` · implemented as a **LangChain Post-Session Chain** (fixed steps) · the chain's `flag → Sheets` step writes the signal to the Sheets `signal_sheet` |
| **M5** (3 MUSTs × 3) | a new session loads the student's history from Mem0 · **two** memory types kept separate **and both actually populated** (factual + summaries) · factual memory loaded into the Conversation Agent **at startup** |
| **M6** (5 MUSTs × 1.8) | a signal is written after every session · severity **and** urgency, LLM-assessed · persisted to the Google Sheets `signal_sheet` (severity/urgency/actioned) · serious signals trigger a **Concern Resolution Agent (LangGraph ReAct)** · **critical** severity auto-notifies the manager with a contextual summary |
| **M7** (6 MUSTs × 1.5) | coach-triggered structured day with session type + reason · defer-to-tomorrow with reason · coach-account calendar invites · built as a **LangGraph StateGraph** (nodes streamed) · **Orchestrator-Workers** (orchestrator coordinates sub-agents, never reads raw data) · plan written to `runtime/daily_plan.md` |
| **M8** (4 MUSTs × 2.25) | coach requests a brief per student · **LangChain Chain** (load → 1 LLM call → markdown) · brief covers **all four** parts (current situation / what changed since last session / open concerns / conversation starters) · draws from **both** factual memory **and** session summaries |
| **M9** (5 MUSTs × 1.8) | serious concern **auto-updates the existing plan** (works, no crash) · adds a slot or defers, each change with a reason · two-critical-one-slot conflict **surfaced to the coach** (human-in-the-loop, works) · **LangChain Chain** that loads + rewrites `runtime/daily_plan.md` · coach sees a change summary |

### Security MUSTs (6 pts)

- No hardcoded secrets; all read from env/`.env` (2)
- No secrets/credentials committed; correctly git-ignored (2)
- No unsafe execution of raw user input (1)
- No secret **value** leaked via logs/prints (1)

### Repository structure (7 pts) — award only for required components present in mandated form

- `config/llm.py` `get_llm()` factory (1)
- agents — conversation, concern-resolution, post-session-chain, briefing, replanning (1.5 — i.e. 0.3 each, present in the mandated form)
- planner LangGraph StateGraph (1)
- `memory/mem0_client.py` (0.5)
- RAG retriever + indexer (0.5)
- tools — sheets + calendar (0.5)
- UI — student + coach (0.5)
- `scripts/setup_google_auth.py` (0.25)
- `data/` CSV fallback (0.25)
- `runtime/daily_plan.md` (0.25)
- session archive (0.25)
- `requirements.txt` / `pyproject.toml` (0.5)

### Repository hygiene MUSTs (6 pts)

- `.gitignore` exists and covers the required categories (2)
- Tracked tree is free of caches/venv/secrets/OS junk (2)
- Dependencies declared (1)
- Cleanliness: no leftover debug flags/stray prints/dup code, complete `.env.example` (1)

### Milestone status (strict)

- **ACHIEVED** — **all** MUSTs met (full 9/9).
- **PARTIALLY ACHIEVED** — some MUSTs met, score ≥ 4.0/9, and the milestone's core feature actually works.
- **NOT ACHIEVED** — score < 4.0/9, **or** the core feature is broken/non-functional, **or** a milestone-specific hard rule forces NOT (e.g. plain Python instead of StateGraph; required framework absent). A hard rule overrides the numeric band.

### Verdict bands (from the computed total)

- **Pass** — total ≥ 75/100
- **Needs Improvement** — 50 ≤ total < 75
- **Fail** — total < 50

The report must show the per-MUST breakdown table so the total is reproducible from the rubric.
