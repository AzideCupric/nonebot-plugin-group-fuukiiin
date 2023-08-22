from collections import Counter

from expiringdict import ExpiringDict
from nonebot import on_message
from nonebot.adapters.onebot.v11 import (
    GROUP_ADMIN,
    GROUP_MEMBER,
    Bot,
    GroupMessageEvent,
    MessageSegment,
)
from nonebot.log import logger

from .rule_set import group_need_manage

MAX_REPEAT_COUNT = 3

repeated_dict = ExpiringDict(max_len=100, max_age_seconds=40)

fuukiiin = on_message(
    permission=GROUP_MEMBER | GROUP_ADMIN, priority=1, rule=group_need_manage
)


@fuukiiin.handle()
async def repeat_fuukiiin(bot: Bot, event: GroupMessageEvent):
    logger.debug("单人复读风纪委员巡逻中!")
    logger.trace(f"风纪委员当前所有记录: {repeated_dict}")
    stripped_msg = event.get_plaintext().strip()
    if event.user_id not in repeated_dict:
        logger.debug(f"风纪委员首次检查到{event.user_id}发送消息: {stripped_msg}，记录中...")
        repeated_dict[event.user_id] = Counter([stripped_msg])
        await fuukiiin.finish()

    user_records = repeated_dict.get(event.user_id)  # 不会取出 "", 因为是一个Counter类的实例
    logger.debug(f"风纪委员检查到{event.user_id}在记录中，检查消息是否重复...")
    assert isinstance(user_records, Counter)
    user_records.update([stripped_msg])
    most_common_message, most_common_count = user_records.most_common(1)[0]
    logger.trace(f"用户{event.user_id}消息记录: {user_records.most_common(3)}")
    if most_common_count > MAX_REPEAT_COUNT:
        logger.debug(
            f"风纪委员检查到重复消息{most_common_message}超过{MAX_REPEAT_COUNT}次，检查发送者身份..."
        )

        match event.sender.role:
            case "admin":
                logger.debug("发送者是管理员，不处以禁言，仅通知发送者")
                user_records.pop(most_common_message)
                await fuukiiin.finish(
                    "检测到管理员" + MessageSegment.at(event.user_id) + "发送重复消息，警告"
                )
            case "member":
                logger.debug("发送者是群员，处以禁言5分钟，通知发送者")
                await bot.set_group_ban(
                    group_id=event.group_id, user_id=event.user_id, duration=60 * 5
                )
                user_records.pop(most_common_message)
                await fuukiiin.finish(
                    MessageSegment.at(event.user_id) + f"检测到重复消息{MAX_REPEAT_COUNT}次，已禁言"
                )
            case _:
                logger.debug("发送者身份未知，不处以禁言，仅通知发送者")
                user_records.pop(most_common_message)
                await fuukiiin.finish(
                    "检测到未知成员" + MessageSegment.at(event.user_id) + "发送重复消息，警告"
                )

    logger.debug("风纪委员检查到重复消息未超过阈值，不做处理，继续巡逻...")
    await fuukiiin.finish()
