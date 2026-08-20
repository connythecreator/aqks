# Athru Language Specification

**Document:** SPEC-01
**Version:** 0.1.0
**Status:** Draft

## 1. Introduction

The Athru language is the single source language for the entire platform. It
expresses structure, style, and behavior together in one C-family, declarative-
first syntax. There is no HTML/CSS/JS triplet and no separate styling language.

The language is compiled (at development time) into Athru bytecode. It is never
interpreted at runtime.

## 2. Design Principles

1. **Unified.** Structure, style, and logic live in the same declaration. A
   widget is one unit, not three.
2. **Declarative-first.** The developer describes what a UI is, not imperative
   per-frame how-to-draw steps. The compiler derives the rendering program.
3. **Immediate, no DOM.** The language has no notion of a Document Object Model.
   It produces a compiled scene. There is no DOM or Virtual DOM anywhere.
4. **Compile-time dependency tracking.** The compiler is the engine that powers
   redrawing; the language is expressive enough for the compiler to know, at
   compile time, which state feeds which rendered instruction.
5. **Widgets analogous to HTML tags.** Widgets such as `heading`, `text`,
   `video`, `image`, `button` map to familiar concepts without being HTML.
6. **Immediate-mode by default.** There are no event handlers. The latest input
   (pointer position/buttons, keys, focus) is exposed as read-only state that is
   read *during* draw. A widget derives its own response from current state plus
   current input each frame. No dispatch, no callbacks, no bubbling.
7. **C-family syntax.** Braces, semicolons, explicit blocks, type annotations.
8. **Memory safe.** No raw pointers in source. State is explicit and owned.
9. **Compiled native.** Source has no textual `script` or `style` tags; there is
   one declaration language.

## 3. Lexical Structure

- Case-sensitive identifiers; snake_case by convention for values, PascalCase
  for type/widget names.
- Keywords are reserved and cannot be identifiers.
- Comments: `// line` and `/* block */`.
- String literals: double-quoted with escape sequences.
- Numbers: integer and decimal literals, plus color literals `0xRRGGBB` and
  `0xAARRGGBB`.

### Keywords

```
widget state fun layout style
struct enum match if else for while return
in out const let impl input
```

### Whitespace and structure

- Braces `{}` delimit blocks.
- Semicolon `;` terminates statements where required.
- Widgets are declared with `widget` and composed by nesting blocks.

## 4. Widgets (Structure)

Widgets are the leaf and composite units of every Athru interface. Each widget
is a declaration that carries structure, style, and behavior.

### 4.1 Widget declarations

```
widget greeting {
    text "Hello"
}
```

- Widget identifiers are CamelCase.
- A widget body combines children widgets, state, style, and behavior.

### 4.2 Widgets analogous to HTML

The set of built-in widgets is intentionally "basic", analogous to HTML tags:

| Athru widget             | Analogy (not HTML)      | Purpose                       |
|--------------------------|--------------------------|--------------------------------|
| `text`                   | `<h>`/`<p>`              | Runs of text              |
| `image`                  | `<img>`                  | Raster images              |
| `video`                  | `<video>`                | Video surfaces             |
| `box`                    | `<div>`/`<section>`      | Rectangular containers     |
| `button`                 | `<button>`               | Interactable region        |
| `input`                  | `<input>`                | Text/entry input           |
| `link`                   | `<a>`                    | Navigation                 |
| `scroll`                 | scroll region            | Scrollable area            |

Each widget has a set of intrinsic props (e.g. `text: "…"`, `src: …`).

### 4.3 Widget composition

Deeper nesting builds the scene tree. The compiler lowers the widget tree into
an array of rendering instructions.

```
widget home {
  box {
    text "Hello"
    button label="Go"
  }
}
```

## 5. Style (Visual State)

Style is a first-class part of the `text`/`box`. It is expressed with typed
properties bound to constants or to state variables.

```
widget hero {
  box {
    style {
      width: 640
      height: 480
      background: 0xFFFFFF
      radius: 12.0
    }
  }
}
```

When a style property depends on state, the compiler registers a dataflow edge
from that state to the matching rendering instruction. This is how style
animation and interactions are expressed without a DOM.

### Fill properties

`background`, `foreground`, `opacity`, `radius`, `border`.

## 6. State

State is the source of rendering dependencies. State declarations are explicit,
typed, and live inside a widget.

```
widget counter {
  state count : i32 = 0
  box {
    text "count: \\(count)"
  }
  button label="+1"
}
```

State rules:

