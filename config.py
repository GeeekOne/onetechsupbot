from dataclasses import dataclass
from environs import Env


@dataclass
class TgBot:
    token: str
    dev_chat_id: int

@dataclass
class Config:
    tg_bot: TgBot


def load_config(path: str | None = None) -> Config:

    env: Env = Env()
    env.read_env(path)

    return Config(
        tg_bot=TgBot(
            token=env('TOKEN'),
            dev_chat_id=int(env('DEVELOPER_CHAT_ID'))
        )
    )