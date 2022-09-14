from re import fullmatch

EMAIL_REGEX = r"^([^\x00-\x20\x22\x28\x29\x2c\x2e\x3a-\x3c\x3e\x40\x5b-\x5d\x7f-\xff]+|\x22([^\x0d\x22\x5c\x80-\xff]|\x5c[\x00-\x7f])*\x22)(\x2e([^\x00-\x20\x22\x28\x29\x2c\x2e\x3a-\x3c\x3e\x40\x5b-\x5d\x7f-\xff]+|\x22([^\x0d\x22\x5c\x80-\xff]|\x5c[\x00-\x7f])*\x22))*\x40([^\x00-\x20\x22\x28\x29\x2c\x2e\x3a-\x3c\x3e\x40\x5b-\x5d\x7f-\xff]+|\x5b([^\x0d\x5b-\x5d\x80-\xff]|\x5c[\x00-\x7f])*\x5d)(\x2e([^\x00-\x20\x22\x28\x29\x2c\x2e\x3a-\x3c\x3e\x40\x5b-\x5d\x7f-\xff]+|\x5b([^\x0d\x5b-\x5d\x80-\xff]|\x5c[\x00-\x7f])*\x5d))*$"

TWITTER_LINK_REGEX = r"^@?(\w){1,15}$"

DISCORD_REGEX = r"^.{3,32}#[0-9]{4}$"


def check_email(email) -> bool:
    return True if fullmatch(EMAIL_REGEX, email) else False


def check_twitter(link) -> bool:
    return True if fullmatch(TWITTER_LINK_REGEX, link) else False


def check_discord(username) -> bool:
    return True if fullmatch(DISCORD_REGEX, username) else False


def check_platform(txt) -> bool:

    txt = txt.lower()

    return txt == "ios" or txt == "android"
