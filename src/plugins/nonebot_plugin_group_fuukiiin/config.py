from nonebot import get_driver
from pydantic import BaseSettings


class Config(BaseSettings):
    # Your Config Here
    max_allowed_frequent_speaking_count: int = 6
    frequent_speaking_timeout: int = 4
    max_allowed_repeat_speaking_count: int = 4
    repeat_speaking_timeout: int = 10

    fuuki_managed_group: list[str] = []
    fuuki_specific_member: list[str] = []

    class Config:
        extra = "ignore"


global_config = get_driver().config
plugin_config = Config.parse_obj(global_config)
