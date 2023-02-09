from nonebot.adapters.onebot.v11 import Bot, Event, GroupMessageEvent
from nonebot.log import logger
from nonebot.typing import T_State

from .config import plugin_config
from .utils import is_alphabet


async def is_long_letters_text(event: Event, state: T_State):
    # 判定是否为超长(len>5)全字母文本
    msg = event.get_plaintext()

    logger.debug(f"get msg:{msg}")

    if len(msg) > 5:  # 处理掉可能存在的字符插入攻击
        logger.debug("msg length is over 5, hit")

        cut_msg_length = len(msg) if len(msg) <= 50 else 50
        cut_msg = list(msg[:50])

        outlier = 0
        for pos, word in enumerate(cut_msg):
            if not is_alphabet(word):
                outlier += 1
                cut_msg[pos] = " "

        logger.debug(f"sentense length: {cut_msg_length}, outlier: {outlier}")

        if cut_msg_length <= 10 and outlier < 4:
            logger.debug(f"pinyin check hit by short case({outlier})")
            state["clear_msg"] = "".join(cut_msg)
            return True
        elif 10 < cut_msg_length <= 20 and outlier < 9:
            logger.debug(f"pinyin check hit by midium case({outlier})")
            state["clear_msg"] = "".join(cut_msg)
            return True
        elif 20 < cut_msg_length and outlier / cut_msg_length < 0.3:
            logger.debug(
                f"pinyin check hit by long case({outlier/cut_msg_length*100}%)"
            )
            state["clear_msg"] = "".join(cut_msg)
            return True
        else:
            logger.debug(f"pinyin check miss when {cut_msg_length}:{outlier}")
            return False

    return False


async def group_need_manage(event: GroupMessageEvent):
    logger.debug(f"got group id:{event.group_id}")
    if not plugin_config.managed_group:
        return False
    elif str(event.group_id) in plugin_config.managed_group:
        logger.debug("group need manage")
        return True

    return False
