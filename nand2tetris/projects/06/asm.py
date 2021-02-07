import sys
import re
import binascii


class CommandType:
    typ = None

    def __init__(self, t: str) -> None:
        self.typ = t


A_COMMAND = CommandType('A')
C_COMMAND = CommandType('C')
L_COMMAND = CommandType('L')

comment = re.compile(r'//.+')
addr = re.compile(r'^@[0-9]+$')
comp = re.compile(r'^([MDA])?=?([MDA+-10!]+);?(J(GT|GE|EQ|NE|LT|LE|MP))?$')


class Parser:
    lines: list[str]
    lineCount = 0
    currentSymbol: str
    currentCommand: CommandType
    currentDest: str
    currentComp: str
    currentJump: str

    def __init__(self, name: str) -> None:
        fd = open(name)
        self.lines = fd.readlines()

    def __setComp(self, s1, s2, s3):
        self.currentDest = s1 or None
        self.currentComp = s2 or None
        self.currentJump = s3 or None

    def hasMoreCommands(self) -> bool:
        return self.currentCommand is not None

    def advance(self) -> None:
        while len(self.lines) > self.lineCount:
            self.currentSymbol = re.sub(
                comment, '', self.lines[self.lineCount].strip().replace(' ', ''))
            self.lineCount += 1
            if addr.match(self.currentSymbol) is not None:
                self.currentCommand = A_COMMAND
                self.__setComp(None, None, None)
                return
            smbl = comp.findall(self.currentSymbol)
            if len(smbl) > 0:
                smbl: tuple = smbl[0]
                self.currentCommand = C_COMMAND
                self.__setComp(smbl[0], smbl[1], smbl[2])
                return
        self.currentCommand = None

    def commandType(self) -> CommandType:
        return self.currentCommand

    def symbol(self) -> str:
        return self.currentSymbol

    def dest(self) -> str:
        return self.currentDest

    def comp(self) -> str:
        return self.currentComp

    def jump(self) -> str:
        return self.currentJump


destMap: dict[str:bytearray] = {
    None: b'\x00\x00\x00',
    'M': b'\x00\x00\x01',
    'D': b'\x00\x01\x00',
    'MD': b'\x00\x01\x01',
    'A': b'\x01\x00\x00',
    'AM': b'\x01\x00\x01',
    'AD': b'\x01\x01\x00',
    'AMD': b'\x01\x01\x01',
}

compMap: dict[str:bytearray] = {
    '0': b'\x00\x01\x00\x01\x00\x01\x00',
    '1': b'\x00\x01\x01\x01\x01\x01\x01',
    '-1': b'\x00\x01\x01\x01\x00\x01\x00',
    'D': b'\x00\x00\x00\x01\x01\x00\x00',
    'A': b'\x00\x01\x01\x00\x00\x00\x00',
    'M': b'\x01\x01\x01\x00\x00\x00\x00',
    '!D': b'\x00\x00\x00\x01\x01\x00\x01',
    '!A': b'\x00\x01\x01\x00\x00\x00\x01',
    '!M': b'\x01\x01\x01\x00\x00\x00\x01',
    '-D': b'\x00\x00\x00\x01\x01\x01\x01',
    '-A': b'\x00\x01\x01\x00\x00\x01\x01',
    '-M': b'\x01\x01\x01\x00\x00\x01\x01',
    'D+1': b'\x00\x00\x01\x01\x01\x01\x01',
    'A+1': b'\x00\x01\x01\x00\x01\x01\x01',
    'M+1': b'\x01\x01\x01\x00\x01\x01\x01',
    'D-1': b'\x00\x00\x00\x01\x01\x01\x00',
    'A-1': b'\x00\x01\x01\x00\x00\x01\x00',
    'M-1': b'\x01\x01\x01\x00\x00\x01\x00',
    'D+A': b'\x00\x00\x00\x00\x00\x01\x00',
    'D+M': b'\x01\x00\x00\x00\x00\x01\x00',
    'D-A': b'\x00\x00\x01\x00\x00\x01\x01',
    'D-M': b'\x01\x00\x01\x00\x00\x01\x01',
    'A-D': b'\x00\x00\x00\x00\x01\x01\x01',
    'M-D': b'\x01\x00\x00\x00\x01\x01\x01',
    'D&A': b'\x00\x00\x00\x00\x00\x00\x00',
    'D&M': b'\x01\x00\x00\x00\x00\x00\x00',
    'D|A': b'\x00\x00\x01\x00\x01\x00\x01',
    'D|M': b'\x01\x00\x01\x00\x01\x00\x01',
}

jumpMap: dict[str:bytearray] = {
    None: b'\x00\x00\x00',
    'JGT': b'\x00\x00\x01',
    'JEQ': b'\x00\x01\x00',
    'JGE': b'\x00\x01\x01',
    'JLT': b'\x01\x00\x00',
    'JNE': b'\x01\x00\x01',
    'JLE': b'\x01\x01\x00',
    'JMP': b'\x01\x01\x01',
}


class Code:
    def dest(nemonic: str) -> bytearray:
        return destMap[nemonic]

    def comp(nemonic: str) -> bytearray:
        return compMap[nemonic]

    def jump(nemonic: str) -> bytearray:
        return jumpMap[nemonic]


class SymbolTable:
    table: dict
    cursor: dict

    def __init__(self) -> None:
        self.table = dict()
        self.cursor = dict()

    def addEntry(self, symbol: str, address: int) -> None:
        l = self.table.get(symbol)
        if l is None:
            l = list()
        l.append(address)
        self.table[symbol] = l
        self.cursor[symbol] = 0
        pass

    def contains(self, symbol: str) -> bool:
        l = self.table.get(symbol)
        return l is not None or len(l) > self.cursor[symbol]

    def getAddress(self, symbol: str) -> int:
        l: list[int] = self.table.get(symbol)
        idx = self.cursor[symbol]
        self.cursor[symbol] += 1
        return l[idx]


def main() -> None:
    path = sys.argv[1]
    dest = sys.argv[2]
    print(f"asm!!! {path}")
    tbl = SymbolTable()

    # 1st read
    parser = Parser(path)
    addr = 0
    parser.advance()
    while parser.hasMoreCommands():
        tbl.addEntry(parser.symbol(), addr)
        addr += 1
        parser.advance()

    # 2nd read
    lines = list()
    parser = Parser(path)
    parser.advance()
    while parser.hasMoreCommands():
        ct = parser.commandType()
        if ct is A_COMMAND:
            a = int(parser.symbol().replace('@', ''))
            lines.append(''.join(format(byte, '04b')
                                 for byte in a.to_bytes(4, byteorder='big'))+"\n")
        if ct is C_COMMAND:
            d = Code.dest(parser.dest())
            c = Code.comp(parser.comp())
            j = Code.jump(parser.jump())
            lines.append(''.join(format(byte, 'b')
                                 for byte in (b'\x01\x01\x01'+c+d+j))+"\n")
        parser.advance()

    f = open(dest, mode='w')
    f.writelines(lines)


if __name__ == '__main__':
    main()
