from dataclasses import dataclass

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


@dataclass
class RepeatRecord:
    message: str
    repeat_count: int


MAX_REPEAT_COUNT = 3

repeated_dict = ExpiringDict(max_len=100, max_age_seconds=20)

fuukiiin = on_message(permission=GROUP_MEMBER | GROUP_ADMIN, priority=1)


@fuukiiin.handle()
async def repeat_fuukiiin(bot: Bot, event: GroupMessageEvent):
    logger.debug("单人复读风纪委员巡逻中!")

    stripped_msg = event.get_plaintext().strip()
    if event.user_id not in repeated_dict:
        logger.debug(f"风纪委员检查到{event.user_id}第一次发送消息: {stripped_msg}，记录中...")
        repeated_dict[event.user_id] = RepeatRecord(stripped_msg, 1)
        await fuukiiin.finish()

    if record := repeated_dict.get(event.user_id):
        logger.debug("风纪委员检查到重复消息，检查是否超过最大重复次数...")
        assert isinstance(record, RepeatRecord)
        if record.message == stripped_msg:
            repeated_dict[event.user_id].repeat_count += 1  # type: ignore
            logger.debug(
                f"风纪委员检查到重复消息:{record.message}，重复次数+1，当前重复次数为:{record.repeat_count}次!"
            )
            if record.repeat_count > MAX_REPEAT_COUNT:
                logger.debug(f"风纪委员检查到重复消息超过{MAX_REPEAT_COUNT}次，检查发送者身份...")
                if event.sender.role == GROUP_MEMBER:
                    logger.debug("发送者是群员，处以禁言5分钟，通知发送者")
                    await bot.set_group_ban(
                        group_id=event.group_id, user_id=event.user_id, duration=60 * 5
                    )
                    await fuukiiin.finish(
                        MessageSegment.at(event.user_id)
                        + f"检测到重复消息{MAX_REPEAT_COUNT}次，已禁言"
                    )
                else:
                    logger.debug("发送者是管理员，不处以禁言，仅通知发送者")
                    await fuukiiin.finish("检测到管理员发送重复消息，警告")

            logger.debug("消息重复次数未超过最大重复次数，风纪委员进行下一轮巡逻")
            await fuukiiin.finish()

    logger.debug("风纪委员未检查到重复消息，下一轮巡逻...")
    await fuukiiin.finish()
