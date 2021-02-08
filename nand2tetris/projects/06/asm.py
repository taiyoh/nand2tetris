import enum
import sys
import re


class CommandType(enum.Enum):
    A = 'A_COMMAND'
    C = 'C_COMMAND'
    L = 'L_COMMAND'


class Parser:
    lines: list[str]
    lineCount = 0
    currentSymbol: str
    currentCommand: CommandType
    currentDest: str
    currentComp: str
    currentJump: str

    comment = re.compile(r'//.+')
    addrInst = re.compile(r'^@.+$')
    compInst = re.compile(
        r'^([MDA]{1,3})?=?([MDA+-10!&|]+);?(J(GT|GE|EQ|NE|LT|LE|MP))?$')
    labelInst = re.compile(r'^\(.+\)$')

    def __init__(self, name: str) -> None:
        with open(name) as f:
            self.lines = f.readlines()

    def __setComp(self, s1, s2, s3):
        self.currentDest = s1 or None
        self.currentComp = s2 or None
        self.currentJump = s3 or None

    def hasMoreCommands(self) -> bool:
        return self.currentCommand is not None

    def advance(self) -> None:
        while len(self.lines) > self.lineCount:
            self.currentSymbol = re.sub(
                self.comment, '', self.lines[self.lineCount].strip().replace(' ', ''))
            self.lineCount += 1
            if self.addrInst.match(self.currentSymbol) is not None:
                self.currentCommand = CommandType.A
                self.__setComp(None, None, None)
                return
            if self.labelInst.match(self.currentSymbol) is not None:
                self.currentCommand = CommandType.L
                self.__setComp(None, None, None)
                return
            compInst = self.compInst.findall(self.currentSymbol)
            if len(compInst) > 0:
                smbl: tuple = compInst[0]
                self.currentCommand = CommandType.C
                self.__setComp(smbl[0], smbl[1], smbl[2])
                return
        self.currentCommand = None

    def commandType(self) -> CommandType:
        return self.currentCommand

    def symbol(self) -> str:
        if self.currentCommand is CommandType.A:
            return self.currentSymbol.replace('@', '')
        else:
            return self.currentSymbol.replace('(', '').replace(')', '')

    def dest(self) -> str:
        return self.currentDest

    def comp(self) -> str:
        return self.currentComp

    def jump(self) -> str:
        return self.currentJump


reservedSymbol: dict[str:int] = {
    'SP': 0,
    'LCL': 1,
    'ARG': 2,
    'THIS': 3,
    'THAT': 4,
    'R0': 0,
    'R1': 1,
    'R2': 2,
    'R3': 3,
    'R4': 4,
    'R5': 5,
    'R6': 6,
    'R7': 7,
    'R8': 8,
    'R9': 9,
    'R10': 10,
    'R11': 11,
    'R12': 12,
    'R13': 13,
    'R14': 14,
    'R15': 15,
    'SCREEN': 16384,
    'KBD': 24576,
}


class Code:
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

    def dest(nemonic: str) -> bytearray:
        return __class__.destMap[nemonic]

    def comp(nemonic: str) -> bytearray:
        return __class__.compMap[nemonic]

    def jump(nemonic: str) -> bytearray:
        return __class__.jumpMap[nemonic]


class SymbolTable:
    table: dict[str:int]

    def __init__(self) -> None:
        self.table = dict()

    def addEntry(self, symbol: str, address: int) -> None:
        # print(f'addEntry {symbol}:{address}')
        self.table[symbol] = address

    def contains(self, symbol: str) -> bool:
        return self.table.get(symbol) is not None

    def getAddress(self, symbol: str) -> int:
        return self.table.get(symbol)


def main() -> None:
    path = sys.argv[1]
    dest = sys.argv[2]
    print(f"asm!!! {path}")
    tbl = SymbolTable()

    # 1st read
    parser = Parser(path)
    addr = 0
    labels: list[str] = list()
    parser.advance()
    while parser.hasMoreCommands():
        if parser.commandType() is CommandType.L:
            labels.append(parser.symbol())
        else:
            for l in labels:
                tbl.addEntry(l, addr)
            labels.clear()
            addr += 1
        parser.advance()

    print('=======')
    # 2nd read
    memAddr = 16
    lines = list()
    parser = Parser(path)
    parser.advance()
    while parser.hasMoreCommands():
        ct = parser.commandType()
        if ct is CommandType.A:
            s = parser.symbol()
            try:
                a = int(s)
            except:
                if s in reservedSymbol:
                    a = reservedSymbol[s]
                elif tbl.contains(s):
                    a = tbl.getAddress(s)
                else:
                    a = memAddr
                    tbl.addEntry(s, memAddr)
                    memAddr += 1
            lines.append(f"{format(a, '016b')}\n")
        if ct is CommandType.C:
            c = Code.comp(parser.comp())
            d = Code.dest(parser.dest())
            j = Code.jump(parser.jump())
            bl = b'\x01\x01\x01'+c+d+j
            lines.append(''.join(format(b, 'b') for b in bl)+"\n")
        parser.advance()

    with open(dest, mode='w') as f:
        f.writelines(lines)


if __name__ == '__main__':
    main()
