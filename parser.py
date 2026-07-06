from dataclasses import dataclass
from enum import Enum, auto
from typing import Protocol

from flowlauncher_types import FlowLauncherResult
from lexer import Token, TokenType


class ParserError(ValueError):
    def as_flowlauncher_result(self) -> FlowLauncherResult:
        return FlowLauncherResult(
            Title="Syntax error",
            IcoPath="Images/transparent.png",
        )


class ParserState(Enum):
    START = auto()
    EXPECT_TAG = auto()
    EXPECT_PROGRAM = auto()
    COMMAND_READY = auto()


class Command(Protocol):
    pass


@dataclass(frozen=True)
class GetProgramsByTag(Command):
    tag_name: str


@dataclass(frozen=True)
class AddTag(Command):
    tag_name: str
    program_name: str


@dataclass(frozen=True)
class RemoveTag(Command):
    tag_name: str
    program_name: str


class AutocompleteType(Enum):
    COMMAND = auto()
    TAG = auto()
    PROGRAM = auto()
    NOTHING = auto()


@dataclass(frozen=True)
class AutocompleteContext:
    type: list[AutocompleteType]
    prefix: str


@dataclass(frozen=True)
class ParserResult:
    command: Command | None
    tag_name: str | None
    program_name: str | None
    autocomplete_context: AutocompleteContext


class Parser:
    def __init__(self) -> None:
        self.state: ParserState = ParserState.START
        self.current_token: Token = Token(TokenType.NOTHING, "")
        self.command: Command | None = None
        self.tag_name: str | None = None
        self.program_name: str | None = None

    def parse_token(self, token: Token) -> None:
        self.current_token = token

        match self.state:
            case ParserState.START:
                match token.type:
                    case TokenType.SPACE:
                        pass
                    case TokenType.NOTHING:
                        pass
                    case TokenType.IDENTIFIER:
                        self.command = GetProgramsByTag
                        self.tag_name = token.value
                        self.state = ParserState.COMMAND_READY
                    case TokenType.OP_ADD:
                        self.command = AddTag
                        self.state = ParserState.EXPECT_TAG
                    case TokenType.OP_REM:
                        self.command = RemoveTag
                        self.state = ParserState.EXPECT_TAG

            case ParserState.EXPECT_TAG:
                if token.type == TokenType.IDENTIFIER:
                    self.tag_name = token.value
                    self.state = ParserState.EXPECT_PROGRAM
                elif token.type == TokenType.SPACE:
                    pass
                else:
                    raise ParserError("expected IDENTIFIER")

            case ParserState.EXPECT_PROGRAM:
                if token.type == TokenType.IDENTIFIER:
                    self.program_name = token.value
                    self.state = ParserState.COMMAND_READY
                elif token.type == TokenType.SPACE:
                    pass
                else:
                    raise ParserError("expected IDENTIFIER")

            case ParserState.COMMAND_READY:
                raise ParserError("unexpected extra token")

    @property
    def autocomplete_context(self) -> AutocompleteContext:
        if self.current_token.type == TokenType.SPACE:
            match self.state:
                case ParserState.START:
                    # complete tag and command
                    return AutocompleteContext(
                        [AutocompleteType.TAG, AutocompleteType.PROGRAM],
                        self.current_token.value,
                    )
                case ParserState.EXPECT_TAG:
                    # complete tag
                    return AutocompleteContext(
                        [AutocompleteType.TAG],
                        "",
                    )
                case ParserState.EXPECT_PROGRAM:
                    # complete program
                    return AutocompleteContext(
                        [AutocompleteType.PROGRAM],
                        "",
                    )
                case ParserState.COMMAND_READY:
                    # complete nothing
                    return AutocompleteContext(
                        [AutocompleteType.NOTHING],
                        "",
                    )
        else:
            if self.state == ParserState.COMMAND_READY:
                return AutocompleteContext(
                    [AutocompleteType.PROGRAM],
                    self.current_token.value,
                )

            match self.current_token.type:
                case TokenType.NOTHING:
                    # at the beginning, complete tag and command
                    return AutocompleteContext(
                        [AutocompleteType.TAG, AutocompleteType.COMMAND],
                        self.current_token.value,
                    )

                case TokenType.IDENTIFIER:
                    # complete tag
                    if self.state == ParserState.EXPECT_PROGRAM:
                        return AutocompleteContext(
                            [AutocompleteType.TAG],
                            self.current_token.value,
                        )
                    # or program
                    return AutocompleteContext(
                        [AutocompleteType.PROGRAM],
                        self.current_token.value,
                    )
                case TokenType.OP_ADD:
                    # complete tag
                    return AutocompleteContext(
                        [AutocompleteType.TAG],
                        "",
                    )
                case TokenType.OP_REM:
                    # complete tag
                    return AutocompleteContext(
                        [AutocompleteType.TAG],
                        "",
                    )

    def get_result(self) -> ParserResult:
        return ParserResult(
            self.command, self.tag_name, self.program_name, self.autocomplete_context
        )
