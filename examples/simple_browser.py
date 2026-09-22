import sys
from pyegui import *

class Format():
    """ parse a FORMAT type string """

    def __init__(self):
        self.fmt = ''
        self.elements = []

    def parse(self, fmt):
        self.count = fmt[0]

    def len(self):
        return 16

    def element(self, addr):
        return 'Hello, World!'

class Renderer():
    """ interpret DRAW instructions """

    def __init__(self):
        self.path = ''
        self.bytes = []
        self.version = 0
        self.index = 0
        self.memory = Format()
        self.entry_point = 0
        self.stack = []
        self.pencil = [0, 0]

    def parse(self, path):
        self.path = path

        with open(path, 'rb') as file:
            self.bytes = bytearray(file.read())

        # check header
        if self.bytes[:4] != bytearray('ATHR', 'utf-8'):
            print('MAGIC mismatch, expected "ATHR" but got: ', self.bytes[:4])

        self.version = self.bytes[5] + (0xFF * self.bytes[4])
        print('version: ', self.version)

        # read memory section
        self.memory.parse(self.bytes[6:])

        # point index to code section, MEMORY size + HEADER size
        self.entry_point = self.memory.len() + 6
        self.index = self.entry_point

    def draw_text(self, text):
        label(text)

    def draw_button(self, text, pos, func):
        print('button')

    def get_input(self):
        print("fuck you")

    def exec(self):
        while self.index < len(self.bytes) - 1:
            inst = self.bytes[self.index]
            self.interp(inst)

        # jump to top after program
        self.index = self.entry_point
        self.pencil = [0, 0]

    def interp(self, inst):
        match (inst):
            case 0x00:
                addr = self.bytes[self.index + 1]
                label = self.memory.element(addr)
                print('BEGIN_FRAME, ', label)
                self.index += 2

            case 0x01:
                print('END_FRAME')
                self.index += 1

            case 0x02:
                x = self.bytes[self.index + 1]
                y = self.bytes[self.index + 2]
                w = self.bytes[self.index + 3]
                h = self.bytes[self.index + 4]
                a = self.bytes[self.index + 5]
                print('PUSH_TRANSFORM, X:',x ,' Y:',y ,' W:',w ,' H:',h ,' A:',a)
                self.index += 6

            case 0x03:
                print('POP_TRANSFORM')
                self.index += 1

            case 0x04:
                addr = self.bytes[self.index + 1]
                label = self.memory.element(addr)
                print('DRAW_BUTTON, ', label)
                self.index += 1

            case 0x05:
                print('DRAW_IMAGE')
                self.index += 1

            case 0x06:
                addr = self.bytes[self.index + 1]
                label = self.memory.element(addr)
                self.draw_text(label)
                print('DRAW_TEXT, ', label, ', ', 'Default')
                self.index += 3

            # memory instructions

            case 0x10:
                print('FORMAT, ', label)
                self.index += 1

            case 0x11:
                print('VARIABLE, ', label)
                self.index += 1

            case 0x12:
                print('LOAD, ', label)
                self.index += 1

            case 0x13:
                print('STORE, ', label)
                self.index += 1

            # operation instructions

            case 0x20:
                print('NEG, ', label)
                self.index += 1

            case 0x21:
                print('ADD, ', label)
                self.index += 1

            case 0x22:
                print('SUB, ', label)
                self.index += 1

            case 0x23:
                print('MUL, ', label)
                self.index += 1

            case 0x24:
                print('DIV, ', label)
                self.index += 1

            case 0x25:
                print('SIZE, ', label)
                self.index += 1

            # control-flow instructions

            case 0x30:
                print('NOP')
                self.index += 1

            case 0x31:
                print('BEGIN_FUNC')
                self.index += 1

            case 0x32:
                print('FUNC_PARAM')
                self.index += 1

            case 0x33:
                print('END_FUNC')
                self.index = self.stack.pop()

            case 0x34:
                self.stack.append(self.index + 1)
                print('CALL_FUNC')
                self.index += 1

            # communication instructions

            case 0x40:
                print('REQUEST ')
                self.index += 1

            case 0x41:
                print('RECEIVE ')
                self.index += 1

            case _:
                print('UNRECOGNISED INSTRUCTION: ', inst)
                quit()

    def loop(self, ctx):
        heading('Athru browser')
        self.exec()

def main():
    if len(sys.argv) <= 1:
        print('please provide path to bytecode file')

    renderer = Renderer()
    renderer.parse(sys.argv[1])

    run_native("Example app", renderer.loop)

if __name__ == '__main__':
    main()
