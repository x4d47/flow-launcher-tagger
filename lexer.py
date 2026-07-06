from dataclasses import dataclass
from enum import StrEnum, auto


class CommandKeyword(StrEnum):
    ADD_TAG = "+"
    REMOVE_TAG = "-"


class TokenType(StrEnum):
    NOTHING = auto()
    SPACE = auto()
    IDENTIFIER = auto()
    OP_ADD = auto()
    OP_REM = auto()


@dataclass(frozen=True)
class Token:
    type: TokenType
    value: str


class Lexer:
    def __init__(self, input: str) -> None:
        self.input: str = input

    @property
    def tokens(self):
        parts = self.input.split(maxsplit=2)

        if not parts:
            yield Token(TokenType.NOTHING, "")
            return

        for part in parts:
            match part:
                case CommandKeyword.ADD_TAG:
                    yield Token(TokenType.OP_ADD, part)
                case CommandKeyword.REMOVE_TAG:
                    yield Token(TokenType.OP_REM, part)
                case _:
                    yield Token(TokenType.IDENTIFIER, part)

        if self.input.endswith(" "):
            yield Token(TokenType.SPACE, " ")
