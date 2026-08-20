# Athru Compiler Specification

**Document:** SPEC-02
**Version:** 0.1.0
**Status:** Draft

## 1. Introduction

The compiler is the component (`athru-page-compiler`) that turns Athru source
into custom bytecode and a distributable `.athp` package. It runs only in
development environments. It is never linked into nor invoked by the runtime.

The compiler is special because it is where the platform's core idea lives: it
constructs the static **dataflow graph** that lets the runtime re-render without
a DOM. All discovery of "which state affects which drawing" happens here, once,
at compile time.

## 2. Non-Goals

- No interpreter. No JIT. The compiler emits a fixed binary artifact.
- The compiler does not draw anything. It has no rendering path.
- No requirement to run on hardware in production.

## 3. Pipeline

```
Source (.ath files)
        │
        ▼
  01 Lexer                 → tokens
  02 Parser                → AST / widget tree
  03 Semantic Analysis      → typed AST, widgets, imports resolved
  04 State & Dataflow Scan   → build state→instruction edge set
  05 Redraw Region Analysis  → compute independent draw regions
  06 Bytecode Emission       → custom bytecode + graph + regions
  07 Asset & Manifest        → .athp package
```

The compiler produces exactly one primary artifact: bytecode that SPEC-03
defines. It also reports diagnostics to the developer.

## 4. Stages

### 4.1 Lexer

- Runs over the source text.
- Produces tokens: keywords, identifiers, literals, punctuation.
- Reports unterminated string/block comment errors.

### 4.2 Parser

- Produces an AST representing widget declarations, style blocks, state
  declarations, functions, and uses of `input` in draw-time expressions
  (SPEC-01).
- Handles imports/`use` of other `.ath` files into one module graph.
- Enforces C-family structure. Errors on malformed blocks.

### 4.3 Semantic Analysis and Typing

- Resolves widget built-in names, type-checks, and matches props to widget
  signatures (`text`, `box`, `button`, `image`, `video`, ...).
- Checks that every `state` is declared before use within its widget.
- Checks `fun` signatures and types.
- Resolves every `input.*` reference to a well-typed input field.
- Produces a typed, resolved IR of the whole program.

### 4.4 Static Dataflow Analysis (State/Input → Instruction)

This is the core algorithm.

1. Traverse the AST.
2. For every reference to a `state` variable or an `input.*` field (in style
   props, widget props, text content, `if` conditions, and function calls),
   record the resulting rendering instruction as a dependent.
3. Emit the edge set:
   ```
   state ID ──▶ target instruction ID
   input ID ──▶ target instruction ID
   ```
   The target is usually the instruction that paints the text or the surface
   whose value changed.

The result is the **dataflow table** that goes into the bytecode (SPEC-03 §5).
Only reads observed during draw establish edges.

### 4.5 Redraw Region Analysis

The compiler partitions the scene into **regions** (groups of rendering
instructions). A region has a host rectangle and a set of instruction IDs.

- Reads the dataflow table to see which regions change when a given state or
  input field changes.
- Emits, for each state and each input field, the set of affected region IDs.
- The engine's surface of redrawing is per-region.

The renderer then can `athruInvalidate(region)` and re-run only that region's
raw instructions with current state and input.

### 4.6 Bytecode Emission

Outputs the bytecode per SPEC-03:

- scene section (instructions)
- dataflow table
- region table
- constant/asset table
- entry point

Bytecode is a `raw file` — not a script, not text, not a ZIP of virtualized
executables. It has no interpreter; the renderer loads it in-memory and walks
it directly (SPEC-04/05).

### 4.7 Asset + Packaging

Assets (fonts, images, video) are packed into the package alongside the
bytecode. Output is a single `.athp` (package) file or an unpacked directory for
debug.

## 5. Incremental Builds

- The compiler caches parse/typing results keyed by file hash and dependency
  graph.
- On edit, only the affected module(s) are re-parsed and re-analyzed; the
  dataflow graph for unchanged modules is reused.
- The output is still a single coherent bytecode with a merged dataflow table.

## 6. Dev Tooling

- `ath ru page-compiler` is a CLI used in dev, implementing:
  - `ath-compile input.ath -o app.athp`
  - `ath-preview input.ath` — launches a preview against a test host.
  - `ath-inspect app.athp` — dump sections (scenes, dataflow, regions) for debugging.
- Hot reload / live preview is driven by the compiler producing a new package
  that the preview runtime loads (see SPEC-04/05), not by a running interpreter.

## 7. Diagnostics

Compiler errors are classed:

- Lexical
- Syntactic
- Semantic / typing
- Dataflow (e.g. "state `count` read in two widgets; ambiguous region")

The compiler refuses to emit a package if dataflow graph is incomplete.

## 8. Portability Check

- The compiler is a development tool.
- It can be implemented in any suitable language (undecided; Rust recommended).
- It produces no platform-specific code other than a neutral bytecode.

All published .p file(s) (bytecode) are portable and OS-independent.

## Next

The actual bytecode connection — the format the compiler emits — is defined in
SPEC-03.
