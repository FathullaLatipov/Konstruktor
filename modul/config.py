from pathlib import Path
from typing import Any

from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.executors.pool import ProcessPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pydantic.v1 import BaseSettings

# from apscheduler.executors.asyncio import AsyncIOExecutor
# from apscheduler.executors.pool import ProcessPoolExecutor
# from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
# from apscheduler.schedulers.asyncio import AsyncIOScheduler
# from pydantic import BaseSettings, validator


DEBUG = True
BASE_DIR = Path(__file__).resolve().parent

MEDIA_ROOT = BASE_DIR / "downloads"


class Settings(BaseSettings):
    # HOST: str
    WEBHOOK_PATH: str = "/webhook/{token}"
    WEBHOOK_URL: str = 'https://8bb4-212-115-114-108.ngrok-free.app/webhook/{token}'

    BOT_TOKEN: str = '996043954:AAGbwv9SCRyklY4-hMsy3yMkZsiDJbDJ6YU'
    # ERROR_CHANNEL: str
    ADMIN: int = 889121031
    # ADMIN_LIST = [ADMIN, 302942780]
    # PAYS: int = -1001726742937
    # CRYPTOMUS_MERCHANT: str
    # DOLLAR_CURRENCY: float = 0
    # CRYPTOMUS_APPKEY: str
    # AI_KEY: str
    # AI_ASSISTANT_KEY: str
    # HISTORY_LIMIT: int = 6
    # IS_LOCAL_BOT: bool
    # CHATGPT_KEY: str
    # SIM_ONLINE: str
    # PROJECT_HOST: str
    # PROJECT_PORT: int
    # RUN_JOBS: bool
    # COUNT_WORKETS: int
    # BOT_IN_RECONSTRUCTION: bool
    # COUNT_BOT_LIMIT: int = 8
    # AAIO_ID: str
    # AAIO_KEY: str
    # AAIO_SECRET_1: str
    # AAIO_SECRET_2: str
    # SPONSORS: dict = {
    #     1044817432: {
    #         'percent': 15,
    #         'referrals': 0
    #     },
    #     5005746701: {
    #         'percent': 10,
    #         'referrals': 0
    #     },
    # }
    SLEEP_TIME: float = .3
    ALLOWED_CONTENT_TYPES: list = ["text",
                                   "photo",
                                   "audio",
                                   "video",
                                   "video_note",
                                   "voice", ]
    USED_UPDATE_TYPES: list = [
        "message",
        "callback_query",
        "chat_member"
    ]

    # DB_URL: str
    #
    # SMM_KEY: str
    # SMM_BASE_URL: str = "https://partner.soc-proof.su"
    # SMM_BASE_API_URL: str = None
    # SMM_SERVICES_URL: str = None
    #
    # INSTAGRAM_LOGIN: str
    # INSTAGRAM_PASSWORD: str
    #
    # TIMEZONE: str = "Europe/Moscow"
    # timezone: Any = None
    #
    # @validator('SMM_BASE_API_URL')
    # def smm_base_api_url(cls, v, values: dict):  # noqa
    #     return f"{values.get('SMM_BASE_URL')}/api/v2?key={values.get('SMM_KEY')}"
    #
    # @validator('SMM_SERVICES_URL')
    # def smm_services_url(cls, v, values: dict):  # noqa
    #     return f"{values.get('SMM_BASE_URL')}/services"
    #
    # @validator("WEBHOOK_URL")
    # def webhook_url(cls, _, values: dict):
    #     return values.get("HOST") + values.get("WEBHOOK_PATH")

    class Config:
        env_file_encoding = 'utf-8'


env_file = "prod.env"

settings_conf = Settings(_env_file=env_file)
#
# TORTOISE_ORM = {
#     "connections": {"default": settings.DB_URL},
#     "apps": {
#         "models": {
#             "models": ["aerich.models", "db.models"],
#             "default_connection": "default",
#         },
#     },
# }

scheduler = AsyncIOScheduler(jobstores={'default': SQLAlchemyJobStore(url="sqlite:///jobs.sqlite")},
                             executors={
                                 'default': AsyncIOExecutor(),
                                 'processpool': ProcessPoolExecutor(max_workers=1)
                             },
                             job_defaults={
                                 'misfire_grace_time': 15 * 60,
                                 "coalesce": False,
                                 "max_instances": 1,
                             }
                             )
