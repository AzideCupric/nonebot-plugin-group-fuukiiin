from nonebot.adapters.onebot.v11 import Event


async def is_all_letters(event: Event):
    msg = event.get_plaintext()
    if msg.replace(" ", "").isalpha():
        return True

    return False
