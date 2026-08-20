# Athru Render Engine API Specification

**Document:** SPEC-05
**Version:** 0.1.0
**Status:** Draft

## 1. Introduction

The render engine (`athru-render-engine`) is the core unit of Athru. It is a
**core module / library** exposing a **Vulkan-style C ABI**. It takes bytecode
as input and produces rendered output. This document defines the API that a
host (the browser `athru-web`, or any embedder) links against.

The engine is deliberately simple at its boundary:

- **Input:** a validated Athru bytecode blob (SPEC-03).
- **Output:** rendered frames (GPU-first, CPU fallback).

It never runs application logic. It never parses source. It has no DOM. It has
no interpreter loop.

## 2. Design Principles

1. **Vulkan-style API:** global handles, explicit `ath*Create*`, resource
   lifetime, command-style draw, no hidden global state.
2. **C ABI.** Stable and callable from any language/embedding.
3. **Bytecode-centric.** The scene is loaded from bytecode, not built in code.
4. **Region-aware.** The engine redraws regions, not whole pages.
5. **Immediate-mode draws.** Each frame draws only what is needed; input is read
   as state during draw. No event dispatch, no hit-test pre-pass.
6. **GPU-first with CPU fallback.** Backends: Vulkan (Linux/Windows), Metal
   (macOS), optional DirectX; a software rasterizer as fallback.
7. **Deterministic and repeatable.** Given the same bytecode + state + input,
   the output at a given frame is stable.

## 3. Naming and Library

- Library names: `libathru.so` / `libathru.dll` / `libathru.dylib`.
- All symbols prefixed `ath_`.
- Header `athru.h`, C11, and a thin C++ wrapper for ergonomics.
- Threading: all engine state is owned by one logical "context"; the API is
  callable from a single thread per context unless noted.

## 4. Core Model

```
   Athru Context (device)
        │
        ├── SceneHandle  ← athLoadScene(bytecodeBlob)  →  walkable scene
        │        └── Region(s) (redraw regions + instruction lists)
        │        └── Input layout (from bytecode Input Table)
        │
        └── Surface / Output (backbuffer)
```

Multiple scenes may exist in one context (e.g. tabs in the browser).

### 4.1 GPU / CPU Backends

- Selection at context creation via `char* backend`.
- Abstract **Renderer** interface: `begin_frame`, `command draws`, `end_frame`.
- GPU: builds a command buffer from the region's instruction list.
- CPU: rasterize region bounds into a backing bitmap then blit.

Both honor region coords; the API does not care.

## 5. Core API (C declarations)

```c
// Context / device
athResult athInitContext(athBackendType backend, athContext* out);
void      athDestroyContext(athContext ctx);

// Scenes (from bytecode)
athResult athLoadScene(athContext ctx, const uint8_t* bytes, size_t len,
                       athScene* out);         // validates (SPEC-03 §11)
void      athDestroyScene(athScene scene);

// Surfaces and draw
athResult athCreateSurface(athScene scene, int w, int h, athSurface* out);
void      athDestroySurface(athSurface surf);

// Input state (sampled each frame by the host; layout from Input Table)
athResult athSetInput(athSurface surf, const void* inputBlock, size_t inputLen);

// Per-frame
athResult athBeginFrame(athSurface surf);
athResult athDrawRegion(athSurface surf, uint32_t regionId,
                        const void* stateBlock, size_t stateLen);
athResult athDrawScene(athSurface surf, const void* stateBlock, size_t stateLen);
athResult athEndFrame(athSurface surf);

// Invalidation / regions (driven by dataflow, supplied by App VM)
athResult athInvalidate(athSurface surf, const uint32_t* regions, size_t nRegions);

// Text / assets
athResult athLoadFont(athContext ctx, const uint8_t* data, size_t len,
                      athFont* out);
athResult athRegImage(athContext ctx, athImage* out);
athResult athQueueVideo(...);   // future
```

## 5.1 Key behavior

