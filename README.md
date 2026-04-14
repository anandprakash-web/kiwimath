# Kiwimath 🥝

Adaptive math app for Grade 1 global learners. Duolingo-style engagement, with a diagnostic step-down moat: every wrong answer is diagnosed for the underlying misconception, and the student is scaffolded back up through smaller sub-steps until they recover.

v0 scope: Grade 1, Kangaroo Felix context, Topics 1–2 (Counting & Observation, Arithmetic & Missing Numbers), Android first.

## Repo layout

```
backend/         FastAPI server, Pydantic models, adaptive engine
content_tools/   CLI tools for the academic team (validator, ingester, previewer)
docs/            Architecture decisions, schema reference, runbooks
app/             Flutter Android app (coming Week 2)
```

## Quickstart (local dev)

```bash
# Install Python 3.11+, then:
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Validate a folder of authored questions
python -m content_tools.validate ~/Documents/Kiwimath-Content/Grade1/

# Run the backend
uvicorn app.main:app --reload
```

## Content workflow

1. Academic team authors JSON questions in `~/Documents/Kiwimath-Content/Grade1/0N-Topic/`.
2. Validator catches schema errors, broken step-down refs, unrealistic distractors.
3. Ingest script loads approved questions into Postgres.
4. App fetches rendered questions from `/questions/next`.

## Status

| System | Status |
|---|---|
| Question schema | ✅ v0.1 locked |
| Pydantic models | ✅ shipped |
| Schema validator | ✅ shipped |
| Question renderer | ✅ shipped (params, locale, pronouns, distractors, step-downs) |
| Safe formula evaluator | ✅ shipped (ast-based, no eval()) |
| SVG generator framework | ✅ shipped (1 generator: object_row_with_cross_out) |
| FastAPI skeleton | ✅ shipped (/questions/next, /questions/{id}, /health) |
| Content store (in-memory) | ✅ shipped |
| Flutter app | ⏳ Week 3 |
| Firebase wiring | ⏳ Week 3 |
| Adaptive engine v0 | ⏳ Week 3 |
| Postgres ingester | ⏳ Week 4 |
