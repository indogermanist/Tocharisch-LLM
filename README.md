# Tocharisch-LLM

## Project goal

This project uses LLMs to simplify search in:

- the Tocharian dictionary
- translated Tocharian fragments
- links between dictionary entries and fragment words

The XML source files are transformed by a reproducible data pipeline into:

- a **Knowledge Graph** in Neo4j (entities + relationships)
- a **Vector Store** in Qdrant (semantic search over embeddings)

The user interface is built with Streamlit.

## Prerequisites

- Docker + Docker Compose

## Required `.env` variables

Add these keys to your `.env` file:

```env
OPENAI_API_KEY=""
NEO_4J_PORT="8687"
NEO_4J_USER="neo4j"
NEO_4J_PASSWORD="your_password"
DEEPSEEK_API_KEY=""
```

Notes:

- `DEEPSEEK_API_KEY` is used for the chat model.
- `OPENAI_API_KEY` is used for embeddings in Qdrant (`text-embedding-3-large`).
- Optional for Dockerized networking:
  - `NEO_4J_HOST="neo4j"`
  - `QDRANT_HOST="qdrant"`
  - `QDRANT_PORT="6333"`

## How to start everything

### 1. Start all long-running services (Neo4j, Qdrant, Streamlit app)

```bash
docker compose up --build
```

The UI is available at `http://localhost:8501`.

### 2. Run ingestion pipeline (second terminal)

```bash
docker compose run --rm ingestion --with-qdrant
```

Default XML paths used by this command:

- `Tocharisch_Fragmente/fragments_dummy.xml`
- `Tocharisch_Fragmente/dictionaries_dummy.xml`

Run with explicit custom paths:

```bash
docker compose run --rm ingestion \
  --fragments-xml path/to/fragments.xml \
  --dictionary-xml path/to/dictionaries.xml \
  --with-qdrant
```

## What the ingestion command does

`src/services/run_ingestion.py` is the executable entrypoint for `src/services/ingestion.py`.
It runs the full XML pipeline:

1. loads fragment metadata, transcriptions, and translations into Neo4j
2. loads dictionary entries, lexical subentries, inflected forms, and their relations into Neo4j
3. optionally pushes fragment translations from Neo4j into Qdrant (`--with-qdrant`)

Useful flags:

- `--no-reset`: keep existing Neo4j graph data
- `--no-enrich`: skip word graph enrichment relations
- `--fragments-xml PATH`: custom fragments XML path
- `--dictionary-xml PATH`: custom dictionary XML path