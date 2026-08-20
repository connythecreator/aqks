# Athru Bytecode Specification

**Document:** SPEC-03
**Version:** 0.1.0
**Status:** Draft

## 1. Introduction

Athru bytecode is a custom binary format produced by the compiler (SPEC-02).
It is a **rendering instruction set**, not a general-purpose machine-code ISA
and not a script. It is intentionally "basic": its instructions correspond to
widgets (analogous to HTML tags—headings, video, boxes, buttons) rather than to
low-level CPU operations.

Bytecode is a raw file. The runtime loads it directly into memory and the render
engine walks it to emit immediate-mode draw calls. There is no interpreter loop,
no JIT, and no DOM.

A companion format is the distributable **package** (`.athp`), which wraps the
compiled bytecode with assets and a manifest. (Authored source is `.ath`.)
bytecode with assets and a manifest.

## 2. Design Principles

1. **Raw and load-ready.** Bytecode is memory-mapped or read as a blob; the
   renderer processes it directly.
2. **Rendering-focused.** Instructions describe what to draw and how to react,
   not CPU computation.
3. **Graph-aware.** The dataflow graph (which state changes which rendering) is
   embedded as a first-class section.
4. **Region-aware.** Rendering instructions are grouped into redraw regions so
   the engine can re-render subsets precisely.
5. **Widget-analogous.** The instruction set reflects the language's widgets.
6. **Portable and endian-neutral.** Bytecode has an explicit endianness and
   version header.

## 3. File Layout (Bytecode)

A single bytecode file has this top-level structure:

```
┌───────────────────────────────────────────┐
│ MAGIC + VERSION + FLAGS                   │   header
│ SECTION DIRECTORY (offset/size per table) │
├───────────────────────────────────────────┤
│ SCENE SECTION         (rendering program) │
│ CONSTANT TABLE        (strings, numbers)  │
│ ASSET TABLE           (font/image/video)   │
│ DATAFLOW TABLE        (state/input → instr)│
│ REGION TABLE           (region → instrs)   │
│ INPUT TABLE           (input field layout) │
│ PACKAGE TABLE         (data/manifest)      │
└───────────────────────────────────────────┘
```

Sections are located by the section directory; unknown sections are ignored for
forward compatibility. All multi-byte values honor the declared endianness, by
default little-endian.

### 3.1 Header (normative)

| Field             | Size  | Meaning                                   |
|-------------------|-------|--------------------------------------------|
| Magic             | 4     | `0x41 0x54 0x48 0x52` ("ATHR")            |
| Version           | 2   | 0x0001                                    |
| Flags             | 2   | bit0 = has assets, bit1 = has input table, ... |
| SectionCount      | 1   | number of sections to follow                |
| Endianness        | 1   | 0 = LE (default), 1 = BE                  |
| Reserved          | 4   | 0                                          |

Followed by `SectionCount` directory entries, each 12 bytes:
`type (2), unknown/zero (2), offset(4), size(4)`.

## 4. Rendering Instruction Set

Instructions live in the SCENE section. Each instruction is a contiguous record.

### 4.1 Instruction framing

```
+--------+--------+--------------+----------------+
| opcode | width  | operand...   | (region tag)    |
| u8     | u8   | width bytes  | optional        |
```

Common helper encodings:

- **RGBA color**: 4 bytes.
- **i32/f32**: 4 bytes.
- **String index**: index into the constant table.

### 4.2 Opcodes (baseline set)

These correspond to the widgets in SPEC-01 §4.2. They are "basic", analogous to
HTML tags; the mix is extensible with feature flags.

| Byte | Instruction | Meaning / operands                        |
|------|-------------|-------------------------------------------|
| 0x01 | `INIT_VIEW`         | viewport size (w,h), background            |
| 0x02 | `DRAW_TEXT`          | string(id), x, y, font(id), size, color     |
| 0x03 | `DRAW_IMAGE`         | image(id), x, y, w, h, alpha               |
| 0x04 | `DRAW_VIDEO`         | video(id), box(videoid, x, y, w, h)        |
| 0x05 | `DRAW_BOX`           | x, y, w, h, fill(color), radius, border    |
| 0x06 | `BEGIN_CLIP`         | x, y, w, h (clip region)                    |
| 0x07 | `END_CLIP`           | (no payload)                               |
| 0x08 | `PUSH_TRANSFORM`     | translate/scale (x, y, sx, sy, rot)         |
| 0x09 | `POP_TRANSFORM`      | (no payload)                               |
| 0x0A | `SET_FILL`           | color (sets current fill)                   |
| 0x0B | `PATH`               | begin polygon path, points count            |
| 0x0C | `LINE_TO` / `MOVE_TO`| path extension                              |
| 0x0D | `FILL_PATH` / `STROKE_PATH` | draw the current path           |
| 0x0E | `REGION_MARK`       | start of a region (marks region id)        |
| 0x0F | `INT_REGION` / ext.  | end of current region                      |

