# Athru Runtime (App VM) Specification

**Document:** SPEC-04
**Version:** 0.1.0
**Status:** Draft

## 1. Introduction

The runtime component in Athru is the **App VM**. It is the part of the host
(`athru-web`) that:

- loads a `.athp` package,
- owns all mutable application state,
- samples and exposes current input as read-only state,
- and drives the render engine (SPEC-05) to produce output.

The App VM holds the bytecode in memory. It does **not** interpret a general
instruction stream, does **not** compile anything, and does **not** run event
handlers. Interaction is immediate-mode: the latest input is read during draw,
and the App VM only supplies state plus a sampled input-state block to the
engine each frame.

## 2. Relation to the Engine

The engine (SPEC-05) is a Vulkan-style API that takes bytecode plus a state
block (and input state) and returns rendered output. The App VM:

1. Holds mutable state in a fixed-layout `StateBlock`.
2. Samples current input (pointer, keyboard, focus) into the `InputBlock` whose
   layout the bytecode's Input Table describes (SPEC-03 §7).
3. Each frame calls `athruDrawFrame(scene, stateBlock, inputBlock)`, drawing all
   or dirty regions.
4. When a state changes, consults the DATAFLOW table to decide which regions to
   invalidate and calls `athruInvalidate(region)`.

There is no event path. The engine reads `input.*` during draw; it never
dispatches a callback, never fires a handler.

## 3. Process Model

- By default the App VM and the render engine live in **one process**, with the
  engine linked as a module (a "core module" / Vulkan-style API).
- For hardening, the engine can be placed in a separate process with the API
  transport bridged (SPEC-06). The VM-facing contract is identical in both
  modes.

## 4. Loading a Package

1. `AthruApp.load(path)` reads the manifest and bytecode.
2. Bytecode is validated (SPEC-03 §11).
3. State is allocated from the state declarations encoded in the bytecode's
   CONST/DATA tables; initial values are initialized.
4. The engine module performs `athruLoadScene(bytecodeBlob)` and returns a
   scene handle, the region map, and the input layout.

Any failure aborts loading; no partial app runs.

## 5. State Ownership

- All mutable state is owned by the App VM and stored in one contiguous,
  fixed-layout `StateBlock` described by the bytecode.
- State is identified by `STATE_ID`s referenced in the DATAFLOW table.
- The VM passes the `StateBlock` to the engine at draw time (as a read-only
  view). The engine never writes to it.

### 5.1 InputState

- Separate read-only block (`InputState`) allocated/filled by the App VM each
  frame from the OS input snapshot.
- Layout governed by the bytecode's Input Table (SPEC-03 §7) so the engine can
  read fields by offset.
- Fields include pointer position/buttons, keyboard keys, focus. Written, not
  dispatched; read during draw.

## 6. Per-Frame Flow

```
loop (vsync / redraw requested):
  1. App VM samples input → InputState (per bytecode Input Table layout)
  2. athBeginFrame(surf)
  3. for each dirty region (from invalidation map):
       athDrawRegion(surf, region, stateBlock, inputBlock)
     (or athDrawScene(surf, stateBlock, inputBlock) on first frame)
  4. athEndFrame(surf)
```

There is **no event queue, no dispatch, no bubbling**. The engine decides what
an input hit means purely from the current input during a draw.

## 7. The Dataflow Query Interface

```
deps = vm.resolveDependents(depId)   → set of region IDs (state or input)
```

- Called whenever a state value changes to decide invalidation.
- Input changes are handled at frame granularity: on input change, the VM (or
  host) invalidates the regions the dataflow table binds to the changed input
  field; unchanged regions are skipped.
- Maps the state/input → region mapping into the engine's invalidation API.

## 8. Animation / Time (design note)

- Continuous timers drive redraws by mutating a `time` state each tick; the
  dataflow graph then invalidates only the regions that read `time`.
- No global full-frame redraw requirement.

## 9. Interfacing with the Render Engine

The App VM drives the engine through a small client API (defined fully in
SPEC-05):

```
scene = athLoadScene(ctx, &bytecode, len)
surf  = athCreateSurface(scene, w, h)
athSetInput(surf, &inputBlock, inputLen)      // sampled input
athBeginFrame(surf)
athDrawRegion(surf, regionId, &stateBlock, stateLen)
athEndFrame(surf)
athInvalidate(surf, regions, nRegions)
```

The VM never touches the GPU directly.

## 10. Loading and Updating Assets

- Fonts, images, and video are requested from the package asset store.
- Bytecode references them by `assetId`; the VM hands the loaded asset to the
  engine cache (bitmap/font) rather than the engine loading files itself.

## 11. Potential Failure Modes / Robustness

- Corrupt bytecode → refused by validator (§4).
- Region arithmetic overflow → clipped to viewport or error.
- Malformed InputState layout → treated as load-time error.

## 12. Security Surface

- The VM runs no arbitrary code and no handlers; the only "execution" is
  drawing, driven by valid bytecode and bounded state.
- The engine gets a sandboxed view (a memory blob of validated bytecode plus
  read-only state) and a capability-based API (SPEC-06).
- No network or filesystem unless granted by the package manifest.

## Summary

SPEC-04 defines the App VM: package loading, state ownership, input sampling,
and the dataflow-driven invalidations that tell the engine exactly what to
redraw — with no DOM, no event queue, and no handlers. It depends on SPEC-03
(bytecode) and SPEC-05 (engine API).
