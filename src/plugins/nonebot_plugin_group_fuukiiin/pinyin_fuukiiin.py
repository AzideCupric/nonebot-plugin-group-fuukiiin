from asyncio import sleep
from typing import Any

from enchant.checker import SpellChecker
from nonebot import on_command, on_message
from nonebot.adapters.onebot.v11 import (
    GROUP_ADMIN,
    GROUP_MEMBER,
    GROUP_OWNER,
    Bot,
    Event,
    GroupMessageEvent,
    MessageSegment,
    PokeNotifyEvent,
)
from nonebot.log import logger
from nonebot.params import ArgPlainText, Depends
from nonebot.rule import Rule
from nonebot.typing import T_State
from pydantic import BaseModel

from .config import global_config, plugin_config
from .rule_set import group_need_manage, is_long_letters_text, only_targeted_member

need_pinyin_fuukiiin = Rule(
    is_long_letters_text, group_need_manage, only_targeted_member
)

pinyin_state: dict[Any, Any] = {}


class BannedMsg(BaseModel):
    user_id: int
    msg: str
    err: str


fuukiiin = on_message(permission=GROUP_MEMBER, rule=need_pinyin_fuukiiin, block=False)


@fuukiiin.handle()
async def pinyin_fuukiiin(event: GroupMessageEvent, state: T_State):
    logger.debug("pinyin fuukiiin got it!")

    clear_msg = state.get("clear_msg", "")
    if not clear_msg:
        return

    pinyin_checker = SpellChecker("en_US")
    pinyin_checker.set_text(clear_msg)

    err = next(iter(pinyin_checker), None)

    if not err:
        await fuukiiin.finish()

    await fuukiiin.send(
        MessageSegment.text(
            f"检测到群成员 {event.get_user_id()} 发送不正确的单词: {err.word} ...\n使用戳一戳确认撤回该消息"
        )
    )

    state["confirm"] = {
        "user_id": event.get_user_id(),
        "group_id": event.group_id,
        "message_id": event.message_id,
        "message": event.get_plaintext(),
        "err_word": err.word,
    }


async def _is_need_confirm(state: T_State) -> bool:
    return bool(state.get("confirm"))


@fuukiiin.got("pokepoke", "请戳一戳", [Depends(_is_need_confirm)])
async def pinyin_fuukiiin_poke(bot: Bot, event: Event, state: T_State):
    logger.debug("pinyin fuukiiin got poke!")

    if not isinstance(event, PokeNotifyEvent):
        await fuukiiin.reject()

    if not event.is_tome():
        await fuukiiin.reject()

    group_id = state["confirm"]["group_id"]
    user_id = state["confirm"]["user_id"]
    message_id = state["confirm"]["message_id"]
    message = state["confirm"]["message"]
    err = state["confirm"]["err_word"]

    # 权限确认
    if await GROUP_ADMIN(bot, event) or await GROUP_OWNER(bot, event):
        await bot.set_group_ban(group_id=group_id, user_id=int(user_id), duration=300)

        if plugin_config.fuuki_pinyin_delete:
            await sleep(1.5)
            await bot.delete_msg(message_id=message_id)

        if global_config.superusers and plugin_config.fuuki_pinyin_delete_feedback:
            feedback_msg = (
                f"bot{bot.self_id} 撤回了 群{group_id} 中 成员{user_id} 的违禁字符消息：{message}"
            )
            # 将撤回的消息存储为全局变量，供其他部分使用
            banned_msg = BannedMsg(user_id=user_id, msg=message, err=err)
            pinyin_state["deleted_msg"] = banned_msg

            await bot.send_private_msg(
                user_id=int(global_config.superusers.copy().pop()), message=feedback_msg
            )

    else:
        # 记录可能的恶意戳一戳
        if state["spite_poke"][event.get_user_id()]:
            state["spite_poke"][event.get_user_id()] += 1
        else:
            state["spite_poke"][event.get_user_id()] = 1
        if state["spite_poke"][event.get_user_id()] > 2:
            await bot.set_group_ban(
                group_id=group_id, user_id=int(user_id), duration=300
            )

            del state["spite_poke"][event.get_user_id()]

            await fuukiiin.finish("恶意，你也闭嘴")
        else:
            await fuukiiin.reject("权限不足，下一个")


test = on_command("测试Pinyin", group_need_manage)


@test.handle()
async def _():
    await test.finish("检测PinyinFuuki成功！")


show_deleted_msg = on_command(
    "查看撤回", group_need_manage, permission=GROUP_ADMIN | GROUP_OWNER
)


@show_deleted_msg.handle()
async def msg_show(event: GroupMessageEvent):
    if deleted_msg := pinyin_state.get("deleted_msg"):
        assert isinstance(deleted_msg, BannedMsg)
        msg = (
            MessageSegment.text("上次撤回的消息>>\n")
            + MessageSegment.at(deleted_msg.user_id)
            + MessageSegment.text(f": {deleted_msg.msg}\n")
            + MessageSegment.text(f"错误词汇：{deleted_msg.err}\n")
            + MessageSegment.text("使用`加入词典`命令将该词汇加入词典")
        )
        await show_deleted_msg.send(msg)
    else:
        await show_deleted_msg.finish("上次没有撤回消息")


# 检测到回复加入词典命令时，将撤回的消息加入词典
@show_deleted_msg.got("is_need_add")
async def add_to_dict(
    bot: Bot, event: GroupMessageEvent, is_need_add: str = ArgPlainText()
):
    if is_need_add == "加入词典" and (deleted_msg := pinyin_state.get("deleted_msg", "")):
        assert isinstance(deleted_msg, BannedMsg)
        pinyin_checker = SpellChecker("en_US")
        pinyin_checker.add(deleted_msg.err)
        await show_deleted_msg.finish(f"已将{deleted_msg.err}加入词典")
