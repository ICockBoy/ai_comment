import json

from peewee import *


db = SqliteDatabase('database.db', timeout=10)

class BaseModel(Model):
    class Meta:
        database = db

class Sub(BaseModel):

    # class Meta:
    #     db_table = 'Subs'

    price = IntegerField()
    sub_data_dt_delta_expire = IntegerField()
    sub_data_account_limit = IntegerField()



class User(BaseModel):

    class Meta:
        db_table = 'Users'
    
    user_id = IntegerField()

    balance = FloatField()
    accounts = TextField()

    sub_data_dt_expire = IntegerField()
    sub_data_account_limit = IntegerField()
    referal_id = IntegerField(default=None)

class Comment(BaseModel):

    class Meta:
        db_table = 'Comments'

    owner_id = IntegerField()
    comment_dt = IntegerField()

    channel_id = IntegerField()
    message_id = IntegerField()


if __name__ == "__main__":
    db.create_tables([User, Sub, Comment])