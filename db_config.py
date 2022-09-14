import psycopg2
from playhouse.postgres_ext import PostgresqlExtDatabase, Model
from decouple import config


db = PostgresqlExtDatabase(
    config("DB_NAME"),
    user=config("DB_USER"),
    password=config("DB_PASSWORD"),
    host=config("DB_HOST"),
    port=config("DB_PORT"),
    autorollback=True,
)
