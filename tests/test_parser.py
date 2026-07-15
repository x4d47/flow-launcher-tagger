import pytest

from core.lexer import CommandKeyword, Lexer
from core.parser import (
    AddTag,
    AutocompleteContext,
    AutocompleteType,
    Parser,
    ParserResult,
    RemoveTag,
)


def parse_input(input: str) -> ParserResult:
    lexer = Lexer(input)
    parser = Parser()

    for token in lexer.tokens:
        parser.parse_token(token)

    return parser.get_result()


@pytest.mark.parametrize(
    "input, expected_result",
    [
        (
            "",
            ParserResult(
                command=None,
                autocomplete_context=AutocompleteContext(
                    [AutocompleteType.COMMAND, AutocompleteType.TAG], ""
                ),
            ),
        )
    ],
)
def test_empty_input(input: str, expected_result: ParserResult):
    lexer = Lexer(input)
    parser = Parser()

    for token in lexer.tokens:
        parser.parse_token(token)

    assert parser.get_result() == expected_result


@pytest.mark.parametrize(
    "input, expected_result",
    [
        (
            " ",  # one space
            ParserResult(
                command=None,
                autocomplete_context=AutocompleteContext(
                    [AutocompleteType.COMMAND, AutocompleteType.TAG], ""
                ),
            ),
        ),
        (
            "  ",  # two spaces
            ParserResult(
                command=None,
                autocomplete_context=AutocompleteContext(
                    [AutocompleteType.COMMAND, AutocompleteType.TAG], ""
                ),
            ),
        ),
    ],
)
def test_space_input(input: str, expected_result: ParserResult):
    assert parse_input(input) == expected_result


@pytest.mark.parametrize(
    "input, expected_result",
    [
        (
            f"{CommandKeyword.ADD_TAG}",
            ParserResult(
                command=None,
                autocomplete_context=AutocompleteContext([AutocompleteType.TAG], ""),
            ),
        ),
        (
            f"{CommandKeyword.ADD_TAG} ",
            ParserResult(
                command=None,
                autocomplete_context=AutocompleteContext([AutocompleteType.TAG], ""),
            ),
        ),
        (
            f"{CommandKeyword.ADD_TAG} TagName",
            ParserResult(
                command=None,
                autocomplete_context=AutocompleteContext(
                    [AutocompleteType.TAG], "TagName"
                ),
            ),
        ),
        (
            f"{CommandKeyword.ADD_TAG} TagName ",
            ParserResult(
                command=None,
                autocomplete_context=AutocompleteContext(
                    [AutocompleteType.PROGRAM], ""
                ),
            ),
        ),
        (
            f"{CommandKeyword.ADD_TAG} TagName Program",
            ParserResult(
                command=AddTag("TagName", "Program"),
                autocomplete_context=AutocompleteContext(
                    [AutocompleteType.PROGRAM], "Program"
                ),
            ),
        ),
        (
            f"{CommandKeyword.ADD_TAG} TagName Program Name",
            ParserResult(
                command=AddTag("TagName", "Program Name"),
                autocomplete_context=AutocompleteContext(
                    [AutocompleteType.PROGRAM], "Program Name"
                ),
            ),
        ),
    ],
)
def test_add_command(input: str, expected_result: ParserResult):
    assert parse_input(input) == expected_result


@pytest.mark.parametrize(
    "input, expected_result",
    [
        (
            f"{CommandKeyword.REMOVE_TAG}",
            ParserResult(
                command=None,
                autocomplete_context=AutocompleteContext([AutocompleteType.TAG], ""),
            ),
        ),
        (
            f"{CommandKeyword.REMOVE_TAG} ",
            ParserResult(
                command=None,
                autocomplete_context=AutocompleteContext([AutocompleteType.TAG], ""),
            ),
        ),
        (
            f"{CommandKeyword.REMOVE_TAG} TagName",
            ParserResult(
                command=None,
                autocomplete_context=AutocompleteContext(
                    [AutocompleteType.TAG], "TagName"
                ),
            ),
        ),
        (
            f"{CommandKeyword.REMOVE_TAG} TagName ",
            ParserResult(
                command=None,
                autocomplete_context=AutocompleteContext(
                    [AutocompleteType.PROGRAM], ""
                ),
            ),
        ),
        (
            f"{CommandKeyword.REMOVE_TAG} TagName Program",
            ParserResult(
                command=RemoveTag("TagName", "Program"),
                autocomplete_context=AutocompleteContext(
                    [AutocompleteType.PROGRAM], "Program"
                ),
            ),
        ),
        (
            f"{CommandKeyword.REMOVE_TAG} TagName Program Name",
            ParserResult(
                command=RemoveTag("TagName", "Program Name"),
                autocomplete_context=AutocompleteContext(
                    [AutocompleteType.PROGRAM], "Program Name"
                ),
            ),
        ),
    ],
)
def test_remove_command(input: str, expected_result: ParserResult):
    assert parse_input(input) == expected_result
