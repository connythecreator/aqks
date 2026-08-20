# Athru Security Specification

**Document:** SPEC-06
**Version:** 0.1.0
**Status:** Draft

## 1. Introduction

Athru is designed from the ground up for memory safety and capability-based
sandboxing. The platform removes the most damaging legacy web attack surfaces
at their root:

- No arbitrary JavaScript execution.
- No DOM, so no DOM-based injection/scripting.
- No union of untrusted content by the engine (it only reads validated
  bytecode).
- No JIT, so no runtime code generation.

This document defines the security model across the App VM, the render engine,
and the host/browser.

## 2. Threat Model Summary

- Contents of a package is data moving the engine (bytecode) and the App
  VM (state + input). Both are treated as untrusted.
- The engine runs in the same memory or a separate process (hardening), but in
  every case bytecode is validated before interpretation.
- The host/browser is the trusted boundary.

## 3. Memory Safety

Fundamental principle: memory safety at the language and runtime level.

- **Implementation language.** The engine and compiler are to be implemented in
  a memory-safe language (Rust recommended). This dominates the entire security
  posture.
- **No unsafe graphics transparency** unless strictly necessary and fenced.
- **Bounds.** All region/instruction/state indexes validated in the loader
  (SPEC-03 §11) and the engine (SPEC-05). Out-of-range access is an abort-and-
  retry of the frame, never UB.

## 4. The App VM and its Safety Properties

- The runtime performs **no arbitrary code execution and no event handling**.
  Package content is never executed as a program: it is validated bytecode that
  the engine draws with, plus fixed state and sampled input read during draw.
  There are no function pointers into untrusted memory and no dynamic code.
- State is a fixed-layout `StateBlock`. The VM passes it to the engine read-only;
  it never lets the engine write state.
- Input is a fixed-layout read-only block the host writes each frame; nothing
  executes in response to it — it is merely data read at draw time.

## 5. The Engine Sandbox

The engine accepts only:

- a validated bytecode blob,
- a read-only `stateBlock` (copy or shared, read-only),
- a read-only `inputBlock`,
- a set of region IDs,
- asset data it loaded itself.

The engine's contract is **capability-based**: the engine is a library that can
draw and load fonts/assets registered by the App. It cannot:

- access network,
- read files (except via explicit asset registration),
- allocate unbounded memory (region budgets and frame budgets),
- touch other process memory.

## 6. Optional Process Isolation (Hardening)

By default the engine is linked in-process as a module. The recommended
hardening tier splits engines into a separate process:

- The bytecode blob and state are shared read-only via shared memory.
- The engine returns either a Shm "region" (temp rendered) or commands; the
  host composites.
- The engine's failure (crash, oom) is contained: the browser shows the region
  in place of live content without killing the whole session.
- A separate engine process also isolates GPU-driver faults.

The **API remains unchanged** across both modes (SPEC-05) — this is the key:
Vulkan-style API is transport-agnostic.

## 7. Sandbox of Assets

- Images/these extracted only to fixed-size bitmap caches with
  decompression-bomb limits decided at load.
- Font loading from package is validated by a parser; no exec.
- Video decode fenced to a separate codec thread/process.

## 8. Filesystem & Network

- No arbitrary file read/write from a package unless manifest-granted.
- The `.athp` manifest lists explicit permissions (SPEC-03 §9.1). The App VM
  enforces them.
- No network APIs in the initial drop (deferred).

## 9. Validate-at-Load

Loader (both engine and VM) validation described in SPEC-03 §11. Bytecode that
fails to validate is refused. Nothing runs. No partial state.

## 10. Deterministic execution

- Engine draw deterministic (SPEC-05 §13) enables cross-implementation test
  binaries: same bytecode + state ⇒ same output. Good for auditing.

## 11. Distribution & Supply chain

- The `.athp` package can carry a signature in the manifest; the host verifies
  before handing bytecode to the engine (not implement now).

## 12. Deployment Notes

- In-process mode is suitable for trusted local UI.
- For loading untrusted packages, use process isolation (at a minimum).

## Summary

Athru's security is defense-in-breadth: memory-safe implementation, no arbitrary
code execution over packages (no handlers, no event dispatch), and validated
bytecode through a capability-based, Vulkan-style API that only draws. The
optional engine process isolation creates a browser-grade fault barrier without
changing the interface. The threats of `window/document` injection, XSS-style
script execution, and JIT-based escalation are non-existent by construction.
