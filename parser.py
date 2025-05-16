from ply.lex import lex
from ply.yacc import yacc
import sys


class Parser:
    opcodes = {
        "add": "ADD",
        "sub": "SUB",
        "slt": "SLT",
        "li": "LI",
        "lw": "LW",
        "sw": "SW",
        "beq": "BEQ",
        "bne": "BNE",
        "push": "PUSH",
        "pop": "POP",
        "j": "J",
        "jal": "JAL",
        "jr": "JR",
        "nop": "NOP",
    }

    tokens = (
        "REGISTER",
        "NUMBER",
        "COMMA",
        "LABEL",
        "ID",
    ) + tuple(opcodes.values())

    def __init__(self):
        self._lexer = lex(module=self)
        self._parser = yacc(module=self)
        self._failed = False
        self._file_name = ""

    def t_REGISTER(self, t):
        r"D[0-3]"
        return t

    def t_NUMBER(self, t):
        r"[-+]?[0-9]+"
        value = int(t.value)
        if value > 31 or value < 0:
            self.t_error(t, reason=f"value of '{value}' is out of range.")
        t.value = value
        return t

    def t_LABEL(self, t):
        r"[a-zA-Z_][a-zA-Z0-9_]*:"
        t.value = t.value[:-1]
        return t

    def t_ID(self, t):
        r"[a-zA-Z_][a-zA-Z0-9_]*"
        t.type = self.opcodes.get(t.value, "ID")
        return t

    t_COMMA = r","
    t_ignore = " \t"

    def t_COMMENT(self, _):
        r"\#.*"
        pass

    def t_newline(self, t):
        r"\n+"
        t.lexer.lineno += len(t.value)

    def t_error(self, t, **kwargs):
        RED = "\033[31m"
        BOLD = "\033[1m"
        RESET = "\033[0m"

        line = t.lineno
        column = self.find_column(t.lexer.lexdata, t)
        line_start = t.lexer.lexdata.rfind("\n", 0, t.lexpos) + 1
        line_end = t.lexer.lexdata.find("\n", t.lexpos)
        if line_end == -1:
            line_end = len(t.lexer.lexdata)
        error_line = t.lexer.lexdata[line_start:line_end]
        pointer = f"{' ' * (column - 1)}{BOLD}{RED}^{'~' * (len(t.value) - 1)}{RESET}"

        reason = kwargs.get("reason", f"invalid token '{t.value}'")

        print(
            f"{BOLD}{self._file_name}:{line}:{column + 1}:{RESET} {RED}error:{RESET} {reason}\n"
            f"    {line} | {error_line}\n"
            f"    {' ' * len(str(line))} | {pointer}"
        )
        self._failed = True
        if hasattr(t.lexer, "skip"):
            t.lexer.skip(1)

    def p_program(self, p):
        """program : instruction
        | instruction program"""
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = [p[1]] + p[2]

    def p_instruction(self, p):
        """instruction : r_type
        | i_type
        | j_type
        | nop_type
        | LABEL r_type
        | LABEL i_type
        | LABEL j_type
        | LABEL nop_type"""
        pos = (p.lineno(1), p.lexpos(1))
        if len(p) == 2:
            p[0] = ("instr", p[1], pos)
        else:
            p[0] = ("label", p[1], ("instr", p[2], pos))

    def p_nop_type(self, p):
        "nop_type : NOP"
        p[0] = (p[1],)

    def p_r_type(self, p):
        """r_type : ADD REGISTER COMMA REGISTER COMMA REGISTER
        | SUB REGISTER COMMA REGISTER COMMA REGISTER
        | SLT REGISTER COMMA REGISTER COMMA REGISTER"""
        p[0] = (p[1], p[2], p[4], p[6])

    def p_i_type(self, p):
        """i_type : LI REGISTER COMMA NUMBER
        | LW REGISTER COMMA NUMBER
        | LW REGISTER COMMA ID
        | SW REGISTER COMMA NUMBER
        | SW REGISTER COMMA ID
        | BEQ REGISTER COMMA NUMBER
        | BEQ REGISTER COMMA ID
        | BNE REGISTER COMMA NUMBER
        | BNE REGISTER COMMA ID"""
        if isinstance(p[4], int):
            p[0] = (p[1], p[2], p[4])
        else:
            p[0] = (p[1], p[2], ("label_ref", p[4]))

    def p_i_type_stack(self, p):
        """i_type : PUSH REGISTER
        | POP REGISTER"""
        p[0] = (p[1], p[2])

    def p_j_type(self, p):
        """j_type : J NUMBER
        | J ID
        | JAL NUMBER
        | JAL ID"""
        if isinstance(p[2], int):
            p[0] = (p[1], p[2])  # resolved address
        else:
            p[0] = (p[1], ("label_ref", p[2]))  # mark as needing label resolution

    def p_j_type_jr(self, p):
        "j_type : JR"
        p[0] = (p[1],)

    def p_error(self, p):
        self._failed = True
        if p:
            self.t_error(p)
        else:
            print("Syntax error: Unexpected EOF")

    def find_column(self, input, token):
        last_cr = input.rfind("\n", 0, token.lexpos)
        if last_cr < 0:
            last_cr = -1
        return token.lexpos - last_cr

    def parse(self, code, file_name=""):
        try:
            self._file_name = file_name
            self._source_code = code
            self._failed = False

            raw_instructions = self._parser.parse(code, lexer=self._lexer)
            if self._failed:
                raise Exception()

            # Flatten labels and collect instructions
            instructions = []
            labels = {}
            pc = 0

            for instr in raw_instructions:
                if instr[0] == "label":
                    labels[instr[1]] = pc
                    instr = instr[2]
                if instr and instr[0] == "instr":
                    instructions.append(instr)
                    pc += 1

            # Resolve label references
            resolved = []
            for op, pos in [(i[1], i[2]) for i in instructions]:
                resolved_instr = []
                for part in op:
                    if isinstance(part, tuple) and part[0] == "label_ref":
                        label = part[1]
                        addr = labels.get(label)
                        if addr is None:
                            fake_token = type(
                                "Token",
                                (),
                                {
                                    "value": label,
                                    "lineno": pos[0],
                                    "lexpos": pos[1],
                                    "lexer": type(
                                        "Lexer", (), {"lexdata": self._source_code}
                                    )(),
                                },
                            )()
                            self.t_error(fake_token, reason=f"Unknown label: '{label}'")
                            raise Exception()
                        resolved_instr.append(addr)
                    else:
                        resolved_instr.append(part)
                resolved.append(tuple(resolved_instr))

            return resolved

        except Exception as e:
            print(e)
            sys.exit(1)
