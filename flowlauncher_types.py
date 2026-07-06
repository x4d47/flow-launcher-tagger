from typing import NotRequired, TypedDict

type JsonValue = (
    str | int | float | bool | list[JsonValue] | dict[str, JsonValue] | None
)


class JsonRPCAction(TypedDict):
    method: str
    parameters: list[object]
    dontHideAfterAction: NotRequired[bool]


class GlyphInfo(TypedDict):
    FontFamily: str
    Glyph: str


class PreviewInfo(TypedDict):
    PreviewImagePath: NotRequired[str]
    IsMedia: NotRequired[bool]
    Description: NotRequired[str]
    FilePath: NotRequired[str]


# --- Головний словник ---


class FlowLauncherResult(TypedDict):
    # Текст та підказки
    Title: NotRequired[str]
    SubTitle: NotRequired[str]
    TitleToolTip: NotRequired[str]
    SubTitleToolTip: NotRequired[str]
    AutoCompleteText: NotRequired[str]
    QuerySuggestionText: NotRequired[str]
    CopyText: NotRequired[str]
    ActionKeywordAssigned: NotRequired[str]

    # Іконки
    IcoPath: NotRequired[str]
    BadgeIcoPath: NotRequired[str]
    RoundedIcon: NotRequired[bool]
    Glyph: NotRequired[GlyphInfo]
    ShowBadge: NotRequired[bool]

    # Візуал та сортування
    Score: NotRequired[int]
    TitleHighlightData: NotRequired[list[int]]
    ProgressBar: NotRequired[int]
    ProgressBarColor: NotRequired[str]
    Preview: NotRequired[PreviewInfo]

    # Робота з даними
    ContextData: NotRequired[JsonValue]
    RecordKey: NotRequired[str]
    AddSelectedCount: NotRequired[bool]

    # Специфіка JSON-RPC
    JsonRPCAction: NotRequired[JsonRPCAction]
