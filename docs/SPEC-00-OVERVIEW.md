# Athru Overview

**Document:** SPEC-00
**Version:** 0.1.0
**Status:** Draft

## 1. Purpose

Athru is a complete redo of the web technology stack. It replaces HTML, CSS, and
JavaScript, and the legacy browser engines (Chromium/Blink and Gecko/Servo-style
engines) that interpret them. Athru is an immediate-rendering system that relies on
neither a DOM nor a Virtual DOM.

This document is the entry point to the Athru specification set. It defines the
vision, the non-negotiable design constraints, the architecture, the data flow
from source to pixels, and how the three subsystems relate to one another.

## 2. Vision and Goals

- Provide a **single unified language** that expresses structure, style, and
  logic together. There is no separation into an HTML (structure), CSS (style),
  and JS (logic) triplet.
- **Compile to native, declarative-first** output. Source is compiled into a
  compact custom bytecode that the runtime loads directly.
- **Immediate rendering**, with **no DOM and no Virtual DOM**. Interaction is
  not handled through events: the latest input (pointer, keys, focus) is exposed
  as read-only state and is read *during* draw, so widgets derive their own
  response from current state plus current input each frame.
- **Compile-time dependency tracking** so that UI updates are precise and cheap:
  the compiler constructs a static dataflow graph and embeds it in the bytecode,
  so the runtime never has to discover dependencies dynamically.
- Replace the legacy browser engines with a **Vulkan-style rendering engine
  API**: bytecode in, rendered frames out. The engine is a linkable core module.
- **Memory safety and sandboxing** as first-class properties.

## 3. Non-Goals

- Supporting HTML, CSS, or JavaScript content natively. Athru is a clean-break
  native-first platform. Legacy content support is explicitly deferred
  (see SPEC-07 Roadmap).
- Packaging a general-purpose interpreter or JIT into the runtime.
- Including a compiler in normal application runtime.
- Mobile, embedded, or server targets in the first milestones. Athru targets
  desktop first (Linux, macOS, Windows).

## 4. Glossary

| Term                 | Definition                                                              |
|----------------------|------------------------------------------------------------------------|
| **Athru source**     | The unified language file(s) authored by developers. `.ath` source. |
| **Compiler**          | A dev-time tool (`athru-page-compiler`) that turns source into bytecode.|
| **Bytecode**          | A custom, raw binary format containing rendering instructions, the dataflow graph, and redraw regions. |
| **Package**           | A single distributable `.athp` file containing bytecode plus assets and a manifest. |
| **Scene**             | The compiled representation of a page/application that the engine walks to render. |
| **Dataflow graph**    | A static graph, computed at compile time, mapping state variables to the rendering instructions that depend on them. |
| **Redraw region**     | A screen region whose rendering instructions can be re-run independently. |
| **App VM**            | The runtime component that owns state and supplies it (plus current input state) to the engine for drawing. |
| **Render Engine**     | The `athru-render-engine` core module. A Vulkan-style C ABI library that takes bytecode and produces rendered output. |
| **Host / Browser**     | The `athru-web` application/process that links the engine and hosts the App VM. |
| **Input state**       | Read-only current input (pointer, keys, focus) available during draw; widgets derive responses from it. |

## 5. Design Constraints (Non-Negotiable)

These constraints shape every other document in this set. They cannot change
without invalidating the specification.

1. No DOM. No Virtual DOM. No generic interpreter loop. No JIT. No event
   dispatch. True immediate-mode: input is read as state during draw.
2. The compiler never runs in normal application runtime. Compilation happens
   only in development environments to produce bytecode.
3. The engine is a core module / library with a Vulkan-style API. It does not
   run application logic; it takes bytecode as input and produces output.
4. State is owned by the App VM. Redrawing is driven by the embedded dataflow
   graph and redraw regions.
5. The language is C-family in syntax and declarative-first, with widgets that
   relate to HTML tags (e.g. headings, video) without being HTML.
6. The bytecode is custom to Athru and is intentionally a "basic" rendering
   instruction set, analogous to widgets rather than to general-purpose machine
   code.

## 6. The Three Subsystems