- `athLoadScene` validates the bytecode (magic/version/section/dataflow bounds)
  exactly (SPEC-03 §11). On failure it returns an error; nothing else runs.
- `athDrawRegion` takes the current `stateBlock` (the VM's StateBlock, SPEC-04
  §5) and `inputBlock` (set via `athSetInput`) and runs only that region's
  instructions. Widgets read `input.*` during draw.
- Regions not invalidated are skipped; `athDrawScene` draws all regions.
- `athInvalidate` records which regions are dirty for the next frame.
- There is **no** event dispatch and **no** hit-test API in the engine. Input
  is sampled into the input block; its effect on rendering is a draw-time
  decision of each instruction.

### Example lifecycle

```
ctx   = athInitContext(...);
scene = athLoadScene(bytes, len);
surf  = athCreateSurface(scene, 1280, 800);
stateBlock = ... // VM-owned memory; inputBlock sampled by host each frame

loop (vsync)
  athSetInput(surf, inputBlock);            // sampled pointer/keys/focus
  athBeginFrame(surf);
    for r in dirtyRegions: athDrawRegion(surf, r, stateBlock);
  athEndFrame(surf);
  // host/VM decides region invalidation from the dataflow graph
```

## 6. Dataflow-driven drawing

```
athLoadScene     — loads bytecode the scene built by compiler
athInvalidate(regions) — marks regions whose state changed
athDrawFrame     — walks the SCENE section; for regions in current set, runs
                   their instructions with the current stateBlock
```

The engine is *told* which regions to draw (by the VM using the dataflow
graph). It does not perform dynamic reconciliation or dependency discovery.

## 7. Text Rendering

- Fonts: `ath_load_font` + `ath_draw_text`.
- Text shaping: a shaping library (e.g. Harfbuzz) used internally. Shaping is
  deterministic.
- Layout is provided as declarative bounds (SPEC-01); the engine lays out text
  runs and rasterizes them.

## 8. Accessibility (future baseline)

- Engine gives hit/region/tree info (bounds per region) to the host.
- A11y tree from region bounds + widget names in the bytecode.

## 9. Video

- Draw command `DRAW_VIDEO` (0x04); content decoded out-of-band; regions
  presented per frame.

## 10. Swapchain and Composite

- One output backbuffer per surface.
- On `ath_end_frame`, regions drawn swap the partial surface; compositor blends
  to window (GPU or CPU).
- The browser owns the window; the engine owns drawing into it.

## 11. Error Handling

All engine functions return `athResult`:
```
ok, invalidBytecode, invalidRegion, outOfMemory, backendUnsupported, badStateBlock, badInputBlock
```

Errors do not crash the host: the engine sanitizes region bounds and aborts a
frame with a benign partial draw, then reports.

## 12. Thread-Safety

- A single context must not be used concurrently for draws without external
  lock; the engine documents which calls are allowed from other threads
  (e.g. `ath_load_font` pre-loadable before frame loop).
- Multiple surfaces on one context are valid.

## 13. Determinism

- Rendering a region with the same state (input) yields the same draw commands
  in the same order. This aids testing, caching, and offline snapshots.
- No global randomness in the engine.

## 14. Extensions

The ABI is versioned. Feature flags cover: GPU backends, video, custom
shader/widget code, fair additions in the SCENE graph. Unknown extensions are
ignored gracefully.

## 15. Scope Note

The engine is the future core of the browser. Like a Vulkan API it is a
`core-module-like` interface: the browser (`athru-web`) links it as a module and
does not hard-code a particular engine implementation's internals.

## Summary

SPEC-05 defines the render engine: a Vulkan-style C ABI that takes Athru
bytecode as input, reads the current state and sampled input during draw, and
produces rendered frames, drawing only flagged regions, GPU-first with a CPU
fallback. It never interprets application code, never has a DOM, and never
dispatches events. It is the contract that the App VM (SPEC-04) drives and the
browser (`athru-web`) links.
