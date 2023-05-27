def is_chinese(uchar):
    return "\u4e00" <= uchar <= "\u9fa5"


def is_number(uchar):
    return "\u0030" <= uchar <= "\u0039"


def is_alphabet(uchar):
    return "\u0041" <= uchar <= "\u005a" or "\u0061" <= uchar <= "\u007a"


def is_other_word(uchar):
    return not (is_chinese(uchar) or is_number(uchar) or is_alphabet(uchar))


if __name__ == "__main__":
    str1 = "a一1&"

    assert is_alphabet(str1[0])
    assert is_chinese(str1[1])
    assert is_number(str1[2])
    assert is_other_word(str1[3])
