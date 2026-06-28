# KiwiReader — Execution Plan

> Build plan for the Reader & Annotation module that plugs into **kiwimaths** (Flutter, iOS + Android).
> Companion to the design doc (`kiwireader_design.html`). This document is the *how we ship it*.

---

## 0. Strategy in one paragraph

We **de-risk by building the hard core first**. The two things that can sink this product — annotation **anchoring** (does a highlight land on the right words after reflow / re-publish?) and **sync conflict resolution** (do two devices ever lose a student's note?) — are both **pure logic with no UI dependency**. So we isolate them in a Flutter-free Dart package (`kiwi_reader_core`) and cover them with unit tests *before* a single pixel is drawn. The Flutter UI and the format renderers sit on top of that proven core behind clean seams.

---

## 1. Repository & module strategy

A **monorepo** with two packages plus the API contract:

```
kiwireader/
├── packages/
│   ├── kiwi_reader_core/      # PURE DART — no Flutter. Models, anchoring, sync. 100% unit-tested.
│   └── kiwi_reader/           # FLUTTER — widgets, renderers, Riverpod providers. Depends on core.
├── openapi/openapi.yaml       # REST contract for the Annotation & Sync API
├── EXECUTION_PLAN.md
└── README.md
```

**Why split the package?** It forces the dependency rule (UI → core, never the reverse), makes the risky logic testable on a CI runner with no device/emulator, and lets the core be reused by a future web reader or a backend re-anchoring job.

**Integration into kiwimaths:** add `kiwi_reader` as a path/git dependency, implement two interfaces (`ContentProvider`, `AuthProvider`), drop `KiwiReader(bookId: …)` into the new bottom-nav tab. No other coupling.

---

## 2. Milestones (mapped to PRD phases)

| Milestone | PRD phase | Outcome | Exit criteria |
|---|---|---|---|
| **M0 — Proven core** | Foundations | Tested anchoring + sync + models + API contract | All core unit tests green; OpenAPI validates |
| **M1 — Reader MVP** | Phase 0 | Read tab; HTML/JSON + PDF render; bookmark; progress; offline cache; single-color highlight | Open < 2 s cached; highlight + bookmark persist offline |
| **M2 — Annotate** | Phase 1 | Multi-color highlight, underline, typed notes, annotations list, cross-device sync, orphan handling, export(MD) | Orphan rate < 1% on re-publish fixture; 2-device sync verified |
| **M3 — Scribe** | Phase 2 | EPUB reflow, stylus ink + eraser/lasso, handwriting→text, PDF export, teacher-shared annotations | Ink 60 fps + palm rejection on target devices |
| **M4 — Loop** | Phase 3 | Highlight→quiz linking, spaced-repetition review, teacher analytics, image OCR | Measurable quiz-attempt/retention lift |

---

## 3. Sprint plan (2-week sprints, indicative)

| Sprint | Theme | Headline tickets |
|---|---|---|
| **S1** | Core + contract (**M0**) | KR-001…008 — models, anchor resolver, sync merge, in-memory mock, OpenAPI |
| **S2** | Render + shell (**M1**) | KR-010…016 — ContentRenderer seam, HTML & PDF adapters, reader shell, progress, offline cache |
| **S3** | Highlight + bookmark (**M1**) | KR-020…025 — selection pipeline, overlay layer, single-color highlight, bookmark, local store (Drift) |
| **S4** | Notes + list + sync (**M2**) | KR-030…037 — note editor, multi-color, annotations list, REST client, SyncEngine wiring, conflict UI |
| **S5** | Resilience (**M2**) | KR-040…045 — re-anchor on version bump, orphan "needs review" UX, export(MD), a11y pass, perf hardening |
| **S6** | Scribe start (**M3**) | KR-050…056 — EPUB renderer, ink layer, eraser/lasso, palm rejection |

> Phases are independently shippable behind a feature flag (`reader_tab_enabled`, `reader_ink_enabled`).

---

## 4. Ticket backlog (S1–S4 detailed)

Estimates in **story points** (1≈half-day, 2≈1d, 3≈2d, 5≈3-4d). `→` = depends on.

### M0 · Core (this session's target)
| ID | Ticket | Pts | Deps | DoD |
|---|---|---|---|---|
| KR-001 | Domain models (Annotation, Anchor, 3 selectors, Bookmark, Progress, Manifest) + JSON | 3 | — | Round-trip JSON tests pass |
| KR-002 | Text normalizer (whitespace, canonical stream, offset map) | 2 | KR-001 | Idempotent; offset map verified |
| KR-003 | Quote matcher (exact, prefix/suffix, multi-match, fuzzy) | 3 | KR-002 | Unit tests for each match class |
| KR-004 | `AnchorResolver.resolve()` decision tree (resolved/repaired/approx/orphaned) | 5 | KR-003 | Branch coverage; fixtures for reflow & re-publish |
| KR-005 | Sync models + field-level merge (LWW, tombstone-wins, note keep-both) | 3 | KR-001 | Conflict matrix tests |
| KR-006 | `SyncEngine` over `LocalStore` + `AnnotationApi` interfaces | 3 | KR-005 | Offline→push, pull→merge, idempotent by id |
| KR-007 | In-memory `LocalStore` + mock `AnnotationApi` (conflict-injecting) | 2 | KR-006 | Used by engine tests |
| KR-008 | OpenAPI 3 spec + schema parity with Dart models | 2 | KR-001 | `openapi` lints clean |

### M1 · Reader MVP
| ID | Ticket | Pts | Deps |
|---|---|---|---|
| KR-010 | `ContentRenderer` interface + `Locator`/`Selection` geometry types | 2 | KR-001 |
| KR-011 | `HtmlRenderer` (custom JSON/HTML, math via flutter_math_fork) | 5 | KR-010 |
| KR-012 | `PdfRenderer` (pdfrx; text layer → quote anchors) | 5 | KR-010 |
| KR-013 | Reader shell (chrome, pagination/scroll, settings sheet) | 3 | KR-010 |
| KR-014 | Reading-progress persistence + restore | 2 | KR-013, KR-007 |
| KR-015 | Offline content cache (range-aware) | 3 | KR-012 |
| KR-016 | Riverpod providers + `ReaderController` | 3 | KR-013 |

### M1/M2 · Annotate
| ID | Ticket | Pts | Deps |
|---|---|---|---|
| KR-020 | Selection pipeline → `anchorForSelection()` | 3 | KR-011/012 |
| KR-021 | Annotation overlay layer (highlight/underline draw + hit-test) | 5 | KR-020, KR-004 |
| KR-022 | Selection toolbar (color, underline, note, copy) | 3 | KR-021 |
| KR-023 | Single-color highlight create/persist (optimistic) | 2 | KR-022, KR-007 |
| KR-024 | Bookmark toggle + panel | 2 | KR-016 |
| KR-025 | Drift local store (replaces in-memory on device) | 3 | KR-007 |
| KR-030 | Note editor bottom sheet + autosave draft | 3 | KR-023 |
| KR-031 | Multi-color + underline + strikethrough | 2 | KR-023 |
| KR-032 | Annotations list (filter/sort/search/jump) | 5 | KR-031 |
| KR-035 | REST `AnnotationApi` client (Dio) against OpenAPI | 3 | KR-008 |
| KR-036 | Wire `SyncEngine` to Drift + REST + connectivity | 3 | KR-035, KR-025 |
| KR-037 | Conflict + sync-state surfacing (indicator, trash window) | 3 | KR-036 |

---

## 5. Definition of Done (every ticket)

- Code + dartdoc on public API; passes `dart analyze` (lints in `analysis_options.yaml`).
- Unit tests for logic; widget tests for UI; golden tests for highlight rendering.
- No `TODO` without a ticket link; no secrets in code.
- Accessibility: semantics labels on interactive elements (M2+).
- Updated `CHANGELOG.md`; PR reviewed; feature behind a flag if user-facing.

---

## 6. Test strategy

| Layer | Tooling | What |
|---|---|---|
| Core logic | `dart test` | Anchoring branch coverage, sync conflict matrix, JSON round-trips |
| Renderers | `flutter_test` + goldens | Anchor→rect mapping, highlight paint, reflow stability |
| Integration | `integration_test` | Open→select→highlight→kill→reopen→synced |
| Contract | OpenAPI + mock | Client/server schema parity; mock injects 409s, 413s, offline |
| Perf | DevTools + benchmarks | Open < 2 s, 60 fps highlight, 2k-annotation list scroll |

**Risk burn-down order:** KR-004 (anchoring) and KR-005/006 (sync) are scheduled *first* because they carry the most product risk and the least UI risk. ← **delivered this session.**

---

## 7. CI/CD

- PR pipeline: `dart analyze` + `dart test` (core) → `flutter analyze` + `flutter test` (reader) → build iOS/Android artifacts.
- Core package gates the whole pipeline (fast, no emulator).
- Feature flags via remote config so phases ship dark and enable per cohort.

---

## 8. What THIS session delivers (M0)

✅ `kiwi_reader_core` — models, `AnchorResolver`, sync merge + `SyncEngine`, in-memory store + mock API — **with passing unit tests run on the Dart SDK.**
✅ `openapi/openapi.yaml` — the REST contract, schema-parity with the Dart models.
✅ `kiwi_reader` (Flutter) — scaffolded package: `ContentRenderer` seam, host interfaces, Riverpod providers, `KiwiReader` widget skeleton (compiles against Flutter; not run here).
✅ This plan + README.

**Next session:** connect the kiwimaths repo, run `flutter pub get`, implement `HtmlRenderer` first (your content is already structured), and wire the reader shell — i.e., start S2.
