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
  and immediate mode ui projects like Dear ImGui and egui:
  https://www.dearimgui.com/
  https://www.egui.rs/

## FORMAT SCHEMA

data types:

- FORMAT 01
    one byte, number of member types
    preceeding bytes are type of member, like members of struct

- BYTE 02
    one byte, takes 1 byte of space

- INTEGER 03
    one byte width in bytes, 1 (8 bit) to 6 (64 bit)
    all INTEGERS are signed

- FLOAT 04
    one byte width in bytes, 4 (float) OR 6 (double)

- STRING 05
    all strings are utf-8 encoded, no strings are null terminated
    instances of a string begin with string length as 6 bytes (64 bit)

- VECTOR 06

- BLOB 07
    6 bytes (64 bit), BLOB size in bytes

- REFERENCE 08
    6 bytes (64 bit), pointer value

example types:

message with a timestamp (64 bit int), one byte user id and string message
content:

01 03 03 06 02 05

a vector of messages could then be represented as

06 

to create an instance of a message, the program will reference the offset into
the MEMORY section where the message type is stored

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

- META
    FORMAT string of author name and date

### MEMORY

user FORMAT types and known size data put in this section
e.g label strings, known types
indexes into memory are 4 bytes wide

### DRAW

this section contains code bytes which are executed in order from the top

instructions begin with 2 byte instruction code then list of arguments
some instructions have another byte after instruction code, for the number of
arguments in the list

the following instructions are available:

#### DRAWING INSTRUCTIONS

more instructions to be added!

- BEGIN_FRAME 00
    label

- END_FRAME 01
    takes no arguments

- PUSH_TRANSFORM 02
    translate:  x, y
    scale:      width, height
    rotate:     degrees

- POP_TRANSFORM 03
    takes no arguments

- DRAW_TEXT 04
    index of text content in MEMORY
    index of font in ASSETS

- DRAW_BUTTON 05
    text
    pos
    func

- DRAW_IMAGE 06
    text description
    index of image in ASSETS

#### MEMORY INSTRUCTIONS

- FORMAT
    - creates a type, 
    like a struct, that can be identified
    by its offset in memory

    - subsequent bytes are FORMAT definition like in MEMORY section

    - uninitialised memory will have a poison value and reading or writing will
    cause the program to end

- VARIABLE
    - creates an instance of a type,
    like an object

- LOAD

- STORE

#### OPERATION INSTRUCTIONS

- NEG
    index into MEMORY of value to negate
    works on BYTE,INT,FLOAT, otherwise is NOP

- ADD
    first + second
    index of first
    index of second
    index of destination
    works on BYTE,INT,FLOAT, otherwise is NOP

- SUB
    first - second
    index of first operand
    index of second operand
    index of destination
    works on BYTE,INT,FLOAT, otherwise is NOP

- MUL
    index of first operand
    index of second operand
    index of destination
    works on BYTE,INT,FLOAT, otherwise is NOP

- DIV
    index of first operand
    index of second operand
    index of destination
    works on BYTE,INT,FLOAT, otherwise is NOP

- SIZE
    index of data object to get the size of
    works on BYTE,INT,FLOAT, otherwise is NOP

#### CONTROL-FLOW INSTRUCTIONS

- NOP
    does exactly what you think it does... nothing

- BEGIN_FUNC

- FUNC_PARAM

- END_FUNC

- CALL_FUNC

#### COMMUNICATION INSTRUCTIONS

lots of code is deticated to async networking, we can eliminate much
hassle by specifying fixed format then request/recv this from a source

- REQUEST 40
    - index of type to request
    - address of function to call if PENDING state
    - address of function to call if READY state
    - error mask of errors
    - address of function to call on masked error

- RECEIVE 41
    - index of type to request
    - address of function to call if PENDING state
    - address of function to call if READY state
    - error mask of errors
    - address of function to call on masked error

## PROJECT TIMELINE

### Bytecode format

- decide on a basic set of instructions
- make a few test pages

### Renderer

- open a window
- draw loop
- walk instructions
- draw some things from instructions
