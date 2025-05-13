import pytest
from parser import Parser

parser = Parser()


@pytest.mark.parametrize(
    "code,expected",
    [
        ("add    D0, D1, D2", [("add", "D0", "D1", "D2")]),
        ("sub D1, D2, D3", [("sub", "D1", "D2", "D3")]),
        ("slt D3, D2, D1", [("slt", "D3", "D2", "D1")]),
        ("li D0, 5", [("li", "D0", 5)]),
        ("li D0, 3", [("li", "D0", 3)]),
        ("lw D1,0", [("lw", "D1", 0)]),
        ("lw D1,0#comment", [("lw", "D1", 0)]),
        ("sw D2, 0", [("sw", "D2", 0)]),
        ("beq D0,20", [("beq", "D0", 20)]),
        ("bne D3, 30", [("bne", "D3", 30)]),
        ("push D2", [("push", "D2")]),
        ("pop D0", [("pop", "D0")]),
        ("j    15", [("j", 15)]),
        ("jal 31", [("jal", 31)]),
        ("jal 31 # comment :)", [("jal", 31)]),
        ("jr", [("jr",)]),
        (
            """li D0, 3
add D0, D1, D2
j 5""",
            [("li", "D0", 3), ("add", "D0", "D1", "D2"), ("j", 5)],
        ),
    ],
)
def test_valid_programs(code, expected):
    result = parser.parse(code)
    assert result == expected


@pytest.mark.parametrize(
    "code",
    [
        "",  # Empty input
        "add D0, D1, 5",  # Invalid operand type
        "li D0",  # Missing number
        "lw D4, 0",  # Invalid register
        "move D0, D1",  # Unknown instruction
        "push",  # Missing register
        "pop D5",  # Invalid register
        "j",  # Missing target
        "jr D0",  # JR takes no operands
        "li D0, xyz",  # Invalid number
        "add D0 D1, D2",  # Missing comma
        "li, D0, 5",  # Extra comma
        "add D0,, D1, D2",  # Bad comma usage
        "add D0, D1, D2, D3",  # Too many args
        "li D0, 32",  # Immediate out of range
        "li D0, -2",  # Immediate out of range
        "li D0, # comment 2",  # Bad comment location
    ],
)
def test_invalid_programs(code):
    with pytest.raises(ValueError):
        parser.parse(code)
