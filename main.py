from asyncio.log import logger
import logging
from decouple import config
import string
import telebot
from dotenv import load_dotenv
from aiohttp import web
from telegram import ParseMode
import ssl
from time import time


from msgs.rules import RULES_MESSAGE
from msgs.statistics_message import STATISTIC_MESSAGE
from msgs import captcha_messages, reflink_messages, reg_msgs, welcome_message

import profile_checkers
from generators import get_captcha
from models import airdrop_bot_users

print(logging.__file__)
load_dotenv()

API_TOKEN = config("TELEGRAM_BOT_TOKEN")

WEBHOOK_HOST = config("WEBHOOK_HST")
WEBHOOK_PORT = config("WEBHOOK_PRT")  # 443, 80, 88 or 8443 (port need to be 'open')
WEBHOOK_LISTEN = config(
    "WEBHOOK_LSTN"
)  # In some VPS you may need to put here the IP addr

WEBHOOK_SSL_CERT = "./webhook_cert.pem"  # Path to the ssl certificate
WEBHOOK_SSL_PRIV = "./webhook_pkey.pem"  # Path to the ssl private key

WEBHOOK_URL_BASE = "https://{}:{}".format(WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/{}/".format(API_TOKEN)

AIRDROP_END_DATE = 1660435200
WALLET_END_DATE = 1661385601

logging.basicConfig(
    filename="/home/isaevmik/airdropbot/airdropbotmain.log",
    filemode="a",
    format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
    level=logging.DEBUG,
)

# telebot.logger.basicConfig(
#    filename="/home/isaevmik/airdropbot/airdroptelebot.log",
#    filemode="a",
#    format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
#    datefmt="%H:%M:%S",
#    level=logging.DEBUG,
# )

# logger = telebot.logger
# logger.info("Logger-1 started successfully")

_LOGGER = logging.getLogger(__name__)
_LOGGER.info("Logger-1 started successfully")


CAPTCHA_TRYOUTS = 3

CHANNEL_ID = "@sportybeavers"  # -1001624728707
GROUP_ID = -1001798978836

SUBSCRIBED_ROLES = ["creator", "administrator", "member"]
BAD_ROLES = ["creator", "administrator", "member"]

ADMIN_IDS = []


WINNER_IDS = []

bot = telebot.TeleBot(API_TOKEN, num_threads=4)

app = web.Application()


def change_credentials(message, type: string):
    _LOGGER.info(f"Changing credential {message.text} by {message.from_user.id}")

    isChanged = False

    bot.send_message(message.chat.id, captcha_messages.CHECK_MESSAGE)

    if type == "E-MAIL":
        if profile_checkers.check_email(message.text):

            (
                airdrop_bot_users.update({airdrop_bot_users.email: message.text})
                .where(airdrop_bot_users.id == message.from_user.id)
                .execute()
            )
            isChanged = True

        else:
            mesg = bot.send_message(
                message.chat.id,
                reg_msgs.BAD_EMAIL,
                reply_markup=telebot.types.ReplyKeyboardRemove(),
            )
            bot.register_next_step_handler(mesg, change_credentials, type)

    elif type == "Twitter":
        if profile_checkers.check_twitter(message.text):
            (
                airdrop_bot_users.update(
                    {airdrop_bot_users.twitter_username: message.text}
                )
                .where(airdrop_bot_users.id == message.from_user.id)
                .execute()
            )
            isChanged = True

        else:
            mesg = bot.send_message(
                message.chat.id,
                reg_msgs.BAD_TWITTER_LINK,
                reply_markup=telebot.types.ReplyKeyboardRemove(),
            )
            bot.register_next_step_handler(mesg, change_credentials, type)

    elif type == "Discord":
        if profile_checkers.check_discord(message.text):

            (
                airdrop_bot_users.update(
                    {airdrop_bot_users.discord_username: message.text}
                )
                .where(airdrop_bot_users.id == message.from_user.id)
                .execute()
            )
            isChanged = True

        else:
            mesg = bot.send_message(
                message.chat.id,
                reg_msgs.BAD_DICORD_USERNAME,
                reply_markup=telebot.types.ReplyKeyboardRemove(),
            )

            bot.register_next_step_handler(mesg, change_credentials, type)

    if isChanged:
        keyboard = telebot.types.ReplyKeyboardMarkup(True)
        keyboard.row("Statistics", "Airdrop Rules")

        bot.send_message(
            message.chat.id,
            reg_msgs.SUCCESS_CHANGE,
            reply_markup=keyboard,
        )


def change_credentials_task(message):
    to_change = ""
    if message.text == "E-MAIL":
        to_change = reg_msgs.EMAIL_INFO
    elif message.text == "Twitter":
        to_change = reg_msgs.TWITTER_TASK
    elif message.text == "Discord":
        to_change = reg_msgs.DISCORD_TASK

    mesg = bot.send_message(
        message.chat.id,
        to_change,
        reply_markup=telebot.types.ReplyKeyboardRemove(),
    )
    bot.register_next_step_handler(mesg, change_credentials, message.text)


def airdrop_platform_select(message):
    _LOGGER.info(f"Platform select by {message.from_user.id}")

    if profile_checkers.check_platform(message.text):

        (
            airdrop_bot_users.update({airdrop_bot_users.platform: message.text})
            .where(airdrop_bot_users.id == message.from_user.id)
            .execute()
        )

        keyboard = telebot.types.ReplyKeyboardMarkup(True)
        keyboard.row("Statistics", "Airdrop Rules")

        bot.send_message(
            message.chat.id,
            "Thank you for participation! Wait for you NFT ✅",
            disable_web_page_preview=True,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML,
        )

    else:
        mesg = bot.send_message(message.chat.id, reg_msgs.BAD_PLATFORM)
        bot.register_next_step_handler(mesg, airdrop_platform_select)


def platform_select(message, referee_id):
    _LOGGER.info(f"Platform select by {message.from_user.id}")

    if profile_checkers.check_platform(message.text):

        (
            airdrop_bot_users.update({airdrop_bot_users.platform: message.text})
            .where(airdrop_bot_users.id == message.from_user.id)
            .execute()
        )

        if referee_id and referee_id != message.from_user.id:

            _LOGGER.info(f"Reffering {message.from_user.id}")

            (
                airdrop_bot_users.update(
                    {
                        airdrop_bot_users.referal_counter: airdrop_bot_users.referal_counter
                        + 1
                    }
                )
                .where(airdrop_bot_users.id == referee_id)
                .execute()
            )

            _LOGGER.info(f"Reffered {message.from_user.id}")

            (
                airdrop_bot_users.update({airdrop_bot_users.reffered_by: referee_id})
                .where(airdrop_bot_users.id == message.from_user.id)
                .execute()
            )

            _LOGGER.info(f"Refferee {referee_id} of {message.from_user.id} updated")

        keyboard = telebot.types.ReplyKeyboardMarkup(True)
        keyboard.row("Statistics", "Airdrop Rules")

        bot.send_message(
            message.chat.id,
            reflink_messages.REFLINK_MESSAGE.format(
                message.from_user.first_name, message.from_user.id
            ),
            disable_web_page_preview=True,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML,
        )

    else:
        mesg = bot.send_message(message.chat.id, reg_msgs.BAD_PLATFORM)
        bot.register_next_step_handler(mesg, platform_select, referee_id)


def discord_checker(message, referee_id):
    _LOGGER.info(f"Discord {message.text} by {message.from_user.id}")

    bot.send_message(message.chat.id, captcha_messages.CHECK_MESSAGE)

    if profile_checkers.check_discord(message.text):

        (
            airdrop_bot_users.update(
                {airdrop_bot_users.discord_username: message.text.lower()}
            )
            .where(airdrop_bot_users.id == message.from_user.id)
            .execute()
        )

        keyboard = telebot.types.ReplyKeyboardMarkup(True)
        keyboard.row("iOS", "Android")

        mesg = bot.send_message(
            message.chat.id,
            reg_msgs.PLATFORM_TASK,
            reply_markup=keyboard,
        )

        bot.register_next_step_handler(mesg, platform_select, referee_id)

    else:
        mesg = bot.send_message(message.chat.id, reg_msgs.BAD_DICORD_USERNAME)
        bot.register_next_step_handler(mesg, discord_checker, referee_id)


def twitter_checker(message, referee_id):
    _LOGGER.info(f"Twitter {message.text} by {message.from_user.id}")

    bot.send_message(message.chat.id, captcha_messages.CHECK_MESSAGE)
    if profile_checkers.check_twitter(message.text):

        (
            airdrop_bot_users.update({airdrop_bot_users.twitter_username: message.text})
            .where(airdrop_bot_users.id == message.from_user.id)
            .execute()
        )

        mesg = bot.send_message(
            message.chat.id, reg_msgs.DISCORD_TASK, disable_web_page_preview=True
        )
        bot.register_next_step_handler(mesg, discord_checker, referee_id)

    else:
        mesg = bot.send_message(message.chat.id, reg_msgs.BAD_TWITTER_LINK)
        bot.register_next_step_handler(mesg, twitter_checker, referee_id)


def is_subscribed(id) -> bool:
    try:
        channel_info = bot.get_chat_member(chat_id=CHANNEL_ID, user_id=id)
        group_info = bot.get_chat_member(chat_id=GROUP_ID, user_id=id)
        return (
            channel_info.status in SUBSCRIBED_ROLES
            and group_info.status in SUBSCRIBED_ROLES
        )
    except telebot.apihelper.ApiTelegramException as e:
        if e.result_json["description"] == "Bad Request: user not found":
            return False


def subscription_checker(message, referee_id) -> bool:
    """Function created to check if airdrop_bot_users subscribed to channel and then do next step

    Args:
        message (_type_): _description_
        referee_id (int): if of the person who gave ref link

    Returns:
        bool: True if airdrop_bot_users successfully subscriben, else False
    """

    if message.text == "Done✅":
        bot.send_message(
            message.chat.id,
            captcha_messages.CHECK_MESSAGE,
        )
        if is_subscribed(message.from_user.id):  # check 2nd bot

            mesg = bot.send_message(
                message.chat.id,
                reg_msgs.TWITTER_TASK,
                disable_web_page_preview=True,
                reply_markup=telebot.types.ReplyKeyboardRemove(),
            )
            bot.register_next_step_handler(mesg, twitter_checker, referee_id)

            return True
        else:
            bot.send_message(message.chat.id, reflink_messages.BAD_SUBSCRIPTION)

            mesg = bot.send_message(
                message.chat.id,
                reg_msgs.TG_TASK,
                disable_web_page_preview=True,
            )
            bot.register_next_step_handler(mesg, subscription_checker, referee_id)

            return False

    else:
        mesg = bot.send_message(message.chat.id, reg_msgs.BAD_DONE_BUTTON)
        bot.register_next_step_handler(mesg, subscription_checker, referee_id)


def get_confirmation(message, referee_id):
    if message.text == "Submit Details✅":
        keyboard = telebot.types.ReplyKeyboardMarkup(True)
        keyboard.row("Done✅")

        mesg = bot.send_message(
            message.chat.id,
            reg_msgs.TG_TASK,
            reply_markup=keyboard,
            disable_web_page_preview=True,
        )
        bot.register_next_step_handler(mesg, subscription_checker, referee_id)

    else:
        mesg = bot.send_message(message.chat.id, reg_msgs.BAD_OR_REGULAR_SUBMIT_BUTTON)
        bot.register_next_step_handler(mesg, get_confirmation, referee_id)


def get_email(message, referee_id):
    _LOGGER.info(f"Email {message.text} by {message.from_user.id}")

    bot.send_message(message.chat.id, captcha_messages.CHECK_MESSAGE)

    if profile_checkers.check_email(message.text):

        (
            airdrop_bot_users.update({airdrop_bot_users.email: message.text})
            .where(airdrop_bot_users.id == message.from_user.id)
            .execute()
        )

        keyboard = telebot.types.ReplyKeyboardMarkup(True)
        keyboard.row("Submit Details✅")

        bot.send_message(
            message.chat.id,
            reg_msgs.TASK_MESSAGE,
            parse_mode=ParseMode.HTML,
        )

        mesg = bot.send_message(
            message.chat.id,
            reg_msgs.BAD_OR_REGULAR_SUBMIT_BUTTON,
            reply_markup=keyboard,
            disable_web_page_preview=True,
        )
        bot.register_next_step_handler(mesg, get_confirmation, referee_id)

    else:
        bot.send_message(message.chat.id, reg_msgs.BAD_EMAIL)
        mesg = bot.send_message(message.chat.id, reg_msgs.EMAIL_INFO)
        bot.register_next_step_handler(mesg, get_email, referee_id)


def captcha_checker(message, referee_id, captcha_txt, cnt=0) -> bool:
    _LOGGER.info(f"Captcha {message.text} by {message.from_user.id}")

    bot.send_message(message.chat.id, captcha_messages.CHECK_MESSAGE)

    if message.text.lower() == captcha_txt:
        bot.send_message(message.chat.id, captcha_messages.CAPTCHA_CORRECT)

        airdrop_bot_users.insert(
            {
                airdrop_bot_users.id: message.from_user.id,
                airdrop_bot_users.first_name: message.from_user.first_name,
                airdrop_bot_users.last_name: message.from_user.last_name,
                airdrop_bot_users.tg_username: message.from_user.username,
            }
        ).execute()

        bot.send_message(
            message.chat.id,
            welcome_message.WELCOME_MESSAGE.format(message.from_user.first_name),
            parse_mode=ParseMode.HTML,
        )

        mesg = bot.send_message(message.chat.id, reg_msgs.EMAIL_INFO)

        bot.register_next_step_handler(mesg, get_email, referee_id)
        return True

    else:
        if cnt + 1 > CAPTCHA_TRYOUTS:
            bot.send_message(
                message.chat.id,
                captcha_messages.CAPTCHA_LIMIT,
            )
            _LOGGER.info(f"Captcha Limit by {message.from_user.id}")

            return False

        bot.send_message(message.chat.id, captcha_messages.CAPTCHA_BAD)
        mesg = bot.send_message(message.chat.id, captcha_messages.CAPTCHA_INFO)

        cnt += 1

        bot.register_next_step_handler(
            mesg, captcha_checker, referee_id, captcha_txt, cnt
        )
        return False


def send_captcha(message, referee_id):
    captcha = get_captcha(5)
    bot.send_photo(message.chat.id, captcha[0])
    mesg = bot.send_message(message.chat.id, captcha_messages.CAPTCHA_INFO)
    bot.register_next_step_handler(mesg, captcha_checker, referee_id, captcha[1])


def extract_unique_code(text):
    # Extracts the unique_code from the sent /start command.
    return text.split()[1][3:] if len(text.split()) > 1 else None


def set_wallet(message):

    _LOGGER.info(f"wallet setting by {message.from_user.id}")

    bot.send_message(message.chat.id, captcha_messages.CHECK_MESSAGE)

    (
        airdrop_bot_users.update(
            {
                airdrop_bot_users.wallet: message.text,
            }
        )
        .where(airdrop_bot_users.id == message.from_user.id)
        .execute()
    )

    keyboard = telebot.types.ReplyKeyboardMarkup(True)
    keyboard.row("iOS", "Android")

    mesg = bot.send_message(
        message.chat.id, reg_msgs.PLATFORM_TASK, reply_markup=keyboard
    )
    bot.register_next_step_handler(mesg, airdrop_platform_select)


"""
def is_fraud_subscribed(id) -> bool:
    try:
        channel_info = bot.get_chat_member(chat_id=CHANNEL_ID, user_id=id)
        group_info = bot.get_chat_member(chat_id=GROUP_ID, user_id=id)

        record = airdrop_bot_users.select().where(airdrop_bot_users.id == id)

        if record.exists():
            print(record.get().was_reffered)

        print(
            f"Chananel status = {channel_info.status}",
            f"Group status = {group_info.status}",
            f"Statee = {id}",
        )

        return channel_info.status in BAD_ROLES and group_info.status in BAD_ROLES
    except telebot.apihelper.ApiTelegramException as e:
        if e.result_json["description"] == "Bad Request: airdrop_bot_users not found":
            return False
    """


async def handle(request):
    if request.match_info.get("token") == bot.token:
        request_body_dict = await request.json()

        update = telebot.types.Update.de_json(request_body_dict)
        bot.process_new_updates([update])

        return web.Response()

    else:
        return web.Response(status=403)


app.router.add_post("/{token}/", handle)


@bot.message_handler(commands=["start"])
def start_handler(message):
    _LOGGER.info(f"Start by {message.from_user.id}")

    if (
        airdrop_bot_users.select()
        .where(airdrop_bot_users.id == message.from_user.id)
        .exists()
    ):

        (
            airdrop_bot_users.update(
                {
                    airdrop_bot_users.first_name: message.from_user.first_name,
                    airdrop_bot_users.last_name: message.from_user.last_name,
                    airdrop_bot_users.tg_username: message.from_user.username,
                }
            )
            .where(airdrop_bot_users.id == message.from_user.id)
            .execute()
        )

        record = airdrop_bot_users.get(airdrop_bot_users.id == message.from_user.id)

        keyboard = telebot.types.ReplyKeyboardMarkup(True)
        keyboard.row("Statistics", "Airdrop Rules")

        bot.send_message(
            message.chat.id,
            STATISTIC_MESSAGE.format(
                record.id,
                record.referal_counter,
                record.tg_username,
                record.twitter_username,
                record.discord_username,
            ),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
            reply_markup=keyboard,
        )

    elif time() < AIRDROP_END_DATE:
        unique_code = extract_unique_code(message.text)
        _LOGGER.info(f"Attempting to refer {message.from_user.id} from {unique_code}")

        if unique_code and unique_code.isdigit():

            unique_code = int(unique_code)

        else:
            unique_code = None

        bot.send_message(
            message.chat.id,
            welcome_message.PREREG_MESSAGE,
        )

        """
        if is_fraud_subscribed(message.from_user.id):
            _LOGGER.info(
                f"Froud detection by {message.from_user.id} from {unique_code}"
            )
            unique_code = None
        """

        send_captcha(message, unique_code)


@bot.message_handler(commands=["change"])
def change_credentials_handler(message):

    _LOGGER.info(f"Attempting to change credentials by {message.from_user.id}")

    if (
        airdrop_bot_users.select()
        .where(airdrop_bot_users.id == message.from_user.id)
        .exists()
    ) and time() < AIRDROP_END_DATE:

        keyboard = telebot.types.ReplyKeyboardMarkup(True)
        keyboard.row("E-MAIL", "Twitter", "Discord")

        mesg = bot.send_message(
            message.chat.id, reg_msgs.CHANGE_TASK, reply_markup=keyboard
        )

        bot.register_next_step_handler(mesg, change_credentials_task)


@bot.message_handler(commands=["setwallet"])
def change_credentials_handler(message):
    if time() < WALLET_END_DATE:
        if message.from_user.id in WINNER_IDS:
            _LOGGER.info(f"Setting wallet by {message.from_user.id}")
            if (
                airdrop_bot_users.select()
                .where(airdrop_bot_users.id == message.from_user.id)
                .exists()
            ):

                mesg = bot.send_message(message.chat.id, reg_msgs.WALLET_MESSAGE)

                bot.register_next_step_handler(mesg, set_wallet)

        else:
            _LOGGER.info(f"Wrong winner id wallet by {message.from_user.id}")
            bot.send_message(message.chat.id, "You are not winner")

    else:
        bot.send_message(message.chat.id, "Too Late")


@bot.message_handler(commands=["ban"])
def ban_handler(message):

    cur_user_id = message.from_user.id
    _LOGGER.info(f"Attempting to use ban command  by {cur_user_id}")

    if cur_user_id in ADMIN_IDS:
        # keyboard = telebot.types.ReplyKeyboardMarkup(True)
        # keyboard.row("Single", "List")

        # mesg = bot.send_message(message.chat.id, "Ban option", reply_markup=keyboard)
        ban_list = message.text.split()

        for ban_id in ban_list:

            if ban_id.isdigit() and ban_id not in ADMIN_IDS:

                bot.send_message(int(ban_id), reg_msgs.BAN_MESSAGE)

                _LOGGER.info(f"Ban message sent for {cur_user_id}")

                isBannedGroup = bot.ban_chat_member(GROUP_ID, ban_id)
                isBannedChannel = bot.ban_chat_member(CHANNEL_ID, ban_id)

                _LOGGER.info(
                    f"Status of ban in group and channel for{cur_user_id} is {isBannedGroup} and {isBannedChannel}"
                )

                to_delete = airdrop_bot_users.get_or_none(
                    airdrop_bot_users.id == ban_id
                )

                if to_delete:

                    _LOGGER.info(
                        f"finded recored to ban for: {to_delete.uuid}, {to_delete.id}, {to_delete.first_name}, {to_delete.last_name}, {to_delete.tg_username}, {to_delete.twitter_username}, {to_delete.discord_username}, {to_delete.email}, {to_delete.referal_counter}, {to_delete. reffered_by}, {to_delete.platform}"
                    )

                    deleted_amount = to_delete.delete_instance()

                    _LOGGER.info(f"Total record (ban) deleted = {deleted_amount}")
                    _LOGGER.info(f"{ban_id} is banned and deleted")

                    bot.send_message(
                        message.chat.id,
                        f"{ban_id}, {isBannedGroup}, {isBannedChannel}, {deleted_amount}",
                    )

                else:
                    _LOGGER.info(f"No matches for {ban_id}")
                    bot.send_message(message.chat.id, f"No matches for {ban_id}")

        bot.send_message(message.chat.id, "Ban session done")

    else:
        bot.send_message(
            message.chat.id, "Failure attemption, be prepared for kinky punishment"
        )


@bot.message_handler(commands=["win"])
def ban_handler(message):
    cur_user_id = message.from_user.id
    _LOGGER.info(f"Attempting to use win command  by {cur_user_id}")

    if cur_user_id in ADMIN_IDS:
        win_list = message.text.split()
        for win_id in win_list:

            if win_id.isdigit() and win_id not in ADMIN_IDS:

                bot.send_message(int(win_id), reg_msgs.WALLET_MSG)

                bot.send_message(cur_user_id, f"ok for {win_id}")


"""
@bot.message_handler(commands=["stop"])
def stop_handler(message):
    if (
        airdrop_bot_users.select()
        .where(airdrop_bot_users.id == message.from_user.id)
        .exists()
    ):

        bot.send_message(
            message.chat.id,
            f"Hope to see you again, {message.from_user.first_name}!",
            reply_markup=telebot.types.ReplyKeyboardRemove(),
        )

        airdrop_bot_users.delete().where(
            airdrop_bot_users.id == message.from_user.id
        ).execute()

    else:
        bot.send_message(
            message.chat.id,
            f"You are not registered, {message.from_user.first_name}!",
        )
"""


@bot.message_handler(func=lambda message: True)
def text_handler(message):

    if message.text == "Airdrop Rules":
        bot.send_message(message.chat.id, RULES_MESSAGE, parse_mode=ParseMode.HTML)

    if message.text == "Statistics" and (
        airdrop_bot_users.select()
        .where(airdrop_bot_users.id == message.from_user.id)
        .exists()
    ):
        record = airdrop_bot_users.get(airdrop_bot_users.id == message.from_user.id)

        bot.send_message(
            message.chat.id,
            STATISTIC_MESSAGE.format(
                record.id,
                record.referal_counter,
                record.tg_username,
                record.twitter_username,
                record.discord_username,
            ),
            parse_mode=ParseMode.HTML,
        )

    # else:
    #    bot.send_message(message.chat.id, reg_msgs.BAD_REGISTRATION)


# Enable saving next step handlers to file "./.handlers-saves/step.save".
# Delay=2 means that after any change in next step handlers (e.g. calling register_next_step_handler())
# saving will hapen after delay 2 seconds.
bot.enable_save_next_step_handlers(delay=2)

# Load next_step_handlers from save file (default "./.handlers-saves/step.save")
# WARNING It will work only if enable_save_next_step_handlers was called!
bot.load_next_step_handlers()

# Remove webhook, it fails sometimes the set if there is a previous webhook
bot.remove_webhook()

# Set webhook
bot.set_webhook(
    url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH, certificate=open(WEBHOOK_SSL_CERT, "r")
)

# Build ssl context
context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
context.load_cert_chain(WEBHOOK_SSL_CERT, WEBHOOK_SSL_PRIV)

# Start aiohttp server
web.run_app(
    app,
    host=WEBHOOK_LISTEN,
    port=WEBHOOK_PORT,
    ssl_context=context,
)