Other instruction codes are reserved and must be ignored by older decoders.

### 4.3 Instruction payloads

`DRAW_TEXT` (0x02):

```
u8  opcode   (0x02)
u8  flags    (bold/italic)
u16 strlen
...utf8 string bytes (or string table id)
u32 fontId   (data table)
f32 size
4 x color   (RGBA)
f32 x, f32 y
```

`DRAW_BOX`/`DRAW_IMAGE` wrap selected fills; the region tag associates the
instruction with a redraw region.

## 5. Dataflow Table (`DEPGRAPH`)

This is how the runtime knows what to redraw without a DOM.

A **state** is identified by `(STATE_ID)`. The table maps a state to the set of
dependent instructions:

```
STATE 3 → count
    DEP 12  (DRAW_TEXT whose content derives from count)
    DEP 88  (highlight deriving from count)
```

An **input** field is identified by `(INPUT_ID)` and listed in its own way in
the dataflow table too, so a moving pointer/to-a-changed key invalidates exactly
the instructions that read it:

```
INPUT 1 → mouse
    DEP 88  (highlight derived from input.mouse)
```

Formal record (per state or input):

```
u8   kind            (0=state, 1=input field)
u32  depId          (STATE_ID or INPUT_ID)
u32  dependentCount
u32  dependent[ ]
u32  regionId       (region containing those instructions)
```

## 6. Region Table

Regions group instructions for independent re-render.

```
u32 regionId
u32 instrCount
u32 [instr indices]
u32 x, y, w, h  (region bounds)
```

The renderer can:

- `athruDrawRegion(regionId, state, input)` — processes just that section.
- `athruInvalidate(regionId)` — marks for re-render.

Region bounds are also used to resolve `input.*` draw-time queries (e.g.
"is the pointer inside box X?") during render; hit-testing is a by-product of
drawing, not an input pre-pass.

## 7. Input Table

Input is not a set of handlers; it is read-only per-frame state made available
to the draw instructions. The Input Table describes that state's layout so the
engine and host agree on the bytes supplied at draw time.

```
u32     inputFieldCount
per field:
u32     fieldId           (matches INPUT_ID in the dataflow table)
u32     kind              (0=mouse,1=keyboard,2=focus,3=touch,...)
u32     offset            (byte offset into the input state block)
u32     count             (i.e. component count / key-count)
```

At runtime the host writes the sampled input into this fixed layout each frame;
widgets read fields via `input.<field>` during draw, and the dataflow table
invalidates only the regions that depend on them.

## 8. Constant / Data Tables

- **CONST**: strings, floats, colors used by instructions.
- **DATA**: font, image, and video asset IDs; index into the package asset
  store.
- **FONT** metadata: name, path, px height.

## 9. Package Format (`Athru`)

The distribution artifact is a **single file** with a manifest. Two encodings:

- **unpacked**: directory with top-level `.bytecode`, `assets/`, `manifest.json`.
- **packed**: single archive with the same logical sections.

### 9.1 Library manifest (`.json`)

```
{
  "id": "com.example.myapp",
  "version": "1.0.0",
  "entry": "main.bytecode",
  "assets": [ "fonts/inter.ttf", "image/logo.png", "video/intro.mp4" ],
  "permissions": ["..."]
}
```

The engine accepts a `bytecode` blob only; the host/App VM loads the package and
passes the bytecode to the engine (SPEC-04/05).

## 10. Validation

A loader must validate:

- magic and version,
- section bounds,
- dataflow edges point to in-range instruction indices,
- no cycle that cannot be flagged; cycles are allowed but flagged,
- all referenced constants/assets exist.

Malformed bytecode is rejected; never partially executed.

## 11. Endianness and Portability

Bytecode is defined for little-endian by default and is portable across the
three desktop platforms. Bytecode contains no host pointers; offsets/indexes
only.

## Summary

SPEC-03 defines the raw rendering instruction set, the embedded dataflow and
region tables, the input table, and the package format. It is the contract that
the compiler emits (SPEC-02) and the engine and runtime consume (SPEC-04/05).
