
example ATHRU file for a static hello world page
file starts with header information, the file magic 

41 54 48 52     "ATHR"

and version number

00 01           version one

the second section, memory section, is like a flat buffer
it has a count of objects and offsets to the objects

01 04 0d        one object, starting at 4, length 13

48 65 6c 6c 6f 2c 20 57 6f 72 6c 64 21, "Hello, World!"

next is the draw section which has all of the drawing and logic
instructions

00              BEGIN_FRAME instruction
	01          use first element in MEMORY section for label

06              DRAW_TEXT
	01          use first element in MEMORY section for content
	00          use default font

01              END_FRAME

final application bytecode (26 bytes):

41 54 48 52
00 01
01 04 0d
48 65 6c 6c 6f 2c 20 57 6f 72 6c 64 21
00
01
06
00
01


---------------------------------------------------------------------------------


example ATHRU file for a button and counter static page

41 54 48 52     "ATHR"
00 01           version one

memory section

03              three FORMATs
    04 09       one REFERENCE at 4
                one STRING at 6 with length 9
                another STRING at 6 with length 9

49 6e 63 72 65 6d 65 6e 74 "Increment"
43 6c 69 63 6b 20 6d 65 "Click me"

the drawing section for this application looks like:

00              BEGIN_FRAME instruction
	01          use "Increment" for label

06              DRAW_TEXT
	01          use "Increment:" for content
	00          use default font

04              DRAW_BUTTON
    01
    00

01              END_FRAME


---------------------------------------------------------------------------------


bigger example ATHRU file for a messaging app
