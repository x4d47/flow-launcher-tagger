# ruff: noqa: E402

import sys
from pathlib import Path

plugindir = Path.absolute(Path(__file__).parent)
sys.path.insert(0, str(plugindir / ".venv" / "Lib" / "site-packages"))

import logging
import os
from typing import Unpack, override

from flogin import (
    ExecuteResponse,
    Plugin,
    Query,
    Result,
    ResultConstructorKwargs,
)
from flogin.flow.api import FlowLauncherAPI

from core.lexer import CommandKeyword, Lexer
from core.parser import (
    AddTag,
    AutocompleteContext,
    AutocompleteType,
    GetProgramsByTag,
    Parser,
    ParserError,
    RemoveTag,
)
from core.program_manager import ProgramManager
from core.programs import Program
from core.tag_manager import TagManager

appdata = os.environ.get("APPDATA")

PLUGIN_KEYWORD = "tag"
PLUGIN_DATADIR = (
    (Path(appdata) / "FlowLauncher" / "Cache" / "Plugins" / "Tags")
    if appdata
    else Path(".")
)

# PLUGIN_DATADIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=PLUGIN_DATADIR / "plugin.log",
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


class ChangeQueryResult(Result):
    def __init__(
        self,
        new_query: str,
        api: FlowLauncherAPI,
        **kwargs: Unpack[ResultConstructorKwargs],
    ):
        super().__init__(**kwargs)
        self.new_query: str = new_query
        self.api: FlowLauncherAPI = api

    @override
    async def callback(self):
        await self.api.change_query(self.new_query, requery=False)
        return ExecuteResponse(hide=False)


class LaunchProgramResult(Result):
    def __init__(
        self,
        program: Program,
        api: FlowLauncherAPI,
        **kwargs: Unpack[ResultConstructorKwargs],
    ):
        super().__init__(**kwargs)
        self.program: Program = program
        self.api: FlowLauncherAPI = api

    @override
    async def callback(self):
        if self.program.launch() is None:
            await self.api.show_error_message(
                "Couldn't launch program", "Program path is not specified"
            )
        return ExecuteResponse(hide=True)


# largest score value in FlowLauncher (2^31 - 1)
MAX_SCORE: int = 2_147_483_647


class TagsPlugin(Plugin):
    def __init__(self):
        super().__init__()
        self.program_manager: ProgramManager
        self.tag_manager: TagManager

    @Plugin.event
    async def on_initialization(self):
        try:
            self.program_manager = ProgramManager.from_file(
                PLUGIN_DATADIR / "programs.json"
            )
            logger.info("Loaded programs from file")
        except (
            Exception
        ) as e:  # todo: should differentiate access problems from file unexistence
            logger.exception("Failed to load programs from file: %s", e)
            self.program_manager = ProgramManager.from_os()
            self.program_manager.to_file(PLUGIN_DATADIR / "programs.json")

        try:
            self.tag_manager = TagManager.from_file(PLUGIN_DATADIR / "tags.json")
            logger.info("Loaded tags from file")
        except Exception as e:
            logger.exception("Failed to load tags from file: %s", e)
            self.tag_manager = TagManager()

    @Plugin.search()
    async def search_handler(self, query: Query[None]) -> list[Result]:
        logger.debug("Query: %r", query)

        results: list[Result] = []

        text = query.text

        if query.original_query.endswith(" "):
            text += " "

        lexer = Lexer(text)
        parser = Parser()

        try:
            for token in lexer.tokens:
                parser.parse_token(token)

            parser_result = parser.get_result()
        except ParserError as e:
            logger.exception("Parser error: %s", e)
            return results

        results.extend(
            self.autocomplete(query.original_query, parser_result.autocomplete_context)
        )

        match parser_result.command:
            case GetProgramsByTag():
                results.extend(self.get_programs_by_tag(parser_result.command.tag_name))
            case None:
                pass
            case _:
                pass

        return results

    def get_programs_by_tag(self, tag: str) -> list[Result]:
        result: list[Result] = []

        for program in self.tag_manager.search_by_tag(tag):
            result.append(
                LaunchProgramResult(
                    title=f"{program.name}",
                    query_suggestion_text=f"{program.name}",
                    icon=program.icon_to_data_uri("Images/transparent.png"),
                    program=program,
                    api=self.api,
                )
            )

        return result

    def autocomplete_command(self, base_query: str) -> list[Result]:
        return [
            ChangeQueryResult(
                title="Add tag",
                query_suggestion_text=f"{CommandKeyword.ADD_TAG}",
                icon="Images/transparent.png",
                score=MAX_SCORE,
                new_query=f"{base_query}{CommandKeyword.ADD_TAG} ",
                api=self.api,
            ),
            ChangeQueryResult(
                title="Remove tag",
                query_suggestion_text=f"{CommandKeyword.REMOVE_TAG}",
                icon="Images/transparent.png",
                score=MAX_SCORE,
                new_query=f"{base_query}{CommandKeyword.REMOVE_TAG} ",
                api=self.api,
            ),
        ]

    def autocomplete_tag(self, base_query: str, prefix: str) -> list[Result]:
        results: list[Result] = []

        for tag in self.tag_manager.tags:
            if tag.startswith(prefix):
                results.append(
                    ChangeQueryResult(
                        title=f"{tag}",
                        query_suggestion_text=f"{tag}",
                        icon="Images/transparent.png",
                        new_query=f"{base_query}{tag} ",
                        api=self.api,
                    )
                )

        return results

    def autocomplete_program(self, base_query: str, prefix: str) -> list[Result]:
        results: list[Result] = []

        logger.debug("Prefix: %s", prefix)

        if prefix:
            programs_found: list[Program] = self.program_manager.find(prefix)
        else:
            programs_found = self.program_manager.programs

        for program in programs_found:
            results.append(
                ChangeQueryResult(
                    title=f"{program.name}",
                    query_suggestion_text=f"{program.name}",
                    icon=program.icon_to_data_uri("Images/transparent.png"),
                    new_query=f"{base_query}{program.name} ",
                    api=self.api,
                )
            )

        return results

    def autocomplete(self, query: str, context: AutocompleteContext) -> list[Result]:
        result: list[Result] = []

        if context.prefix and query.endswith(context.prefix):
            # query without autocomplete prefix
            base_query = query[: -len(context.prefix)]
        else:
            base_query = query

        if base_query and not base_query.endswith(" "):
            base_query += " "

        match context.type:
            case [AutocompleteType.COMMAND, AutocompleteType.TAG]:
                result = [
                    *self.autocomplete_command(base_query),
                    *self.autocomplete_tag(base_query, context.prefix),
                ]
            case [AutocompleteType.TAG]:
                result = self.autocomplete_tag(base_query, context.prefix)
            case [AutocompleteType.PROGRAM]:
                result = self.autocomplete_program(base_query, context.prefix)
            case _:
                pass

        return result


if __name__ == "__main__":
    try:
        plugin = TagsPlugin()
        plugin.run(setup_default_log_handler=False)
    except Exception as e:
        logger.exception("Unexpected exception: %r", e)
