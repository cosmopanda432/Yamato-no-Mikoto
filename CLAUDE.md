# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

yamatoLLM: constrained-decoding research on Qwen2.5-Coder. The core idea is a **firewall between
generation and evaluation** (`yomotsu_hirasaka.py`) plus **physical output constraints** (token
masking / reasoning-trace enforcement) so that invalid output is structurally impossible rather than
caught after the fact. The repo is organized as a sequence of experiments targeting different
languages (TypeScript → Go → Elixir), each living in its own `src_min_*` folder. Code and docs use
Kojiki/Shinto mythological names for technical concepts (see "Naming convention" below).

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"             # torch / transformers / peft / accelerate / pyarrow / pytest
pip install -e ".[quantization]"    # + bitsandbytes, for 4bit/8bit model loading
```

`pyproject.toml`'s `packages.find` points only at `src_min/`, so `pip install -e .` makes
`import kojiki_lm` resolve to `src_min/kojiki_lm/`. The other `src_min_*` variants are **not**
installed; code under `tests_go/` (and any equivalent for other variants) manually prepends its
target folder to `sys.path` before importing `kojiki_lm`.

`models/` and eval datasets under `data/` are large and mostly gitignored — see "data/ and
.gitignore" below.

## Tests

```bash
pytest tests/                 # src_min/ (TypeScript-target variant) — CPU only, no GPU needed
pytest tests_go/              # src_min_go/ (Go-target variant)
pytest tests/test_firewall.py::TestL3ToL5Payload::test_valid_payload   # single test
```

**Do not run `pytest tests/ tests_go/` together** (and do not point a single `pytest` invocation at
the repo root). Both suites import the same top-level module name `kojiki_lm` from different
directories (`src_min/` vs `src_min_go/` via manual `sys.path` insertion); whichever gets imported
first wins for the rest of the process, and the other suite's imports break. Run each test directory
in its own `pytest` invocation.

`src_min_eli2/` and `src_min_eli3/` have no unit test suites — they're validated via the eval
scripts below (ablation runs against MultiPL-E-style benchmarks), not pytest.

`src_min_elixir/` is a separate Mix project (archived, see below): `cd src_min_elixir && mix test`.

## Eval pipeline

Each language-target variant follows the same generate → score → judge pattern, e.g. for eli3
(Elixir + reasoning-trace variant):

```bash
python3 scripts/eval/run_yamato_min_elixir3.py \
    --input data/raw/multipl_e/humaneval-elixir/test-00000-of-00001.parquet \
    --out-dir data/eval/generated/humaneval-elixir.yamato_min_elixir3.koumyou-on.seed0 \
    --mode koumyou-on --quantize 4bit --seed 0

python3 scripts/eval/elixir_eval.py \
    --generated-dir data/eval/generated/humaneval-elixir.yamato_min_elixir3.koumyou-on.seed0 \
    --out-dir data/eval/results/humaneval-elixir.yamato_min_elixir3.koumyou-on.seed0
