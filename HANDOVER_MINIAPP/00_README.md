# Mini-App Handover Pack — turning Kiwimath into JEE / NEET / exam apps

**Author:** Anand Prakash (Kiwimath founder)
**Purpose:** Hand the Kiwimath *idea + codebase* to a fresh build (and a fresh Cowork/Claude session) so it can stand up new exam-prep mini-apps — JEE, NEET, and others — without re-inventing the platform.

---

## The one-paragraph thesis

Kiwimath is **not a math app with some software around it**. It is a **content-agnostic adaptive-learning platform** that happens to be filled with math right now. The platform — the question bank format, the adaptive engine, the daily quiz, the contest + league, the economy, the library/reader, the store, the Flutter shell — has **zero knowledge of "math"** baked in. To make a JEE or NEET app you **keep the whole platform and swap the content + the labels on the shelves.** That is the entire strategy. Everything in this pack exists to make that swap safe and fast.

---

## ⚠️ Read this first (the rule that keeps the next cowork honest)

This codebase grew up on **math**, where a question's answer can often be checked by a computer (re-run the arithmetic, confirm the key). **JEE/NEET content is Physics, Chemistry, Biology — you cannot do that.** An AI that tries to *generate* or *verify* a chemistry answer key will hallucinate, confidently.

So the governing rule for every new app is:

> **The AI builds the machine. Humans and authoritative sources supply the content.**
> The new cowork session should treat every question, answer, and solution as **untrusted input that comes from a real source** (official past papers, licensed banks, subject-expert authored material) — never as something it can invent or "double-check" itself.

This pack is deliberately **light on actual subject content** for exactly this reason. If you find yourself asking the next cowork to "write 50 physics questions," stop — that is the one thing it must not do. Detail in `04_CONTENT_GUARDRAILS.md`.

---

## What's in this pack

| File | What it gives you |
|------|-------------------|
| `00_README.md` | This file — the thesis, the rule, how to use the pack. |
| `01_SYSTEM_MAP.md` | The platform explained as a content-agnostic spine. The mental model. No subject content. |
| `02_FORK_VS_REBUILD.md` | The core deliverable: every component → keep as-is / reconfigure / rebuild, with real file paths. |
| `03_BUILD_PLAYBOOK.md` | A phased, step-by-step plan with **ready-to-paste prompts** and guardrails for the new cowork. |
| `04_CONTENT_GUARDRAILS.md` | How to source and validate non-math content without hallucinating. Short and critical. |
| `05_PRODUCT_AND_MONETIZATION.md` | JEE/NEET market, the multi-app strategy, pricing, moat, go-to-market. |
| `SEED_CLAUDE.md` | A starter working-memory file to drop into the new app's repo so its cowork has the architecture from day one. |

---

## How to use it

**If you (Anand) are reading:** start here, then `02` (what you actually own and can reuse) and `05` (where the money is). `03` is the execution plan you'll hand off.

**If a new Cowork/Claude session is reading** (e.g. you started a fresh space to build "JEE Spark"):
1. Read `01` and `02` to understand the platform you're forking.
2. Read `04` **before touching any content** — it's the rule that stops you hallucinating.
3. Follow `03` phase by phase. The paste-ready prompts are written so you can run them with light edits.
4. Drop `SEED_CLAUDE.md` into the new repo as its `CLAUDE.md` and grow it as you go.

---

## What "a mini-app" means here

Not a separate codebase per exam. The end state is **one platform, many skins**:

- **Shared backend + engine + economy** (the Kiwimath spine, reused).
- **Per-exam content packs** (JEE pack, NEET pack, …) loaded the way Kiwimath loads its levels today.
- **Per-exam app builds** that differ mostly in branding, the taxonomy labels, and which content pack they point at.

Build the first one (say NEET) as a clean fork to prove the pattern, then collapse the shared parts into a common core so app #2 and #3 are mostly content + branding. `05` covers when to split vs. share.
