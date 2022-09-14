from db_config import db
import peewee
from uuid import uuid4


class BaseModel(peewee.Model):
    class Meta:
        database = db


class airdrop_bot_users(BaseModel):
    uuid = peewee.UUIDField(primary_key=True, default=uuid4)
    id = peewee.BigIntegerField(null=False, unique=True)
    first_name = peewee.TextField(null=False)
    last_name = peewee.TextField(null=True)
    tg_username = peewee.TextField(null=True)
    twitter_username = peewee.TextField(null=True)
    discord_username = peewee.TextField(null=True)
    email = peewee.TextField(null=True)
    referal_counter = peewee.IntegerField(null=False, default=0)
    reffered_by = peewee.BigIntegerField(null=False, default=0)
    platform = peewee.TextField(null=True, default="NOT SELECTED")
    wallet = peewee.TextField(null=True)

    class Meta:
        database = db
