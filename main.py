import argparse
from parser import Parser


opcode_map = {
    "li": 0b0001,
    "lw": 0b0010,
    "sw": 0b0011,
    "add": 0b0100,
    "sub": 0b0101,
    "slt": 0b0110,
    "beq": 0b0111,
    "bne": 0b1000,
    "j": 0b1001,
    "jal": 0b1010,
    "jr": 0b1011,
    "push": 0b1100,
    "pop": 0b1101,
}


def regnum(r):
    return int(r[1])  #  'D2' => 2


def encode_instruction(instr):
    op = instr[0]
    opcode = opcode_map.get(op)
    if opcode is None:
        raise ValueError(f"Unknown opcode: {op}")

    if op == "li":
        dsel = regnum(instr[1])
        imm = instr[2] & 0b11111
        return (opcode << 7) | (dsel << 5) | imm

    elif op in ("add", "sub", "slt"):
        dsel = regnum(instr[1])
        r1 = regnum(instr[2])
        r2 = regnum(instr[3])
        operand = (r1 << 2) | r2  # 2 bits for r1, 2 bits for r2 = 4 bits
        return (opcode << 7) | (dsel << 5) | operand

    elif op in ("lw", "sw", "push", "pop"):
        dsel = regnum(instr[1])
        addr = instr[2] if len(instr) > 2 else 0
        return (opcode << 7) | (dsel << 5) | (addr & 0b11111)

    elif op in ("beq", "bne"):
        dsel = regnum(instr[1])
        addr = instr[2] & 0b11111
        return (opcode << 7) | (dsel << 5) | addr

    elif op in ("j", "jal"):
        addr = instr[1] & 0b11111
        return (opcode << 7) | (0 << 5) | addr  # no Dsel for jumps

    elif op == "jr":
        return opcode << 7

    else:
        raise ValueError(f"Unhandled instruction: {instr}")


def assemble(parser, code):
    instructions = parser.parse(code)
    resolved = []

    # Resolve labels first
    labels = {}
    flat = []
    pc = 0
    for instr in instructions:
        if isinstance(instr, tuple) and instr[0] == "label":
            labels[instr[1]] = pc
            instr = instr[2]
        if instr:
            flat.append(instr)
            pc += 1

    # Resolve label references
    for instr in flat:
        resolved_instr = []
        for part in instr:
            if isinstance(part, tuple) and part[0] == "label_ref":
                label = part[1]
                addr = labels.get(label)
                if addr is None:
                    raise ValueError(f"Unknown label: {label}")
                resolved_instr.append(addr)
            else:
                resolved_instr.append(part)
        resolved.append(tuple(resolved_instr))

    # Encode
    binary = [encode_instruction(instr) for instr in resolved]

    for i, b in enumerate(binary):
        print(f"{i:02}: {b:011b}")  # 11-bit binary with leading zeros


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument("infile", help="Input file")
    argparser.add_argument("-o", help="Output file")
    args = argparser.parse_args()

    with open(args.infile) as f:
        code = f.read()

    try:
        assemble(Parser(), code)

    except Exception as e:
        print(f"{e}")


if __name__ == "__main__":
    main()
