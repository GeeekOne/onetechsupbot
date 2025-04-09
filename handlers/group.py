import asyncio
import logging

from aiogram import Bot, Dispatcher, Router, types, F
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta


from filters.chat_types import ChatTypeFilter
from handlers.user_private import active_dialogs
from keyboard.reply import start_dialog

group_router = Router()
group_router.message.filter(ChatTypeFilter(['group', 'supergroup'])) # Слушаем только группы/супергруппы


async def schedule_dialog_timeout(user_id: int, bot: Bot, state: FSMContext, delay: int = 600):
    logging.info(f"[debug] ⏱️ Запущен таймер очистки для {user_id}")

    await asyncio.sleep(delay)

    dialog = active_dialogs.get(user_id)
    if not dialog:
        return  # Если диалога уже нет, выходим

    last_update = dialog.get("last_update")

    if last_update is None or datetime.utcnow() - last_update >= timedelta(seconds=delay):
        logging.info(f"[timeout] ⏳ Диалог с user_id={user_id} завершён по таймауту")
        await state.clear()
        active_dialogs.pop(user_id, None)

        try:
            await bot.send_message(
                chat_id=user_id,
                text="⌛ Диалог был завершён автоматически.\n"
                     "Если у вас остались вопросы — нажмите кнопку ниже, чтобы начать заново.",
                     reply_markup=start_dialog
            )

        except Exception as e:
            logging.info(f"[timeout] ⚠️ Ошибка при уведомлении пользователя {user_id}: {e}")
    else:
        logging.info(f"[timeout] ✅ Диалог с user_id={user_id} всё ещё активен, сброс не требуется.")

@group_router.message(F.reply_to_message)
async def reply_to_user_from_dev(message: types.Message, bot: Bot):
    dp: Dispatcher = bot.workflow_data['dp']
    # Найти user_id по forwarded_msg_id
    forwarded_id = message.reply_to_message.message_id

    # Перебрать active_dialogs и найти совпадение
    user_id = None
    for uid, dialog_data in active_dialogs.items():
        if isinstance(dialog_data, dict) and dialog_data.get("forwarded_msg_id") == forwarded_id:
            user_id = dialog_data.get("user_id")
            break

    if user_id is None:
        await message.reply("Пользователь завершил диалог или не найден.")
        return

    try:
        await bot.send_message(
            chat_id=user_id,
            text=f"{message.text}",
            parse_mode="Markdown"
        )

        await bot.set_message_reaction(
            chat_id=message.chat.id,
            message_id=message.reply_to_message.message_id,
            reaction=[types.ReactionTypeEmoji(emoji="👨‍💻")]
        )

        dialog = active_dialogs.get(user_id)
        if dialog:
            dialog["last_update"] = datetime.utcnow()

            # Отменяем старый таймер, если есть
            old_task: asyncio.Task = dialog.get("timeout_task")
            if old_task and isinstance(old_task, asyncio.Task) and not old_task.done():
                old_task.cancel()

            state: FSMContext = dp.fsm.get_context(bot=bot, chat_id=user_id, user_id=user_id)

            # Запускаем новый таймер
            new_task = asyncio.create_task(schedule_dialog_timeout(user_id=user_id, state=state, bot=bot))
            dialog["timeout_task"] = new_task

    except Exception as e:
        logging.info(f"Ошибка отправки пользователю {user_id} {e}")
        await message.reply(f"Не удалось отправить ответ: {e}")
