from datetime import datetime, timedelta
from opentele.tl import TelegramClient
from opentele.api import API, UseCurrentSession

from telethon import functions, types
from telethon.events import NewMessage

import asyncio
from kthread import KThread
from telethon.tl.functions.contacts import ResolveUsernameRequest
from telethon.tl.types import InputPeerChat, InputPeerChannel

from config import *
from ai_core import CommentGenerator

from aiogram import Bot, types as bot_types
from config import *
from db_manage import *
import kb
from init_clients import module_clients_api
import random
import dbm


class CommentsAPI:

    def __init__(self):

        self.loop = asyncio.new_event_loop()
        self.comment_generator = CommentGenerator()

        self.thread_loop = KThread(target=self._run_polling)
        self.thread_loop.start()

        self.bot = Bot(
            token=BOT_TOKEN,
            disable_web_page_preview=True,
            parse_mode='html'
        )

        self.min_message_size = 200

        self.clients_owners = {}
        self.clients_ids = {}
        self.clients_phones = {}

        self.cache = dbm.open('comments_cache/comments_cache', 'c')

        self.comments_on_channel = []

    async def _polling_processing(self):
        while True:
            await asyncio.sleep(0.1)

    def _run_polling(self):
        self.loop.run_until_complete(self._polling_processing())

    def _write_comment_cache(self, owner_id: int, channel_id: int, dt: int):

        self.cache[f'{owner_id}|{channel_id}|{dt}'] = '1'

    def _collect_comment(self, owner_id: int, channel_id: int) -> str:

        for key in self.cache.keys():
            if key.decode().startswith(f'{owner_id}|{channel_id}'):
                return key.decode()

    def _is_comment_ready_to_send(self, owner_id: int, channel_id: int) -> bool:

        comment_row = self._collect_comment(owner_id=owner_id, channel_id=channel_id)

        if not comment_row:
            return True

        _, _, dt = comment_row.split('|')
        dt = int(dt)

        now = int(datetime.now().timestamp())

        print(now, dt)

        if now - dt > 86400:
            return True

        else:
            return False

    async def get_clients_by_owner(self, owner_id: int) -> list[TelegramClient]:

        results = []

        for client, client_owner_id in self.clients_owners.items():
            if owner_id == client_owner_id:
                results.append(client)

        return results

    async def is_channel_private(self, channel_link: str) -> bool:
        if '+' in channel_link:
            return True

    async def check_account(self, client):
        try:
            me = await client.get_me()
            if not me:
                account_id = await self._close_client(self.clients_phones[client])
                remove_accounts(
                    user_id=self.clients_owners[client],
                    account_path=module_clients_api.str_sess[account_id]
                )
                await self.bot.send_message(
                    chat_id=self.clients_owners[client],
                    text=f'Аккаунт <b>{self.clients_phones[client]}</b> удален', )
                return False
        except:
            account_id = await self._close_client(self.clients_phones[client])
            remove_accounts(
                user_id=self.clients_owners[client],
                account_path=module_clients_api.str_sess[account_id]
            )
            await self.bot.send_message(
                chat_id=self.clients_owners[client],
                text=f'Аккаунт <b>{self.clients_phones[client]}</b> удален')
            return False
        else:
            return True

    async def leave_channel(self, phone: str, owner_id: int, channel_id: int):

        clients = await self.get_clients_by_owner(owner_id)

        for client in clients:

            if not await self.check_account(client):
                continue
            me = await client.get_me()

            if me.phone == phone:

                channel = [dialog.id async for dialog in client.iter_dialogs(limit=None) if
                           dialog.is_channel == True and dialog.id == channel_id]

                if channel:
                    channel = channel[0]
                    await client.delete_dialog(channel)

                    await self.bot.send_message(
                        chat_id=owner_id,
                        text=f'Аккаунт <b>{me.phone}</b> отписался от канала <b>{channel}</b>'
                    )

                return

    async def get_account_info(self, phone: str, owner_id: int) -> dict:
        clients = await self.get_clients_by_owner(owner_id)
        for client in clients:
            if not await self.check_account(client):
                continue
            me = await client.get_me()
            if me.phone == phone:
                me_full = await client(functions.users.GetFullUserRequest(me))
                username = me.username
                about = me_full.full_user.about
                photo = await client.download_profile_photo(entity='me',
                                                            file=f'temp/{random.randint(0, 9999999999)}.jpg')
                first_name = me.first_name
                last_name = me.last_name
                channels = []
                async for dialog in client.iter_dialogs(limit=None):
                    if dialog.is_channel:
                        channels.append(dialog.name)

                return {
                    "username": username,
                    "about": about,
                    "photo": photo,
                    "first_name": first_name,
                    "last_name": last_name,
                    "channels": channels,
                    "session_file": client.session.save()
                }

    async def get_channels_data(self, phone: str, owner_id: int) -> list[dict]:
        clients = await self.get_clients_by_owner(owner_id)
        for client in clients:
            if not await self.check_account(client):
                continue
            me = await client.get_me()
            if me.phone == phone:
                channels = [{"name": dialog.name, "id": dialog.id} async for dialog in client.iter_dialogs(limit=None)
                            if dialog.is_channel == True]
                return channels

    async def get_accounts_info(self, owner_id: int) -> list[dict]:
        clients = await self.get_clients_by_owner(owner_id)
        results = []
        for client in clients:
            if not await self.check_account(client):
                continue
            me = await client.get_me()
            results.append({
                "phone": me.phone,
                "first_name": me.first_name,
                "last_name": me.last_name
            })
        return results

    async def update_bio(self, phone: str, bio: str, owner_id: int):
        clients = await self.get_clients_by_owner(owner_id)
        for client in clients:
            if not await self.check_account(client):
                return
            me = await client.get_me()
            if me.phone != phone:
                continue
            try:
                await client(functions.account.UpdateProfileRequest(
                    first_name=me.first_name,
                    last_name=me.last_name,
                    about=bio
                ))
                me_full = await client(functions.users.GetFullUserRequest(me))
                await self.bot.send_message(
                    chat_id=owner_id,
                    text=f'Аккаунт <b>{me.phone}</b> обновил описание'
                )
            except Exception as e:
                print(f'Аккаунт {me.phone} не смог обновить описание: {e}')

                await self.bot.send_message(
                    chat_id=owner_id,
                    text=f'Аккаунт <b>{me.phone}</b> не смог обновить описание'
                )

            return

    async def update_last_name(self, phone: str, last_name: str, owner_id: int):

        clients = await self.get_clients_by_owner(owner_id)

        for client in clients:
            if not await self.check_account(client):
                return
            me = await client.get_me()

            if me.phone != phone:
                continue

            try:

                await client(functions.account.UpdateProfileRequest(last_name=last_name))

                await self.bot.send_message(
                    chat_id=owner_id,
                    text=f'Аккаунт <b>{me.phone}</b> обновил Фамилию'
                )

            except Exception as e:

                print(f'Аккаунт {me.phone} не смог обновить фамилию: {e}')

                await self.bot.send_message(
                    chat_id=owner_id,
                    text=f'Аккаунт <b>{me.phone}</b> не смог обновить Фамилию'
                )

            return

    async def update_username(self, phone: str, username: str, owner_id: int):
        clients = await self.get_clients_by_owner(owner_id)
        for client in clients:
            if not await self.check_account(client):
                return
            me = await client.get_me()
            if me.phone != phone:
                continue
            try:
                await client(functions.account.UpdateUsernameRequest(username=username))
                await self.bot.send_message(
                    chat_id=owner_id,
                    text=f'Аккаунт <b>{me.phone}</b> обновил Юзернейм '
                )
            except Exception as e:
                print(f'Аккаунт {me.phone} не смог обновить юзернейм: {e}')
                await self.bot.send_message(
                    chat_id=owner_id,
                    text=f'Аккаунт <b>{me.phone}</b> не смог обновить юзернейм'
                )
            return

    async def update_first_name(self, phone: str, first_name: str, owner_id: int):

        clients = await self.get_clients_by_owner(owner_id)

        for client in clients:
            if not await self.check_account(client):
                return
            me = await client.get_me()
            if me.phone != phone:
                continue

            try:

                await client(functions.account.UpdateProfileRequest(first_name=first_name))

                await self.bot.send_message(
                    chat_id=owner_id,
                    text=f'Аккаунт <b>{me.phone}</b> обновил Имя '
                )

            except Exception as e:

                print(f'Аккаунт {me.phone} не смог обновить имя: {e}')

                await self.bot.send_message(
                    chat_id=owner_id,
                    text=f'Аккаунт <b>{me.phone}</b> не смог обновить Имя'
                )

            return

    async def update_profile_photo(self, phone: str, photo_path: str, owner_id: int):

        clients = await self.get_clients_by_owner(owner_id)

        for client in clients:
            if not await self.check_account(client):
                continue
            me = await client.get_me()
            if me.phone != phone:
                continue

            try:

                file = await client.upload_file(photo_path)
                await client(functions.photos.UploadProfilePhotoRequest(file=file))

                await self.bot.send_message(
                    chat_id=owner_id,
                    text=f'Аккаунт <b>{me.phone}</b> обновил аватарку'
                )

            except Exception as e:

                print(f'Аккаунт {me.phone} не смог обновить аватарку: {e}')

                await self.bot.send_message(
                    chat_id=owner_id,
                    text=f'Аккаунт <b>{me.phone}</b> не смог обновить аватарку'
                )

            return

    async def check_spam_block(self, phone: str, owner_id: int) -> bool:

        clients = await self.get_clients_by_owner(owner_id)

        for client in clients:
            if not await self.check_account(client):
                continue
            me = await client.get_me()
            if me.phone != phone:
                continue

            try:

                await client.send_message('@SpamBot', message='/start')

                await asyncio.sleep(1)

                m = await client.get_messages('@SpamBot', limit=1)
                m = m[0]

                status = True

                if 'свободен от' in m.message or 'no limits' in m.message:
                    status = False

                return status

            except Exception as e:
                print(e)

    async def is_channel_sub_unique(self, owner_id: int, link: str) -> bool:

        clients = await self.get_clients_by_owner(owner_id)
        results = []

        for client in clients:
            channel_data = await client.get_entity(link)
            results.append(channel_data.left)

        return all(results)

    async def join_channels(self, phone: str, channels: list[str], owner_id: int):

        clients = await self.get_clients_by_owner(owner_id)

        for channel in channels:

            for client in clients:
                if not await self.check_account(client):
                    return None
                me = await client.get_me()
                if me.phone != phone:
                    continue

                try:

                    is_private = await self.is_channel_private(channel)

                    if is_private == True:

                        await client(functions.messages.ImportChatInviteRequest(hash=channel.split('+')[-1]))

                    else:

                        status = await self.is_channel_sub_unique(
                            owner_id=owner_id,
                            link=channel
                        )

                        if status:
                            await client(functions.channels.JoinChannelRequest(channel=channel))

                        else:
                            continue

                    await self.bot.send_message(
                        chat_id=owner_id,
                        text=f'Аккаунт <b>{me.phone}</b> подписался на канал <b>{channel}</b>'
                    )

                    await asyncio.sleep(30)

                except Exception as e:

                    print(f'Аккаунт {me.phone} не смог подписаться на канал {channel}: {e}')

                    await self.bot.send_message(
                        chat_id=owner_id,
                        text=f'Аккаунт <b>{me.phone}</b> не смог подписаться на канал <b>{channel}</b>'
                    )

        await self.bot.send_message(
            chat_id=owner_id,
            text=f'Аккаунт <b>{me.phone}</b> подписался на <b>{len(channels)}</b> каналов'
        )

    async def get_channel_uname(self, client: TelegramClient, channel_id: int) -> str:

        try:

            channel = await client.get_entity(channel_id)

            return '@' + channel.username

        except:

            return None

    async def _run_listener(self, client: TelegramClient):

        def get_user_channel_comments():
            try:
                with open("comments_time.json", "r") as f:
                    return json.loads(f.read())
            except:
                return {}

        def get_user_channel_comment_time(chat_id, client_id):
            try:
                user_channel_comments = get_user_channel_comments()
                return datetime.fromisoformat(user_channel_comments[str(chat_id) + str(client_id)])
            except:
                return None

        def set_user_channel_comment_time(chat_id, client_id):
            user_channel_comments = get_user_channel_comments()
            user_channel_comments[str(chat_id) + str(client_id)] = datetime.now().__str__()
            with open("comments_time.json", "w") as f:
                json.dump(user_channel_comments, f)

        @client.on(NewMessage(chats=[777000]))
        async def code_telegram_handler(update: types.UpdateNewMessage):

            allow_filters = [
                not can_user_working(self.clients_owners[client])
            ]

            if any(allow_filters):
                return

            code = ''

            for char in list(update.message.message):

                if char.isdigit():
                    code += char

            if not len(code) == 5:
                return

            me = await client.get_me()

            await self.bot.send_message(
                chat_id=self.clients_owners[client],
                text=f'Код для входа в аккаунт <b>{me.phone}</b>: <code>{code}</code>'
            )

        @client.on(NewMessage())
        async def new_message_handler(update: types.UpdateNewMessage):
            allow_filters = [
                not can_user_working(self.clients_owners[client])
            ]
            if any(allow_filters):
                return
            comment_time = get_user_channel_comment_time(update.message.peer_id.channel_id, self.clients_owners[client])
            if comment_time is not None:
                if datetime.now() - comment_time < timedelta(days=1):
                    return
            filters = [
                not update.message.message is not None,
                not isinstance(update.message.peer_id, types.PeerChannel),
                not update.message.replies is not None
            ]

            if any(filters):
                return

            filters = [
                not update.message.replies.comments is not None and update.message.replies.comments is True
            ]

            if any(filters):
                return

            if self.min_message_size > len(update.message.message):
                return
            api_tokens = get_user_tokens(self.clients_owners[client])
            for _token in api_tokens:
                comment_text = await self.comment_generator.generate_comment(
                    token=_token,
                    post_text=update.message.message
                )
                if comment_text is False:
                    continue
                elif comment_text is not None:
                    break
                else:
                    api_tokens.remove(_token)
            else:
                if len(api_tokens) == 0:
                    try:
                        await self.bot.send_message(
                            chat_id=self.clients_owners[client],
                            text="Закончились токены для ChatGpt, поэтому комментарий не был отправлен, пожалуйста, добавьте новый токен."
                        )
                    except:
                        pass
                set_user_tokens(self.clients_owners[client], api_tokens)
                return
            set_user_tokens(self.clients_owners[client], api_tokens)

            me = await client.get_me()
            try:

                await asyncio.sleep(random.randint(120, 180))

                message_sent = await client.send_message(update.message.peer_id, comment_text,
                                                         comment_to=update.message)
                kb = bot_types.InlineKeyboardMarkup()
                kb.add(
                    bot_types.InlineKeyboardButton(
                        text='🗑 Удалить комментарий',
                        callback_data=f'rcomm|{me.id}|{message_sent.peer_id.channel_id}|{message_sent.id}'
                    )
                )
                kb.add(
                    bot_types.InlineKeyboardButton(
                        text='✏️ Редактировать комментарий',
                        callback_data=f'ecomm|{me.id}|{message_sent.peer_id.channel_id}|{message_sent.id}'
                    )
                )

                channel_uname = await self.get_channel_uname(
                    client=client,
                    channel_id=update.message.peer_id.channel_id
                )

                await self.bot.send_message(
                    chat_id=self.clients_owners[client],
                    text=f'<b>{me.phone} Отправил комментарий в канал {update.message.peer_id.channel_id if not channel_uname else channel_uname}</b>\n\n' + message_sent.message,
                    reply_markup=kb
                )

                self._write_comment_cache(
                    owner_id=self.clients_owners[client],
                    channel_id=update.message.peer_id.channel_id,
                    dt=int(datetime.now().timestamp())
                )
                add_comment(
                    owner_id=self.clients_owners[client],
                    channel_id=update.message.peer_id.channel_id,
                    comment_dt=int(datetime.now().timestamp()),
                    message_id=message_sent.id
                )
                set_user_channel_comment_time(update.message.peer_id.channel_id, self.clients_owners[client])
                print(f'{me.phone} Отправил комментарий в канал {update.message.peer_id.channel_id}')

            except Exception as e:
                print(f'{me.phone} Не смог отправить комментарий: {e}')

        while True:
            await asyncio.sleep(1)

    async def run_comments(self, clients: list[TelegramClient], owner_id: int):

        for client in clients:
            me = await client.get_me()

            self.clients_owners[client] = owner_id
            self.clients_ids[me.id] = client
            self.clients_phones[client] = me.phone
            asyncio.ensure_future(self._run_listener(client), loop=self.loop)

    async def _close_client(self, phone: str) -> int:

        copy_dict = self.clients_owners.copy()

        for client, owner in copy_dict.items():

            client: TelegramClient

            try:

                me = await client.get_me()

                if me.phone == phone:
                    await client.disconnect()
                    del self.clients_owners[client]
                    del self.clients_phones[client]
                    return me.id

            except Exception as e:
                print(e)

    async def remove_comment(self, account_id: int, channel_id: int, message_id: int):

        client: TelegramClient = self.clients_ids[account_id]

        await client.delete_messages(
            entity=channel_id,
            message_ids=[message_id]
        )

    async def edit_comment(self, account_id: int, channel_id: int, message_id: int, new_content: str):
        client: TelegramClient = self.clients_ids[account_id]
        await client.edit_message(
            entity=channel_id,
            message=message_id,
            text=new_content
        )
