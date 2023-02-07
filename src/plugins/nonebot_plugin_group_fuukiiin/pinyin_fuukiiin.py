import nonebot
from nonebot.adapters.onebot.v11 import GROUP_MEMBER

fuukiiin = nonebot.on_message(permission=GROUP_MEMBER, rule=None)


@fuukiiin.handle()
def pinyin_fuukiiin():
    pass
