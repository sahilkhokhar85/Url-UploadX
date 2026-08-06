from aiogram.filters.callback_data import CallbackData


class UiCallback(CallbackData, prefix="ui"):
    action: str


class RequestCallback(CallbackData, prefix="req"):
    token: str
    action: str

class FormatCallback(CallbackData, prefix="fmt"):
    value: str

class CaptionStyleCallback(CallbackData, prefix="cap"):
    value: str
