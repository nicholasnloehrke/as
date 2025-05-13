from ply.lex import lex
from ply.yacc import yacc


class Parser:
    tokens = (
        "REGISTER",
        "NUMBER",
        "COMMA",
        "ADD",
        "SUB",
        "SLT",
        "LI",
        "LW",
        "SW",
        "BEQ",
        "BNE",
        "PUSH",
        "POP",
        "J",
        "JAL",
        "JR",
    )

    def __init__(self):
        self._lexer = lex(module=self)
        self._parser = yacc(module=self)

    def t_REGISTER(self, t):
        r"D[0-3]"

        return t

    def t_NUMBER(self, t):
        r"\d+"
        value = int(t.value)
        if value > 31 or value < 0:
            print(f"'{value}' out of range. Expected 0 <= value <= 31")
            self.t_error(t)

        t.value = value

        return t

    t_COMMA = r","
    t_ignore = " \t"
    t_ADD = r"add"
    t_SUB = r"sub"
    t_SLT = r"slt"
    t_LI = r"li"
    t_LW = r"lw"
    t_SW = r"sw"
    t_BEQ = r"beq"
    t_BNE = r"bne"
    t_PUSH = r"push"
    t_POP = r"pop"
    t_J = r"j"
    t_JAL = r"jal"
    t_JR = r"jr"

    def t_COMMENT(self, _):
        r"\#.*"
        pass

    def t_newline(self, t):
        r"\n+"
        t.lexer.lineno += len(t.value)

    def t_error(self, t):
        line = t.lineno
        column = self.find_column(t.lexer.lexdata, t)

        line_start = t.lexer.lexdata.rfind("\n", 0, t.lexpos) + 1
        line_end = t.lexer.lexdata.find("\n", t.lexpos)
        if line_end == -1:
            line_end = len(t.lexer.lexdata)
        error_line = t.lexer.lexdata[line_start:line_end]

        pointer = " " * (column - 1) + "^"

        raise ValueError(
            f"Illegal character '{t.value[0]}' at line {line}, column {column}:\n"
            f"{error_line}\n{pointer}"
        )

    def p_program(self, p):
        """program : instruction
        | instruction program"""
        p[0] = [p[1]] if len(p) == 2 else [p[1]] + p[2]

    def p_instruction(self, p):
        """instruction : r_type
        | i_type
        | j_type"""
        p[0] = p[1]

    def p_r_type(self, p):
        """r_type : ADD REGISTER COMMA REGISTER COMMA REGISTER
        | SUB REGISTER COMMA REGISTER COMMA REGISTER
        | SLT REGISTER COMMA REGISTER COMMA REGISTER"""
        p[0] = (p[1], p[2], p[4], p[6])

    def p_i_type(self, p):
        """i_type : LI REGISTER COMMA NUMBER
        | LW REGISTER COMMA NUMBER
        | SW REGISTER COMMA NUMBER
        | BEQ REGISTER COMMA NUMBER
        | BNE REGISTER COMMA NUMBER"""
        p[0] = (p[1], p[2], p[4])

    def p_i_type_stack(self, p):
        """i_type : PUSH REGISTER
        | POP REGISTER"""
        p[0] = (p[1], p[2])

    def p_j_type(self, p):
        """j_type : J NUMBER
        | JAL NUMBER"""
        p[0] = (p[1], p[2])

    def p_j_type_jr(self, p):
        """j_type : JR"""
        p[0] = (p[1],)

    def p_error(self, p):
        if p is None:
            token = "end of file"
        else:
            token = f"{p.type}({p.value}) on line {p.lineno}"

        print(f"Syntax error: Unexpected {token}")

    def find_column(self, input, token):
        last_cr = input.rfind("\n", 0, token.lexpos)
        if last_cr < 0:
            last_cr = -1
        return token.lexpos - last_cr

    def parse(self, code):
        return self._parser.parse(code, lexer=self._lexer)
