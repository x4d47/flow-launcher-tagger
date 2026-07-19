import logging
import os
import subprocess
import webbrowser
from collections.abc import Callable
from pathlib import Path
from typing import override

from flowlauncher.FlowLauncher import FlowLauncher
from flowlauncher.FlowLauncherAPI import FlowLauncherAPI

from core.flowlauncher_types import FlowLauncherResult
from core.lexer import CommandKeyword, Lexer
from core.parser import (
    AddTag,
    AutocompleteContext,
    AutocompleteType,
    Command,
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

logging.basicConfig(
    filename=PLUGIN_DATADIR / "plugin.log",
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


class TagsPlugin(FlowLauncher):
    def __init__(self):
        self.command_registry: dict[
            Command, Callable[..., FlowLauncherResult | None]
        ] = {
            GetProgramsByTag: self.get_programs_by_tag,
            AddTag: self.add_tag,
            RemoveTag: self.remove_tag,
        }

        try:
            self.program_manager: ProgramManager = ProgramManager.from_file(
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
            self.tag_manager: TagManager = TagManager.from_file(
                PLUGIN_DATADIR / "tags.json"
            )
            logger.info("Loaded tags from file")
        except Exception as e:
            logger.exception("Failed to load tags from file: %s", e)
            self.tag_manager = TagManager()

        super().__init__()

    @override
    def query(self, param: str = "") -> list[FlowLauncherResult]:
        logger.info("Query: %r", param)

        results: list[FlowLauncherResult] = []

        lexer = Lexer(param)
        parser = Parser()

        try:
            for token in lexer.tokens:
                parser.parse_token(token)

            parser_result = parser.get_result()
        except ParserError as e:
            logger.exception("Parser error: %s", e)
            # return [e.as_flowlauncher_result()]
            return results

        # logger.debug(parser_result)

        results.extend(self.autocomplete(param, parser_result.autocomplete_context))

        return results

    @override
    def context_menu(self, data):
        return [
            {
                "Title": "Hello World Python's Context menu",
                "SubTitle": "Press enter to open Flow the plugin's repo in GitHub",
                "IcoPath": "Images/app.png",
                "JsonRPCAction": {
                    "method": "open_url",
                    "parameters": [
                        "https://github.com/Flow-Launcher/Flow.Launcher.Plugin.HelloWorldPython"
                    ],
                },
            }
        ]

    def open_url(self, url: str):
        _ = webbrowser.open(url)

    def launch_program(self, path: str):
        _ = subprocess.Popen(path)

    def autocomplete_command(self, base_query: str) -> list[FlowLauncherResult]:
        SCORE: int = 100  # big enough for commands to appear at the top of the list

        return [
            {
                "Title": "Add tag",
                "QuerySuggestionText": "type tag name or select from the list",
                "IcoPath": "Images/transparent.png",
                "JsonRPCAction": {
                    "method": "Flow.Launcher.ChangeQuery",
                    "parameters": [
                        f"{base_query}{CommandKeyword.ADD_TAG} ",
                        False,
                    ],
                    "dontHideAfterAction": True,
                },
                "Score": SCORE,
            },
            {
                "Title": "Remove tag",
                "QuerySuggestionText": "type tag name or select from the list",
                "IcoPath": "Images/transparent.png",
                "JsonRPCAction": {
                    "method": "Flow.Launcher.ChangeQuery",
                    "parameters": [
                        f"{base_query}{CommandKeyword.REMOVE_TAG} ",
                        False,
                    ],
                    "dontHideAfterAction": True,
                },
                "Score": SCORE,
            },
        ]

    def autocomplete_tag(self, base_query: str, prefix: str) -> list[FlowLauncherResult]:
        results: list[FlowLauncherResult] = []

        for tag in self.tag_manager.tags:
            if tag.startswith(prefix):
                results.append(
                    {
                        "Title": f"{tag}",
                        "IcoPath": "Images/transparent.png",
                        "QuerySuggestionText": f"{tag}",
                        "JsonRPCAction": {
                            "method": "Flow.Launcher.ChangeQuery",
                            "parameters": [f"{base_query}{tag} ", False],
                            "dontHideAfterAction": True,
                        },
                    }
                )

        return results

    def autocomplete_program(self, base_query: str, prefix: str) -> list[FlowLauncherResult]:
        results: list[FlowLauncherResult] = [{"Title": "autocomplete_program"}]

        return results

    def autocomplete(self, param: str, context: AutocompleteContext) -> list[FlowLauncherResult]:
        result: list[FlowLauncherResult] = []

        if context.prefix and param.endswith(context.prefix):
            stripped = param[:-len(context.prefix)]
        else:
            stripped = param

        if stripped and not stripped.endswith(" "):
            stripped += " "

        base_query = f"{PLUGIN_KEYWORD} {stripped}"

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

    def get_programs_by_tag(self) -> FlowLauncherResult:
        return FlowLauncherResult()

    def add_tag(self, tag: str, program_name: str):
        program: Program | None = self.program_manager.find_one(program_name)

        if program is not None:
            self.tag_manager.add(program, tag)

            FlowLauncherAPI.show_msg(
                "Success", f"Assigned tag '{tag}' to program '{program_name}'"
            )

            self.tag_manager.to_file(
                PLUGIN_DATADIR / "tags.json"
            )  # todo: catch possible exception
        else:
            FlowLauncherAPI.show_msg(
                "Cannot assign tag", f"Program '{program}' not found."
            )

    def remove_tag(self, _tag: str, _program_name: str):
        pass


if __name__ == "__main__":
    _ = TagsPlugin()
