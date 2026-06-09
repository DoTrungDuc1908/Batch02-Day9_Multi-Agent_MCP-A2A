# Exercise Solutions

## Exercise 2

Implemented in `exercise_2_tools.py`:

- Added the `labor_law` knowledge-base entry.
- Added `check_statute_of_limitations(case_type)`.
- Added the new tool to the bound tools list.
- Executed requested tool calls through a `tool_map`.

Run:

```bash
py exercises/exercise_2_tools.py
```

## Exercise 4

Implemented in `exercise_4_multiagent.py`:

- Added `privacy_analysis` to shared state.
- Added keyword routing for `data`, `privacy`, `gdpr`, `du lieu`, and `ro ri`.
- Implemented `privacy_agent`.
- Added the privacy node, edge, and aggregate section.

Run:

```bash
py exercises/exercise_4_multiagent.py
```

## Stage 5 / Bonus

Implemented:

- Stage 1 question changed from the original NDA example.
- Stage 3 ReAct debug output is enabled with `AGENT_DEBUG=true`.
- `test_client.py` prints end-to-end latency.
- `FAST_ROUTING=true` skips one routing LLM call in Law Agent.
- `scripts/benchmark_latency.py` measures repeated latency runs.
- `scripts/check_dynamic_discovery.py` verifies Registry discovery.
- `docs/agent_interaction_demo.html` demonstrates A2A interaction visually.
- `docs/stage5_trace_and_latency.md` documents trace flow and comparison steps.
- Optional challenges: conversation memory, API key auth, A2A retry, and
  Prometheus-style `/metrics` endpoints.
