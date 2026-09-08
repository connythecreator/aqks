# ATHRU

## PURPOSE

Athru is a bytecode format that can be used to represent a user interface.
Intended to replace traditional HTML, CSS and JS; since the effort required to
build a compliant browser for these standards is ridiculous.

## DESIGN PRINCIPALS

- structure, style, and logic live in the same file
- widgets like HTML tags; heading, text, video, image, button
- immediate-mode design, but you can draw the bytecode however you please
- latest input (mouse, keys, focus, etc) available as variables that are read 
  during drawing
- heavy inspiration from SPIR-V instructions:
  https://registry.khronos.org/SPIR-V/specs/unified1/SPIRV.html#Instructions

## FORMAT SHCEMA

FORMAT:

- NUMBER 01
    next byte width in bytes, 1 (8 bit) to 8 (64 bit)

- STRING 02
    next 4 bytes, length in BYTES! (not characters, utf-8)

- VECTOR, code 03
    next byte is FORMAT of each element, (02 for VECTOR of STRINGS)
    next 4 bytes, size as in number of elements
    each element is a 4 byte index into MEMORY section

- BLOB, code 04
    next 6 bytes, BLOB size in bytes

## FILE LAYOUT (.ath)

- HEADER,   magic number, version
- MEMORY,   strings, arrays of data, formats
- DRAW,     rendering program
- ASSETS,   references to font, image, video

### HEADER

- MAGIC 
    4 bytes, 41 54 48 52, "ATHR"

- VERSION
    2 bytes integer (we are on version 1)

### MEMORY

the memory section

### DRAW

this section contains code bytes which are executed in order from the top
every frame
the following instructions are available:

#### DRAWING INSTRUCTIONS

- BEGIN_FRAME
    label for accessibility
    list of offsets of child frames

- END_FRAME
    takes no arguments

- PUSH_STYLE
    alignment
    colours

- POP_STYLE
    takes no arguments

- PUSH_TRANSFORM
    scale
    rotate

- POP_TRANSFORM
    takes no arguments

- DRAW_TEXT
    offset of text content in MEMORY
    offset of font in ASSETS

- DRAW_IMAGE
    description
    offset of image in ASSETS

- DRAW_VIDEO
    label
    timestamp
    offset of video data in ASSETS

#### MEMORY INSTRUCTIONS

- FORMAT

- VARIABLE

- LOAD

- STORE

#### OPERATION INSTRUCTIONS

- NEG

- ADD

- SUB

- MUL

- DIV

- BITWISE

- SIZE

#### CONTROL-FLOW INSTRUCTIONS

- BEGIN_FUNC

- FUNC_PARAM

- END_FUNC

- CALL_FUNC

#### COMMUNICATION INSTRUCTIONS

lots of code is deticated to async networking, we can eliminate much
hassle by specifying fixed format then request/recv this from a source

- REQUEST

- RECEIVE

#### ASSETS

- asset header with position and length, same FORMAT as memory section
- simple binary storage
- for large assets just store the uri, they can be cached/differed/streamed

## ACCESSIBILITY

a11y tree created from widget names and text labels, we don't necessarily need a
tree, since we can store an index to the current widget and walk around the
bytecode as needed

## VIDEO

to be determined

## PROJECT TIMELINE

### Bytecode format

- decide on a basic set of instructions
- make a few test pages

### Renderer

- open a window
- draw loop
- walk instructions
- draw some things from instructions

### Extra Features

- load a font (or other stuff) from ASSETS
- make a server that serves a page
- make a dynamic server than server a chat window

### Finish

- flexible layouts
- make a page with a video
- screen reader

