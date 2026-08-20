# Athru Roadmap

**Document:** SPEC-07
**Version:** 0.1.0
**Status:** Draft

## 1. Introduction

This document lays out the phased path from specification to a working browser.
The order is chosen so each phase produces a demonstrable artifact that the next
phase builds on:

- Language (SPEC-01) → Compiler (SPEC-02) → Bytecode (SPEC-03) →
  Runtime (SPEC-04) → Render Engine (SPEC-05) → Security (SPEC-06) →
  Browser shell.

The end goal of the first release is a desktop browser (`athru-web`) that links
the render engine as a core module (Vulkan-style API) and runs compiled Athru
packages.

## 2. Phase Lines

### Phase 0 — Foundation and Tooling

- Choose the implementation language (Rust recommended).
- Set up repository workspaces: `athru-page-compiler`, `athru-render-engine`,
  `athru-web`.
- CI, formatting, and test hygiene.
- Decide native windowing (e.g. winit/GLFW) and GPU backends for the engine.

### Phase 1 — Language (SPEC-01)

- Define the minimal C-family, declarative-first grammar.
- Widgets: `text`, `box`, `button`, `image` (video later).
- State declarations, style blocks, input fields, functions.
- Static type checking.

**Artifact:** grammar + parser + pretty-printer, test corpus.

### Phase 2 — Compiler (SPEC-02)

- Lexer, parser, semantic/type analysis.
- Static dataflow graph construction (state→instruction edges).
- Redraw region computation.
- Bytecode emission (SPEC-03).

**Artifact:** CLI `athru-page-compiler` turns sample `.ath` into valid
`.athp` bytecode.

### Phase 3 — Bytecode format (SPEC-03)

- Fixed header/sections, scene instruction set (baseline opcodes).
- Dataflow table, region table, input table, constants/assets.
- Package format + validator.

**Artifact:** bytecode reader/validator + tests.

### Phase 4 — Render Engine API (SPEC-05, the core)

- Implement the Vulkan-style C ABI (`ath_load_scene`, `ath_draw_region`, ...).
- Scene loader validating bytecode.
- Immediate-mode draw loop: walk region instructions, issue draws.
- CPU rasterizer first (simplest), then GPU backend (Vulkan).
- Text shaping via a shaping library.
- Draw-time input access: `input.*` read by instructions, drive re-render
  through the dataflow graph.

**Artifact:** `libathru.so` that takes bytecode as input and returns rendered
frames.

### Phase 5 — Runtime / App VM (SPEC-04)

- Load `.athp` package, own `StateBlock`.
- Build the dataflow query interface (state/input → region).
- Sample OS input into the `InputBlock` per the bytecode's Input Table.
- Wire App VM to engine: sample-input + begin/draw/invalidate/end-frame.

### Phase 6 — Browser shell (`athru-web`)

- Link engine as a module (Vulkan-style), own the window and swapchain.
- Load/build scene from package manifest.
- Sample pointer/key/focus input each frame and forward as an `inputBlock`.
- Open/close tabs (multiple scenes per context).
- Window composition of regions.

**Artifact:** a windowed desktop app running an Athru package end-to-end.

### Phase 7 — Security hardening (SPEC-06)

- Optional engine process isolation with shared-memory transport (API
  unchanged).
- Asset budgets, validate-at-load, per-frame draw budgets (mostly implemented
  along the way).

### Phase 8 — Language growth

- Flexible layout (flex/grid).
- `video` surfaces.
- A11y tree from region+widget metadata.
- Package signing / verified distribution.

## 3. Dependencies & Order

```
Language ─▶ Compiler ─▶ Bytecode ─▶ Engine ─▶ Runtime ─▶ Browser
```

The compiler depends on the language definition; the engine depends on the
bytecode format; the browser depends on both runtime and engine.

## 4. Milestones (Acceptance Criteria)

- **M1 (Phase 0-3):** `athru-page-compiler` emitted a bytecode file.
- **M2 (Phase 4):** Engine renders a `text`+`box` scene to a CPU frame.
- **M3 (Phase 5):** Moving the pointer reprocesses only the region whose draw
  reads the pointer, via the dataflow graph.
- **M4 (Phase 6):** `athru-web` window runs a packaged `.athp` with
  immediate-mode interaction (input sampled as state during draw).
- **M5 (Phase 7):** Engine process isolation release: untrusted package cannot
  crash the browser.

## 5. Open Decisions

- Implementation language (Rust recommended).
- Exact widget set/opcode numbering before Phase 2 (SPEC-03).
- Backend ordering (CPU-first then Vulkan, or both).
- Across concrete syntax — token set is a proposal, refine in Phase 0.

## 6. Definition of Done for the Project

A desktop browser that:

- compiles Athru source (dev-only) → bytecode,
- loads bytecode from a package,
- renders immediately without a DOM/VDOM/interpreter/JIT,
- redraws precisely via the embedded dataflow graph and regions,
- reads input as sampled state during draw (no event handlers),
- and confines untrusted content inside a safety boundary.

## Summary

The phased plan turns the specifications into a working system incrementally:
language → compiler → bytecode → engine → runtime → browser → security. Each
phase's artifact is usable and testable on its own.
