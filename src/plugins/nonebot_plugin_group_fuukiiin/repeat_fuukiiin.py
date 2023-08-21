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
    logger.debug("repeat_fuukiiin active!")

    stripped_msg = event.get_plaintext().strip()
    if event.user_id not in repeated_dict:
        logger.debug("repeat_fuukiiin not in repeated_dict! recording...")
        repeated_dict[event.user_id] = RepeatRecord(stripped_msg, 1)
        await fuukiiin.finish()

    if record := repeated_dict.get(event.user_id):
        logger.debug("repeat_fuukiiin in repeated_dict! checking...")
        assert isinstance(record, RepeatRecord)
        if record.message == stripped_msg:
            logger.debug(f"repeat_fuukiiin found repeated message: {record.message}!")
            if record.repeat_count > MAX_REPEAT_COUNT:
                logger.debug(
                    f"repeat_fuukiiin found repeated message {record.message} more than"
                    f" {MAX_REPEAT_COUNT} times!"
                )
                if event.sender.role == GROUP_MEMBER:
                    logger.debug(
                        "sender is GROUP_MEMBER, banning for 5 minutes and notifying"
                    )
                    await bot.set_group_ban(
                        group_id=event.group_id, user_id=event.user_id, duration=60 * 5
                    )
                    await fuukiiin.finish(
                        MessageSegment.at(event.user_id)
                        + f"检测到重复消息{MAX_REPEAT_COUNT}次，已禁言"
                    )
                else:
                    logger.debug("sender is GROUP_ADMIN, notifying only")
                    await fuukiiin.finish("检测到管理员发送重复消息，警告")

            logger.debug("repeat msg not exceed MAX_REPEAT_COUNT, recording...")
            repeated_dict[event.user_id].repeat_count += 1  # type: ignore
            await fuukiiin.finish()

    logger.debug("repeat_fuukiiin not found repeated message, next!")
    await fuukiiin.finish()
