from nonebot.adapters.onebot.v11 import Bot, Event, GroupMessageEvent
from nonebot.log import logger

from .config import plugin_config


async def is_long_letters_text(event: Event):
    # 判定是否为超长(len>5)全字母文本
    msg = event.get_plaintext()
    logger.debug(f"get msg:{msg}")
    if len(msg) > 5 and (
        msg.replace(" ", "").encode("UTF-8").isalpha()
        or msg[:-1].replace(" ", "").encode("UTF-8").isalpha()
    ):  # 处理掉可能存在的标点符号
        logger.debug("long_letters_text check is pass")
        return True

    return False


async def group_need_manage(event: GroupMessageEvent):
    logger.debug(f"got group id:{event.group_id}")
    if not plugin_config.managed_group:
        return False
    elif str(event.group_id) in plugin_config.managed_group:
        logger.debug("group need manage")
        return True

    return False
