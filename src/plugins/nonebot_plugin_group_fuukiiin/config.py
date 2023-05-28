from typing import Optional

from nonebot import get_driver
from nonebot.log import logger
from pydantic import BaseModel, BaseSettings


class ManagedGroup(BaseModel):
    group_id: str
    targeted_members: Optional[list[str]] = None


class Config(BaseSettings):
    # Your Config Here
    max_allowed_frequent_speaking_count: int = 6
    frequent_speaking_timeout: int = 4
    max_allowed_repeat_speaking_count: int = 4
    repeat_speaking_timeout: int = 10

    fuuki_managed_group: list[ManagedGroup] = []
    fuuki_pinyin_delete: bool = True
    fuuki_pinyin_check_length: int = 5
    fuuki_pinyin_delete_feedback: bool = True

    class Config:
        extra = "ignore"


global_config = get_driver().config
plugin_config = Config.parse_obj(global_config)
logger.debug(f"plugin_config: {plugin_config.json(indent=4, ensure_ascii=False)}")
