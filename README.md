# DUST — Requirements Formalization Engine

DUST turns **natural-language engineering requirements** (aircraft level, systems,
airframe, services, industrial, interfaces, …) into machine- and LLM-readable
**formal artifacts** for downstream reasoning and simulation.

From one input it produces four coordinated outputs:

| Output | Description |
| --- | --- |
| **JSON IR** | Structured intermediate representation — entities, attributes, constraints, relations. The single source of truth. |
| **EARS** | Normalized requirement text using the Easy Approach to Requirements Syntax (When/While/If/Where … shall …). |
| **SysML v2** | SysML v2 textual notation (`requirement def`, `part def`, `interface def`, `satisfy`) ready for modelling/simulation tools. |
| **Ontology** | All identified elements + relationships, as a JSON graph, Mermaid diagram, and RDF Turtle. |

The GenAI call is isolated to a single extraction step; EARS, SysML v2, and the
ontology are deterministic renderers over the IR.

## Architecture

```
text ─▶ segment ─▶ LLM extract ─▶ JSON IR ─┬─▶ EARS
                                           ├─▶ SysML v2
                                           └─▶ Ontology (graph / mermaid / turtle)
```

## LLM providers (provider-agnostic)

Selectable via `LLM_PROVIDER`: `mock` (offline, default), `anthropic`, `openai`,
`huggingface`, `ollama` (local). Each request may also override the provider.

## Install

```bash
pip install -e .                 # base (mock + ollama + huggingface work out of the box)
pip install -e ".[all]"          # + anthropic, openai, spaCy, rdflib, pytest
```

Copy `.env.example` to `.env` and configure your provider.

## Run the API

```bash
uvicorn dust.api.app:app --reload     # or: dust-api
```

Formalize requirements (mock provider needs no keys):

```bash
curl -s localhost:8000/formalize \
  -H 'content-type: application/json' \
  -d "{\"text\": \"The fuel system shall maintain fuel pressure at 30 bar.\", \"provider\": \"mock\"}"
```

`POST /formalize` body: `{ "text": "...", "targets": ["ir","ears","sysml","ontology"], "provider": "ollama" }`.
`GET /health` for a liveness check. Interactive docs at `/docs`.

## Test

```bash
pytest        # runs fully offline via the mock provider
```
