## ON MEMORY INDEXES

if we're going with tagged union / enum as index, we should attempt to pack
more information in than just POISON state or valid address

registers vs indexes, if you want to access a string in the MEMORY section
should you LOAD it into a register or use an index directly.

having a deticated pointer type would allow a simpler method to traverse
FORMAT structures, but required ref/deref/next instructions, can we get away
with just accessing things directly and not programmatically exploring things

## ON ACCESSIBILITY

its very messy, everyone has their own library, every OS has their own library
and there aren't really any standards for desktop applications

we don't want to roll our own accessibility since there is hardware involved
and we're clueless

we should probably just ensure the relevant information is with the right
widgets in the bytecode and let the browser handle accessibility