- A `state` only has one owner (the widget that declares it).
- The state graph is visible to the compiler globally; the compiler records
  the dataflow edges from every `count` read to the instruction that reads it.
- Values are never shared concurrently; no locks required by the language.

## 7. Input State (Immediate-Mode Interaction)

Athru has **no event handlers**. Interaction is implemented by reading live
input during draw. Each frame the host samples the current input and exposes it
as a read-only `input` value:

- `input.mouse.x`, `input.mouse.y` — pointer position
- `input.mouse.left`, `input.mouse.right` — pressed this frame
- `input.key.pressed` — set of keys
- `input.focus` — focused widget/region id (assigned by the compiler/layout)
- `input.touch` (deferred)

A widget derives its own response from state plus these inputs:

```
widget buttonWidget {
  state armed : bool = false
  box {
    // purely a draw-time decision from current input + state
    background: hitTest(input.mouse.x ) ? 0x7899FF : 0xCCCCCC
  }
  text "press"
}

bool hitTest(f) { region contains input.mouse.x, input.mouse.y }
```

Because the dataflow graph records every input-field read against the
instructions that read it, changing a mouse position invalidates exactly the
regions that depend on it; nothing needs collapsing subregions nor any event
dispatch.

Consequences:

1. **No event queue, no bubbling, no callbacks.**
2. Widgets are stateless between frames except `state`.
3. Continuous interactions (drag, hover) are naturally expressed: they're just
   functions of current input inter-frame; the dataflow graph handles it.
4. Hit testing is a by-product of drawing, not an input pre-pass.

A simple button press is expressed as a conditional in the style/layout:

```
button label="OK" {
  // "pressed" brightness derived from input.mouse during render
  fill: (within(this, input.mouse) ? 0x4A76E3 : 0x8899AA)
}
```

There is no mutation of a variable from an action; any state change (e.g. an
accumulated count) must be folded into derived values at draw time by the
compiler.

## 8. Logic, Control Flow, and `fun`

Behavior/logic is expressed with C-family expressions evaluated during draw
(inside `fun` and widget bodies), not in event handlers:

```
fun factorial n:i32 -> i32 {
  if n < 2 return 1
  return n * factorial(n - 1)
}
```

These function calls, being part of the draw graph, are compiled into the
bytecode regions and re-run only when their inputs change.

## 9. The Dataflow Model

The central feature. The compiler constructs a static dependency graph — for
both state *and* input fields:

```
state.count ━━━│
input.mouse --│─→  buttons/extent/text instruction (label of count)
```

Every edge is recorded in the bytecode dataflow table:

```
STATE_ID : count
  EDGE → RENDERING_INSTRUCTION_ID (text label)

INPUT_ID : mouse
  EDGE → RENDERING_INSTRUCTION_ID (highlight)
```

At runtime, when the App VM mutates state (or input changes), it asks the
dataflow table which redraw region to invalidate. It does not walk a DOM, and
does not run a dynamic reconciler.

## 10. No Events (design assert)

There are no event handlers, no listeners, and no dispatch. Interaction is
input-as-state read during draw. Any revision that reintroduces callbacks,
event queues, or bubbling violates the non-negotiable immediate-mode constraint
(SPEC-00 §5).

## 11. Components and Packaging

- A widget can be `.ath`-declared in its own file and `import`ed.
- A large UI is split into components; each component is its own widget file.
- The compiler resolves imports before the dataflow graph is built.

## 12. Type System

- Integers: `i8..i64`, `u8..u64`
- Floats: `f32`, `f64`
- Booleans: `bool`
- Strings: `string` (UTF-8)
- Colors: `color`
- Strongly and statically typed. No `any`; no dynamic dispatch needed.

Compile-time type checking catches errors before bytecode is emitted.

## 13. Intended Future (Deferred)

- `video` and `media` runtime APIs.
- Flexible layout containers (flex/grid) — initially declarative layout of
  position/size.
- Existing legacy sandbox.

These are roadmap items (SPEC-07).

## 14. Tooling expectations

The language tooling surfaces:

- **REPL / preview** in dev ("hot reload") runs via the compiler, not the
  runtime.
- Diagnostics spanning parser, typing, and the dataflow/dependency analysis.
- Code generation and packaging (SPEC-03).

## Summary

The Athru language is unified, C-family, declarative-first, and widget-based,
with compile-time dependency tracking and immediate input-as-state interaction.
The compiler turns everything—structure, style, state, and input dependencies—
into the bytecode in SPEC-03.
