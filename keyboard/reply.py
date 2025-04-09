from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

start_dialog = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='🟢 Начать диалог')]
],
                            resize_keyboard=True)


end_dialog = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='🔴 Завершить диалог')]
],
                            resize_keyboard=True)