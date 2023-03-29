from asyncio import sleep
from typing import Any

from enchant.checker import SpellChecker
from nonebot import on_command, on_message
from nonebot.adapters.onebot.v11 import (
    GROUP_ADMIN,
    GROUP_MEMBER,
    GROUP_OWNER,
    Bot,
    GroupMessageEvent,
    Message,
    MessageSegment,
)
from nonebot.log import logger
from nonebot.params import ArgPlainText
from nonebot.rule import Rule
from nonebot.typing import T_State
from pydantic import BaseModel

from .config import global_config, plugin_config
from .rule_set import group_need_manage, is_long_letters_text, only_specific_member

need_pinyin_fuukiiin = Rule(
    is_long_letters_text, group_need_manage, only_specific_member
)

pinyin_state: dict[Any, Any] = dict()


class BannedMsg(BaseModel):
    user_id: int
    msg: str
    err: str


fuukiiin = on_message(permission=GROUP_MEMBER, rule=need_pinyin_fuukiiin, block=False)


@fuukiiin.handle()
async def pinyin_fuukiiin(bot: Bot, event: GroupMessageEvent, state: T_State):
    logger.debug("pinyin fuukiiin got it!")

    if not (clear_msg := state.get("clear_msg", "")):
        return

    pinyin_checker = SpellChecker("en_US")
    pinyin_checker.set_text(clear_msg)

    for err in pinyin_checker:
        await fuukiiin.send(
            Message(
                "检测到群成员[CQ:at,qq={}]发送不允许的纯英文字符语句\n执行禁言操作并撤回".format(
                    event.get_user_id()
                )
            )
        )

        await bot.set_group_ban(
            group_id=event.group_id, user_id=int(event.get_user_id()), duration=300
        )

        if plugin_config.fuuki_pinyin_delete:
            await sleep(1.5)
            await bot.delete_msg(message_id=event.message_id)

        if global_config.superusers and plugin_config.fuuki_pinyin_delete_feedback:
            feedback_msg = f"bot{bot.self_id} 撤回了 群{event.group_id} 中 成员{event.get_user_id()} 的违禁字符消息：{event.get_plaintext()}"

            # 将撤回的消息存储为全局变量，供其他部分使用
            banned_msg = BannedMsg(
                user_id=event.get_user_id(), msg=event.get_plaintext(), err=err.word
            )
            pinyin_state["deleted_msg"] = banned_msg

            await bot.send_private_msg(
                user_id=int(global_config.superusers.copy().pop()), message=feedback_msg
            )

        break


test = on_command("测试PinyinFuuki", group_need_manage)


@test.handle()
async def _():
    await test.finish("检测PinyinFuuki成功！")


show_deleted_msg = on_command(
    "查看撤回", group_need_manage, permission=GROUP_ADMIN | GROUP_OWNER
)


@show_deleted_msg.handle()
async def msg_show(bot: Bot, event: GroupMessageEvent):
    if deleted_msg := pinyin_state.get("deleted_msg", ""):
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
