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


@dataclass
class RepeatRecord:
    message: str
    repeat_count: int


MAX_REPEAT_COUNT = 3

repeated_dict = ExpiringDict(max_len=100, max_age_seconds=20)

fuukiiin = on_message(permission=GROUP_MEMBER | GROUP_ADMIN)


@fuukiiin.handle()
async def repeat_fuukiiin(bot: Bot, event: GroupMessageEvent):
    if event.user_id not in repeated_dict:
        repeated_dict[event.user_id] = RepeatRecord(event.get_plaintext(), 1)
        await fuukiiin.finish()

    if record := repeated_dict.get(event.user_id):
        assert isinstance(record, RepeatRecord)
        if record.message == event.get_plaintext():
            if record.repeat_count >= MAX_REPEAT_COUNT:
                if event.sender.role == GROUP_MEMBER:
                    await bot.set_group_ban(
                        group_id=event.group_id, user_id=event.user_id, duration=60 * 5
                    )
                    await fuukiiin.finish(
                        MessageSegment.at(event.user_id)
                        + f"检测到重复消息{MAX_REPEAT_COUNT}次，已禁言"
                    )
                else:
                    await fuukiiin.finish("检测到管理员发送重复消息，警告")

            repeated_dict[event.user_id].repeat_count += 1  # type: ignore
            await fuukiiin.finish()
