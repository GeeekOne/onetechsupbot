from aiogram.fsm.state import State, StatesGroup

class Communication(StatesGroup):
    waiting_for_message = State()
    chatting = State()