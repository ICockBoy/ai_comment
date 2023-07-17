import asyncio

from models import *

import json
from datetime import datetime


def create_user_if_not_exist(user_id: int, referal_id: int = 'default_value'):

    if User.select().where(User.user_id == user_id).exists():
        return
    
    User.create(
        user_id=user_id,
        balance=0,
        accounts=json.dumps({
            "td": [],
            "tl": []
        }),
        sub_data_dt_expire=0,
        sub_data_account_limit=0,
        referal_id=referal_id
    )


def get_users_tokens():
    try:
        with open("tokens.json", "r") as f:
            return json.loads(f.read())
    except:
        return {}


def get_user_tokens(user_id):
    try:
        user_tokens = get_users_tokens()
        return user_tokens[str(user_id)]
    except:
        return []


def set_user_tokens(user_id, tokens: list[str]):
    user_tokens = get_users_tokens()
    user_tokens[str(user_id)] = tokens
    with open("tokens.json", "w") as f:
        json.dump(user_tokens, f)


def get_all_users() -> list[dict]:

    results = []

    for user in User.select():

        results.append({
            "user_id": user.user_id,
            "balance": user.balance,
            "accounts": json.loads(user.accounts),
            "sub_data_dt_expire": user.sub_data_dt_expire,
            "sub_data_account_limit": user.sub_data_account_limit,
            "referal_id": user.referal_id
        })
    
    return results

def get_user(user_id: int) -> dict:

    for user in get_all_users():
        if user["user_id"] == user_id:
            return user

def create_sub(price: int, sub_data_dt_delta_expire: int, sub_data_account_limit: int):

    Sub.create(
        price=price,
        sub_data_dt_delta_expire=sub_data_dt_delta_expire,
        sub_data_account_limit=sub_data_account_limit
    )

def get_all_subs() -> list[dict]:

    results = []

    for sub in Sub.select():
        results.append({
            "id": sub.id,
            "price": sub.price,
            "sub_data_dt_delta_expire": sub.sub_data_dt_delta_expire,
            "sub_data_account_limit": sub.sub_data_account_limit
        })
    
    return results

def get_sub_by_id(sub_id: int) -> dict:

    for sub in get_all_subs():
        if sub["id"] == sub_id:
            return sub

def update_user_sub(user_id: int, sub_data_dt_expire: int, sub_data_account_limit: int):

    User.update(sub_data_dt_expire=sub_data_dt_expire).where(User.user_id == user_id).execute()
    User.update(sub_data_account_limit=sub_data_account_limit).where(User.user_id == user_id).execute()

def can_user_working(user_id: int) -> bool:

    user_data = get_user(user_id)

    if user_data["sub_data_dt_expire"] < int(datetime.now().timestamp()):
        return False
    
    return True

def update_user_balance(user_id: int, value: float):

    user_data = get_user(user_id)

    User.update(balance=user_data["balance"] + value).where(User.user_id == user_id).execute()


    try:

        if value > 0 and user_data['referal_id'] != 'default_value' and user_data:
            
            bonus_value = value / 100
            bonus_value = bonus_value * 10

            referal_data = get_user(user_data['referal_id'])

            User.update(balance=referal_data["balance"] + value).where(User.user_id == user_data['referal_id']).execute()

            return {"referal_id": user_data['referal_id'], "value": value}
    
    except Exception as e:
        print('Ошибка при пополнении баланса реферала: ' + str(e))

def update_user_accounts(user_id: int, accounts: list[str], account_type: str):

    user_data = get_user(user_id)

    old_with_new = user_data["accounts"]

    for account in accounts:

        if not account.endswith('.session'):
            continue

        if user_data["sub_data_account_limit"] <= len(old_with_new[f"{'tl' if account_type == 'session' else 'td'}"]):
            break

        old_with_new[f"{'tl' if account_type == 'session' else 'td'}"].append(account)

    User.update(accounts=json.dumps(user_data["accounts"])).where(User.user_id == user_data["user_id"]).execute()

def old_remove_accounts(user_id: int):
    User.update(accounts=json.dumps({"td": [], "tl": []})).where(User.user_id == user_id).execute()

def remove_accounts(user_id: int, account_path: str):

    user_data = get_user(user_id)

    if "td" in account_path:
        user_data["accounts"]["td"].remove(account_path)
    
    elif "tl" in account_path:
        user_data["accounts"]["tl"].remove(account_path)
    
    User.update(accounts=json.dumps(user_data["accounts"])).where(User.user_id == user_data["user_id"]).execute()

def is_user_balance_enough(user_id: int, value: float) -> bool:

    user_data = get_user(user_id)

    if user_data["balance"] >= value:
        return True
    
    return False

def can_user_add_accounts(user_id: int) -> bool:

    user_data = get_user(user_id)

    if user_data["sub_data_account_limit"] <= len(user_data["accounts"]["td"]) or user_data["sub_data_account_limit"] <= len(user_data["accounts"]["tl"]):
        return False

    return True

def add_comment(owner_id: int, comment_dt: int, channel_id: int, message_id: int):

    if Comment.select().where(Comment.owner_id == owner_id, Comment.channel_id == channel_id).exists():

        Comment.update(comment_dt=comment_dt, message_id=message_id).where(Comment.owner_id == owner_id, Comment.channel_id == channel_id).execute()

    else:

        Comment.create(
            owner_id=owner_id,
            comment_dt=comment_dt,
            channel_id=channel_id,
            message_id=message_id
        )


async def is_comment_allow(owner_id: int, channel_id: int) -> bool:
    return True
    # if Comment.select().where(Comment.owner_id == owner_id, Comment.channel_id == channel_id).exists():
    #
    #     q = Comment.select().where(Comment.owner_id == owner_id, Comment.channel_id == channel_id)
    #
    #     comment_dt = q[0].comment_dt
    #     now = int(datetime.now())
    #
    #     if now - comment_dt < 4000:
    #         await asyncio.sleep(8640 - now - comment_dt)
    #         return True
    #
    #     else:
    #         return True
    #
    # else:
    #
    #     return True

if __name__ == "__main__":

    users = get_all_users()

    for user in users:
        update_user_balance(user["user_id"], 100.0)

    # d = get_user(
    #     631172274
    # )

    # print(d)

    # create_sub(
    #     price=200,
    #     sub_data_dt_delta_expire=86400 * 14,
    #     sub_data_account_limit=5
    # )

    # create_sub(
    #     price=350,
    #     sub_data_dt_delta_expire=86400 * 30,
    #     sub_data_account_limit=5
    # )

    # create_sub(
    #     price=400,
    #     sub_data_dt_delta_expire=86400 * 14,
    #     sub_data_account_limit=10
    # )

    # create_sub(
    #     price=650,
    #     sub_data_dt_delta_expire=86400 * 30,
    #     sub_data_account_limit=10
    # )

    # create_sub(
    #     price=1000,
    #     sub_data_dt_delta_expire=86400 * 14,
    #     sub_data_account_limit=30
    # )

    # create_sub(
    #     price=1500,
    #     sub_data_dt_delta_expire=86400 * 30,
    #     sub_data_account_limit=30
    # )


    # update_user_sub(
    #     user_id=631172274,
    #     sub_data_dt_expire=int(datetime.now().timestamp()) + 86400 * 30,
    #     sub_data_account_limit=1000
    # )