The repository is structured around three top-level subsystems. The relation
between them is module/API based, not a strict process topology.

### 6.1 `athru-page-compiler`

A development-time tool. It parses Athru source, performs semantic analysis,
builds the static dataflow graph, and emits the custom bytecode and `.athp`
package. It is never linked into or invoked by the runtime.

Specified in depth in [SPEC-02-COMPILER.md](./SPEC-02-COMPILER.md).

### 6.2 `athru-render-engine`

The core of the platform and the central design. A **Vulkan-style API** —
a linkable module (library) exposing a C ABI. It takes bytecode as input and
produces rendered output. It walks the bytecode each frame, issues
immediate-mode draw calls, uses the GPU when available (Vulkan on Linux/Windows,
Metal on macOS, DirectX as supported), and falls back to CPU rendering.

The engine relationship to the bytecode-based dependency model:

- loads scene bytecode into memory,
- walks the embedded rendering instructions,
- emits draw calls per redraw region,
- re-runs only the instructions that the dataflow graph maps to a changed
  state.

SPEC-05 defines the engine. See [SPEC-05-RENDER-ENGINE-API](./SPEC-05-RENDER-ENGINE-API.md).

### 6.3 `athru-web`

The browser / host process. It links the engine as a module (like a core module
or a Vulkan API), owns the App VM and all mutable state, samples and exposes
input state, loads packages, and presents the engine output. It is the
user-facing surface.

See [SPEC-04-RUNTIME](./SPEC-04-RUNTIME.md).

## 7. Data Flow: Source to Pixels

```
DEV TIME (athru-page-compiler):
   .ath source
   ├─ lexer
   ├─ parser (widget tree, C-family syntax, unified structure/style/logic)
   ├─ semantic analysis / type resolution
   ├─ state + input-state analysis
   ├─ static dataflow graph construction
   ├─ redraw region computation
   └─ bytecode emission (+ asset packaging)
        └─ .athp package (bytecode + graph + regions + assets + manifest)

RUNTIME (athru-web + engine):
   .athp package
   ├─ App VM: loads bytecode raw into memory, owns mutable state
   ├─ Host samples input → input-state block (pointer/keys/focus)
   ├─ per frame: engine athruDrawFrame() reads state + input-state during draw
   └─ state change: dataflow graph → athruInvalidate(region) → re-run region
        instructions (never event dispatch)
```

## 8. Topology

Athru is module-based. By default the engine is linked into the same process as
the App VM and the host. A recommended hardening layer splits the engine into a
separate process so that no rendered content is untrusted memory is co-located
with the state VM. This is a deployment choice; the Vulkan-style API boundary
remains the same. See [SPEC-06-SECURITY](./SPEC-06-SECURITY.md).

## 9. Roadmap Summary

The project moves from language to browser:

1. Language design (SPEC-01)
2. Compiler (SPEC-02)	                    production of bytecode; "SPEC-03
3. Bytecode & package format (SPEC-03)
4. Runtime / App VM (SPEC-04)
5. Render Engine API (SPEC-05)
6. Security hardening (SPEC-06)
7. Browser shell and packages (SPEC-07)

See [SPEC-07-ROADMAP](./SPEC-07-ROADMAP.md) for the phased breakdown.

## 10. Document Index

| Doc       | Title                   | Scope                                        |
|-----------|-------------------------|----------------------------------------------|
| SPEC-00   | Overview                | This document                               |
| SPEC-01   | Language                | Atha language, syntax, widgets, state model |
| SPEC-02   | Compiler                | Dev-time tool, pipeline, dataflow graph     |
| SPEC-03   | Bytecode                | Instruction set, graph encoding, package    |
| SPEC-04   | Runtime                 | App VM, state, input sampling, immediate draw   |
| SPEC-05   | Render Engine API       | Vulkan-style core module API                 |
| SPEC-06   | Security                | Safety, sandboxing, API boundary             |
| SPEC-07   | Roadmap                 | Milestones                                   |

---

This document is normative for the structure of the project. It is intended to
be implemented exactly as specified, with no DOMs and no interpreter loops, from
the lowest level up.