```

`judge_win_condition*.py` scripts (one per language target) do a 95%-CI statistical comparison
against `baselines/` to decide whether a variant beats the baseline (the project's "Win Condition").
These require a real model + GPU; they are not exercised by `pytest`.

## Architecture

### L3/L5 firewall (core mechanism, present in every variant)

`yomotsu_hirasaka.py` enforces a one-way, structurally-isolated boundary between:
- **L3** — the generation runtime (decode loop around the Qwen2.5-Coder backbone)
- **L5** — the evaluator (scores/validates generated text)

The boundary is a pair of frozen dataclasses (`L3ToL5Payload`, `L5ToL3Verdict`) plus a `Verdict`
enum (`commit`/`repair`/`halt`). `__post_init__` asserts reject anything that isn't a plain
str/int/float — in particular, tensors or model internal state cannot cross the boundary, by
construction rather than by convention. `src_min_elixir/` re-implements the same contract as BEAM
GenServers + `defstruct` guards, to test whether process isolation gives the same guarantee "for
free" in a different runtime (see its README — that line was abandoned because Bumblebee doesn't
support the target model, not because the idea failed).

### Kotodama (言霊) — constrained decoding via token masking

In `src_min/` (TypeScript target) and `src_min_go/` (Go target): `kotodama_token_mask.py` builds a
vocabulary of valid symbols/types and `kotodama_decoder.py` applies it as a `-inf` logit mask during
decoding, making invalid tokens physically unselectable. `kotodama_context.py` decides *when*
(which token positions) the mask applies.

This mechanism was **dropped** starting with `src_min_eli2/` (Elixir target): Elixir has no static
type system, so the masking has no clear vocabulary to constrain against, and ablations on the Go
variant showed its standalone contribution was hard to isolate. `src_min_eli2/firewall_decoder.py`
replaces `kotodama_decoder.py` with a version that keeps the firewall but drops the bias/masking
step.

### KoumyouSo (光明想) — reasoning-trace enforcement

`src_min_eli3/kojiki_lm/koumyou_so.py` is the newest mechanism (see
`docs/memo/2026-05-26_須弥山設計原理.md`): it forces the model to emit a `# 思考: ...` reasoning
trace before code, and HALTs generation if the trace is missing or too short. The intent is to make
it physically harder for the model to skip reasoning and jump straight to code. It's evaluated via a
3-arm ablation (`firewall-off` / `firewall-on` / `koumyou-on`) in
`scripts/eval/run_yamato_min_elixir3.py` to isolate the trace mechanism's effect from the firewall's.

### Variant map

| Folder | Target language | Status |
|---|---|---|
| `src_min/` | TypeScript | active; only variant that's `pip install -e`-able |
| `src_min_go/` | Go | active; has symbol oracle in `src_min_go/go_tools/` (Go binary, `go.mod`) |
| `src_min_eli2/` | Elixir | active; firewall only, kotodama masking dropped |
| `src_min_eli3/` | Elixir | active; eli2 + KoumyouSo reasoning-trace enforcement |
| `src_min_elixir/` | Elixir (BEAM-native) | **archived** — Bumblebee lacks Qwen2/Qwen3 MoE support, blocked at model-load step |
| `src/` | — | frozen reference copy of the original (pre-`src_min`) full implementation; read-only |
| `source_reference/` | — | ~13,500 LOC read-only reference implementation, consulted but not imported |

`src_min_eli2/` and `src_min_eli3/` are near-identical (eli3 is a full copy of eli2 plus the
KoumyouSo diff) — this duplication is intentional, to keep ablation comparisons clean rather than
risk a shared-code change silently affecting both arms.

### Naming convention

Modules and classes are named after Kojiki/Shinto mythology, mapped to technical roles (e.g.
`yomotsu_hirasaka` = 黄泉比良坂 = the L3/L5 evaluation gateway/firewall; `kotodama` = 言霊 = the
token-masking mechanism). The full god-name ↔ technical-role table is in
`docs/旧ドキュメント/glossary.md`. `docs/旧ドキュメント/architecture.md` describes the (larger,
not-yet-built) full-version design that the `src_min_*` variants are simplified subsets of.

### data/ and .gitignore

`data/` is currently **tracked** in git (holds `data/kojiki/` and `data/仏教宇宙論/`, source texts
for a separate research thread, ~29MB). This is a recent change — `data/` used to be entirely
gitignored because it also holds large generated eval artifacts (`data/raw/`, `data/eval/generated/`,
`data/eval/results/`, multi-GB MultiPL-E parquet files and generation dumps). Since `data/` is no
longer ignored wholesale, be careful not to `git add` generated eval output under it. Separately,
`.gitignore` ignores `*.json` repo-wide except `baselines/*.json` — eval result JSON files won't show
up in `git status` by default.
