from ast import Str
import random
from typing import Tuple
from captcha.image import ImageCaptcha


def specific_string(length: int) -> Str:
    sample_string = "abcdefmprtvwy"  # define the specific string

    # define the condition for random string
    result = "".join((random.choice(sample_string)) for x in range(length))

    return result


def get_captcha(str: int) -> Tuple:
    captcha_text = specific_string(str)
    image = ImageCaptcha(width=280, height=90)
    data = image.generate(captcha_text)
    return (data, captcha_text)
