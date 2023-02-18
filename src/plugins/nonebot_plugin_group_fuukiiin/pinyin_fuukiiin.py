from enchant.checker import SpellChecker
from nonebot import on_command, on_message
from nonebot.adapters.onebot.v11 import GROUP_MEMBER, Bot, GroupMessageEvent, Message
from nonebot.log import logger
from nonebot.rule import Rule
from nonebot.typing import T_State

from .config import plugin_config
from .rule_set import group_need_manage, is_long_letters_text, only_specific_member

need_pinyin_fuukiiin = Rule(
    is_long_letters_text, group_need_manage, only_specific_member
)

fuukiiin = on_message(permission=GROUP_MEMBER, rule=need_pinyin_fuukiiin, block=False)


@fuukiiin.handle()
async def pinyin_fuukiiin(bot: Bot, event: GroupMessageEvent, state: T_State):
    logger.debug("pinyin fuukiiin got it!")

    if not (clear_msg := state.get("clear_msg", "")):
        return

    pinyin_checker = SpellChecker("en_US")
    pinyin_checker.set_text(clear_msg)

    for _ in pinyin_checker:
        await fuukiiin.send(
            Message(
                "检测到群成员[CQ:at,qq={}]发送不允许的纯英文字符语句，执行禁言操作".format(event.get_user_id())
            )
        )
        await bot.set_group_ban(
            group_id=event.group_id, user_id=int(event.get_user_id()), duration=300
        )
        break

    if plugin_config.fuuki_pinyin_delete:
        await bot.delete_msg(message_id=event.message_id)


test = on_command("测试PinyinFuuki", group_need_manage)


@test.handle()
async def _():
    await test.finish("检测PinyinFuuki成功！")
