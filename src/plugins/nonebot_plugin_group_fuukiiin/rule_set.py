import re

from nonebot.adapters.onebot.v11 import Bot, Event, GroupMessageEvent
from nonebot.log import logger
from nonebot.typing import T_State

from .config import plugin_config
from .utils import is_alphabet


async def is_long_letters_text(event: Event, state: T_State):
    # 判定是否为超长(len>fuuki_pinyin_check_length)全字母文本
    msg = event.get_plaintext()

    logger.debug(f"get msg:{msg}")

    url_parser = re.compile(r"https?://[a-zA-Z0-9]+\.[a-zA-Z0-9]+")
    if re.match(url_parser, msg):
        return False

    if len(msg) > plugin_config.fuuki_pinyin_check_length:  # 处理掉可能存在的字符插入攻击
        logger.debug(
            f"msg length is over {plugin_config.fuuki_pinyin_check_length}, hit"
        )

        cut_msg_length = min(len(msg), 50)
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
        elif 10 < cut_msg_length <= 20 and outlier < 6:
            logger.debug(f"pinyin check hit by midium case({outlier})")
            state["clear_msg"] = "".join(cut_msg)
            return True
        elif cut_msg_length > 20 and outlier / cut_msg_length < 0.3:
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
    """
    检查群组是否需要管理
    """
    logger.debug(f"got group id: {event.group_id}")
    if not plugin_config.fuuki_managed_group:
        return False

    for group in plugin_config.fuuki_managed_group:
        if str(group.group_id) == str(event.group_id):
            logger.debug("group need manage")
            return True

    return False


async def only_targeted_member(event: GroupMessageEvent):
    """
    如果群组需要管理，检查是否有针对用户.
    如果有针对用户，则只有该针对用户被管理，其他用户不受管理;
    如果没有针对用户，则所有用户都受管理
    """
    group_id = event.group_id
    user_id = event.user_id
    logger.debug(f"got group id:{group_id}, user id:{user_id}")

    for group in plugin_config.fuuki_managed_group:
        if str(group.group_id) == str(group_id):
            if str(user_id) in group.targeted_members:
                logger.debug(f"only targeted member managed: {user_id}")
                return True
            else:
                logger.debug("all member need manage")
                return False

    return False
