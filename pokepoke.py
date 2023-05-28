from copy import deepcopy
from typing import Annotated

from nonebot import on_command, on_message
from nonebot.adapters.onebot.v11 import (
    Bot,
    GroupMessageEvent,
    Message,
    MessageSegment,
    PokeNotifyEvent,
)
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.params import Depends
from nonebot.permission import USER, Permission
from nonebot.rule import Rule
from nonebot.typing import T_State


async def _is_managed_group(event: GroupMessageEvent) -> bool:
    return event.group_id in [int("240586981"), int("606489218")]


async def _is_respond_member(event: GroupMessageEvent) -> bool:
    return event.get_user_id() in ["1836954163", "1012293637"]


scope_rule = Rule(_is_managed_group, _is_respond_member)

fk = on_message(rule=scope_rule)


async def _is_start_with_test(
    event: GroupMessageEvent, matcher: Matcher
) -> GroupMessageEvent:
    if event.get_plaintext().startswith("test"):
        return event

    await matcher.finish()


async def _is_poke_bot(event: PokeNotifyEvent):
    if not event.is_tome():
        await fk.reject("戳错了！")

    return event


@fk.handle()
async def target_test(
    event: Annotated[GroupMessageEvent, Depends(_is_start_with_test)], state: T_State
):
    await fk.send("检测到test信息！")
    state["del_msg_id"] = event.message_id
    logger.debug(f"now state:{state}")
    await fk.pause("请戳一戳确认撤回该消息")


@fk.type_updater
async def update_to_notice() -> str:
    return "notice"


@fk.permission_updater
async def update_to_multi_user(
    bot: Bot, event: GroupMessageEvent, matcher: Matcher
) -> Permission:
    group_id = event.group_id
    session_id_str = f"group_{group_id}"
    group_members = filter(
        lambda x: x["role"] != "member",
        await bot.get_group_member_list(group_id=group_id),
    )
    admin_names = "\n".join(
        map(lambda x: str(x["user_id"]) + ":" + x["nickname"], deepcopy(group_members))
    )
    logger.debug(f"now group_members:\n{admin_names}")
    session_ids = map(lambda x: f'{session_id_str}_{x["user_id"]}', group_members)
    return USER(*session_ids, perm=matcher.permission)


@fk.handle()
async def get_poke(
    bot: Bot, event: Annotated[PokeNotifyEvent, Depends(_is_poke_bot)], state: T_State
):
    logger.debug(f"now state:{state}")
    await fk.send("撤回中...")
    await bot.delete_msg(message_id=state["del_msg_id"])
