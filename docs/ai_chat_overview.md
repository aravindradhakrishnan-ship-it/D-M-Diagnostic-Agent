### AI Chat Overview

This project can add a “Chat with the KPIs” experience by combining:
- An LLM with tool-calling (e.g., OpenAI `gpt-4o-mini` or `gpt-4.1-mini`).
- Retrieval over your KPI catalogue/descriptions (vector index).
- Safe data tools that return filtered KPI slices/summaries (country/week/client).

#### Suggested Architecture
- **Retrieval:** Embed KPI catalogue entries (name, description, source table, filters) and store in a vector index (FAISS/Chroma under `assets/ai_index`). Retrieve a handful of top matches per query.
- **Tools:** Expose a Python function (e.g., `get_kpi_data(country, week, client, kpi_id=None, limit=200)`) that uses the existing calculation engine to fetch filtered data or a small sample/sum/avg. Keep outputs small and safe (no PII, cap rows).
- **LLM:** Call the OpenAI Chat Completions API with a system prompt that: (a) enforces scope (only speak about the provided context and tool outputs), (b) uses the tool when needed, (c) cites which filters were applied. Keep temperature low.
- **Streamlit UI:** Add a chat panel (sidebar or main section) that passes the currently selected country/week/client to the backend. On each user turn: retrieve context → call LLM (with tool) → display answer and cited sources/filters.

#### Minimal Files to Add
- `src/ai_tools.py`: define `get_kpi_data(...)` that wraps your calculation engine; include guardrails (row limits, allowed columns).
- `src/ai_retriever.py`: build/load the FAISS index from the KPI catalogue; expose `retrieve(query, top_k=5)`.
- `src/ai_chat.py` (or integrate into `dashboard.py`): Streamlit chat loop using the OpenAI client with the tool schema wired in.

#### Environment/Config
- Add `OPENAI_API_KEY` to your environment (Streamlit Cloud secrets).
- Optional: config file for model name and index path (e.g., `assets/ai_index`).

#### Safety & UX
- Always echo applied filters (country, week, client) in answers.
- Refuse out-of-scope questions (e.g., unrelated topics).
- Cap data returned to the LLM (rows/fields) and avoid PII fields entirely.
- Show sources: list retrieved KPI names/descriptions or sample rows used.

#### Happy Path Flow
1) User selects country/week/client and asks a question.
2) Retrieve relevant KPI catalogue snippets; pass them as context to the LLM.
3) If the LLM needs data, it calls `get_kpi_data`; you execute it and return a small result.
4) LLM responds with a concise, cited answer; UI displays answer + sources/filters.

This doc is a starting point. The next step is to scaffold the three helper files above and wire a chat block into `dashboard.py`. Let me know the target model and I’ll implement the code.***
