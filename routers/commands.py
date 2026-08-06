from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, LinkPreviewOptions, Message

from config import Settings
from services.caption_style_store import CaptionStyleStore
from services.format_preference_store import FormatPreferenceStore
from utils.callbacks import CaptionStyleCallback, FormatCallback
from utils.keyboards import (
    about_keyboard,
    caption_style_keyboard,
    help_keyboard,
    start_keyboard,
    format_preference_keyboard,
)
from utils import text

router = Router(name="commands")


async def _send_start(target: Message, name: str) -> None:
    await target.answer(
        text.START_TEXT.format(name=name),
        reply_markup=start_keyboard(),
        link_preview_options=LinkPreviewOptions(is_disabled=True),
    )


def _is_authorized(message: Message, settings: Settings) -> bool:
    return bool(message.from_user) and message.from_user.id in settings.auth_users


@router.message(Command("start"), F.chat.type == "private")
async def start_command(message: Message, settings: Settings) -> None:
    if not _is_authorized(message, settings):
        await message.answer("🚫 You're not authorized to use this bot.")
        return
    first_name = message.from_user.first_name if message.from_user else "there"
    await _send_start(message, first_name)


@router.message(Command("help"), F.chat.type == "private")
async def help_command(message: Message, settings: Settings) -> None:
    if not _is_authorized(message, settings):
        await message.answer("🚫 You're not authorized to use this bot.")
        return
    await message.answer(
        text.HELP_TEXT,
        reply_markup=help_keyboard(),
        link_preview_options=LinkPreviewOptions(is_disabled=True),
    )


@router.message(Command("about"), F.chat.type == "private")
async def about_command(message: Message, settings: Settings) -> None:
    if not _is_authorized(message, settings):
        await message.answer("🚫 You're not authorized to use this bot.")
        return
    await message.answer(
        text.ABOUT_TEXT,
        reply_markup=about_keyboard(),
        link_preview_options=LinkPreviewOptions(is_disabled=True),
    )


@router.message(Command("setformat"), F.chat.type == "private")
async def setformat_command(
    message: Message, settings: Settings, format_store: FormatPreferenceStore
) -> None:
    if not _is_authorized(message, settings):
        await message.answer("🚫 You're not authorized to use this bot.")
        return
    current = format_store.get(message.from_user.id)
    await message.answer(
        "Choose your default send format for direct links:",
        reply_markup=format_preference_keyboard(current),
    )


@router.callback_query(FormatCallback.filter())
async def format_callback(
    query: CallbackQuery, callback_data: FormatCallback, format_store: FormatPreferenceStore
) -> None:
    if not query.message or not query.from_user:
        await query.answer()
        return
    if callback_data.value == "ask":
        format_store.clear(query.from_user.id)
    else:
        format_store.set(query.from_user.id, callback_data.value)
    await query.message.edit_reply_markup(
        reply_markup=format_preference_keyboard(callback_data.value)
    )
    await query.answer("Saved!")

@router.message(Command("setcaption"), F.chat.type == "private")
async def setcaption_command(
    message: Message, settings: Settings, caption_store: CaptionStyleStore
) -> None:
    if not _is_authorized(message, settings):
        await message.answer("🚫 You're not authorized to use this bot.")
        return
    current = caption_store.get(message.from_user.id)
    await message.answer(
        "Choose your caption style:",
        reply_markup=caption_style_keyboard(current),
    )


@router.callback_query(CaptionStyleCallback.filter())
async def caption_style_callback(
    query: CallbackQuery, callback_data: CaptionStyleCallback, caption_store: CaptionStyleStore
) -> None:
    if not query.message or not query.from_user:
        await query.answer()
        return
    caption_store.set(query.from_user.id, callback_data.value)
    await query.message.edit_reply_markup(
        reply_markup=caption_style_keyboard(callback_data.value)
    )
    await query.answer("Saved!")


async def handle_ui_callback(callback: CallbackQuery, action: str) -> None:
    if not callback.message:
        await callback.answer()
        return

    if action == "home":
        name = callback.from_user.first_name if callback.from_user else "there"
        await callback.message.edit_text(
            text.START_TEXT.format(name=name),
            reply_markup=start_keyboard(),
            link_preview_options=LinkPreviewOptions(is_disabled=True),
        )
    elif action == "help":
        await callback.message.edit_text(
            text.HELP_TEXT,
            reply_markup=help_keyboard(),
            link_preview_options=LinkPreviewOptions(is_disabled=True),
        )
    elif action == "about":
        await callback.message.edit_text(
            text.ABOUT_TEXT,
            reply_markup=about_keyboard(),
            link_preview_options=LinkPreviewOptions(is_disabled=True),
        )
    elif action == "close":
        await callback.message.delete()

    await callback.answer()
