import asyncio

from aiogram import Bot, Router, types, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta

from filters.chat_types import ChatTypeFilter
from keyboard.reply import start_dialog, end_dialog
from common.states import Communication

user_private = Router()
user_private.message.filter(ChatTypeFilter(['private']))

# Словарь для хранения активных диалогов {user_id: developer_message_id}
active_dialogs = {}

@user_private.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        "Приветствую, для начала диалога нажмите кнопку ниже ",
        reply_markup=start_dialog
        )


@user_private.message(F.text.lower() == "🟢 начать диалог")
async def cmd_start_dialog(message: types.Message, state: FSMContext):

    user_id = message.from_user.id
    if user_id in active_dialogs:
        await message.answer(
            "Вы уже находитесь в активном диалоге. Можете продолжать писать или завершить его.",
            reply_markup=end_dialog # Показываем кнопку "Завершить диалог"
        )

        await state.set_state(Communication.chatting)
        return

    await state.set_state(Communication.waiting_for_message)
    await message.answer(
        "📝 Напишите ваше сообщение.\n\n"
        "Вы можете продолжать диалог, пока не нажмёте \"🔴 Завершить диалог\".",
        reply_markup=end_dialog
    )


@user_private.message(Communication.waiting_for_message, F.content_type == types.ContentType.TEXT)
async def handle_first_user_message(message: types.Message, state: FSMContext, bot: Bot):
    workflow_data = bot.workflow_data
    dev_chat_id = workflow_data.get('dev_chat_id')

    user = message.from_user

    try:
        await bot.send_message(
            dev_chat_id,
            text=(
                f"📩 *Сообщение от пользователя:*\n"
                f"👤 *{user.full_name}* (@{user.username})\n"
                f"🆔 *ID:* `{user.id}`"
                ),
            parse_mode="Markdown"
        )

        forwarded = await bot.forward_message(dev_chat_id, message.chat.id, message.message_id)

        # Сохраняем ID сообщения
        active_dialogs[user.id] = {
            "forwarded_msg_id": forwarded.message_id,
            "user_id": user.id,
            "last_update": datetime.now(),
            "timeout_task": asyncio.Task
        }

        await state.set_state(Communication.chatting)

        await message.answer(
            "Ваше сообщение отправлено.\n"
            "Можете продолжать диалог или завершить его."
            )

    except Exception as e:
        print(f"Ошибка при отправке первого сообщения от {user.id} разработчику: {e}")
        await message.answer("К сожалению, произошла ошибка при отправке вашего сообщения. Попробуйте позже.")
        # Очищаем состояние при ошибке
        await state.clear()


@user_private.message(Communication.chatting, F.content_type == "text")
async def handle_user_followups(message: types.Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    workflow_data = bot.workflow_data
    dev_chat_id = workflow_data.get('dev_chat_id')

    if user_id not in active_dialogs:
        await message.answer(
            "❗ Диалог завершён. Нажмите кнопку \"🟢 Начать диалог\", чтобы начать заново.",
            reply_markup=start_dialog
            )
        await state.clear()
        return

    if message.text.lower() == "🔴 завершить диалог":
        await state.clear()
        active_dialogs.pop(user_id, None)
        await message.answer("✅ Диалог завершён", reply_markup=start_dialog)
        return

    try:
        forwarded = await bot.forward_message(dev_chat_id, message.chat.id, message.message_id)
        active_dialogs[user_id] = {
            "forwarded_msg_id": forwarded.message_id,
            "user_id": user_id,
        }
    except Exception as e:
        print(f"[Ошибка] {e}")
        await message.answer("Произошла ошибка при пересылке.")
