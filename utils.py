from datetime import datetime
import os
import shutil
import zipfile
import rarfile
import asyncio

from db_manage import *

from clients_api import ClientsAPI
from comments_api import CommentsAPI

from payments import Payments


module_clients_api = ClientsAPI()
module_comments_api = CommentsAPI()
payments_api = Payments()


async def create_payment(amount: float, user_id: int) -> dict:

    payment_data = await payments_api.create_payment(
        amount=amount,
        user_id=user_id
    )

    return payment_data

async def close_client(phone: str, owner_id: int):

    account_id = await module_comments_api._close_client(
        phone=phone
    )

    remove_accounts(
        user_id=owner_id,
        account_path=module_clients_api.str_sess[account_id]
    )

async def check_payment(bill_id: str) -> bool:

    status = await payments_api.check_payment(bill_id)

    return status

async def code_auth_sign_in_step(phone: str, code: str, owner_id: int):

    session_file_data = await module_clients_api.code_auth_sign_in_step(
        phone=phone,
        code=code,
        owner_id=owner_id
    )

    return session_file_data

async def code_auth_sign_in_2fa_step(phone: str, code: str, owner_id: int, password: str):

    session_file_data = await module_clients_api.code_auth_sign_in_2fa_step(
        phone=phone,
        code=code,
        owner_id=owner_id,
        password=password
    )

    return session_file_data

async def code_auth_send_code_step(phone: str, owner_id: int):

    await module_clients_api.code_auth_send_code_step(
        phone=phone,
        owner_id=owner_id
    )

async def get_channels_data(phone: str, owner_id: int) -> list[dict]:

    r = await module_comments_api.get_channels_data(
        phone=phone,
        owner_id=owner_id
    )

    return r

async def check_spam_block(phone: str, owner_id: int) -> bool:

    status = await module_comments_api.check_spam_block(
        phone=phone,
        owner_id=owner_id
    )

    return status

async def leave_channel(phone: str, owner_id: int, channel_id: int):

    await module_comments_api.leave_channel(
        phone=phone,
        owner_id=owner_id,
        channel_id=channel_id
    )

async def join_channels(phone: str, channels: list[str], owner_id: int):

    await module_comments_api.join_channels(
        phone=phone,
        channels=channels,
        owner_id=owner_id
    )

async def update_profile_photo(phone: str, photo_path: str, owner_id: int):

    await module_comments_api.update_profile_photo(
        phone=phone,
        photo_path=photo_path,
        owner_id=owner_id
    )
async def update_username(phone: str, username: str, owner_id: int):

    await module_comments_api.update_username(
        phone=phone,
        username=username,
        owner_id=owner_id
    )

async def update_first_name(phone: str, first_name: str, owner_id: int):

    await module_comments_api.update_first_name(
        phone=phone,
        first_name=first_name,
        owner_id=owner_id
    )

async def update_last_name(phone: str, last_name: str, owner_id: int):

    await module_comments_api.update_last_name(
        phone=phone,
        last_name=last_name,
        owner_id=owner_id
    )  

async def update_bio(phone: str, bio: str, owner_id: int):

    await module_comments_api.update_bio(
        phone=phone,
        bio=bio,
        owner_id=owner_id
    )

async def get_account_info(phone: str, owner_id: int) -> dict:

    result = await module_comments_api.get_account_info(
        phone=phone,
        owner_id=owner_id
    )

    return result

async def get_accounts_info(owner_id: int) -> list[dict]:

    results = await module_comments_api.get_accounts_info(
        owner_id=owner_id
    )

    return results

async def remove_comment(account_id: int, channel_id: int, message_id: int):
    await module_comments_api.remove_comment(account_id, channel_id, message_id)

async def edit_comment(account_id: int, channel_id: int, message_id: int, new_content: str):
    await module_comments_api.edit_comment(
        account_id=account_id,
        channel_id=channel_id,
        message_id=message_id,
        new_content=new_content
    )

async def remove_account(account_path: str, owner_id: int):

    remove_accounts(
        user_id=owner_id,
        account_path=account_path
    )


    try:

        shutil.rmtree(account_path)
    
    except:
        
        os.remove(account_path)

async def split_run_task(accounts: list[str], type: str, owner_id: int):

    if type == 'tdata':

        # sessions = await module_clients_api.fetch_clients_from_tdatas(
        #     tdatas=accounts,
        #     owner_id=owner_id
        # )
        return
    
    elif type == 'session':

        sessions = await module_clients_api.fetch_clients_from_sessions(
            sessions=accounts,
            owner_id=owner_id
        )

    await module_comments_api.run_comments(
        clients=sessions,
        owner_id=owner_id
    )

async def _run_user_task(user: dict):

    all_clients = []
    
    sessions_tl = await module_clients_api.fetch_clients_from_sessions(
        sessions=user["accounts"]["tl"],
        owner_id=user['user_id']
    )

    # sessions_td = await module_clients_api.fetch_clients_from_tdatas(
    #     tdatas=user["accounts"]["td"],
    #     owner_id=user['user_id']
    # )

    all_clients.extend(sessions_tl)
    # all_clients.extend(sessions_td)

    await module_comments_api.run_comments(
        clients=all_clients,
        owner_id=user["user_id"]
    )

async def run_user_tasks(users: list[dict]):

    for user in users:

        try:

            filters = [
                not can_user_working(user["user_id"])
            ]

            if any(filters):
                continue

            await _run_user_task(user)
        
        except Exception as e:
            print(f'Ошибка при запуске задача пользователя: {e}')
    
    print('Загружены все аккаунты пользователей!')

def convert_timestamp_to_dt(seconds: int) -> datetime:
    return datetime.fromtimestamp(seconds)

def add_keys(keys: list[str]):

    for key in keys:

        with open('OPENAI_KEYS', 'a', encoding='utf-8') as f:
            f.write(key + '\n')

def dump_accounts(file_paths: list[str], zip_path: str) -> str:
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:

        for file_path in file_paths:

            file_name = os.path.basename(file_path)

            zip_file.write(file_path, file_name)

    return zip_path

def unpack_archive(archive_path: str, dest_folder: str) -> list[str]:

    extracted_files = []

    if zipfile.is_zipfile(archive_path):

        with zipfile.ZipFile(archive_path, 'r') as zip_ref:

            for file_info in zip_ref.infolist():

                file_path = os.path.join(dest_folder, file_info.filename).replace("\\", "/")
                zip_ref.extract(file_info.filename, dest_folder)

                if 'td' in file_path:

                    filters = [
                        'tdata' not in file_path,
                        not file_path.endswith('tdata/')
                    ]

                    if any(filters):
                        continue

                    extracted_files.append(file_path)
                
                else:
                    extracted_files.append(file_path)

    elif rarfile.is_rarfile(archive_path):

        with rarfile.RarFile(archive_path, 'r') as rar_ref:

            for file_info in rar_ref.infolist():

                file_path = os.path.join(dest_folder, file_info.filename).replace("\\", "/")
                rar_ref.extract(file_info.filename, dest_folder)

                if 'td' in file_path:

                    filters = [
                        'tdata' not in file_path,
                        not file_path.endswith('tdata')
                    ]

                    if any(filters):
                        continue

                    extracted_files.append(file_path)
                
                else:

                    extracted_files.append(file_path)
    else:
        raise ValueError(f"{archive_path} не является допустимым архивом.")
    
    return extracted_files