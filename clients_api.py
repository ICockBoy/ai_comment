from opentele.tl import TelegramClient
from opentele.td import TDesktop
from opentele.api import API, UseCurrentSession

from telethon.errors.rpcerrorlist import UserDeactivatedError, AuthKeyDuplicatedError, PasswordHashInvalidError, SessionPasswordNeededError
from sqlite3 import OperationalError

from telethon import functions, types
from telethon.sessions import StringSession

import asyncio
from kthread import KThread

import os
import shutil

from aiogram import Bot, types as bot_types

import random
from config import *
from db_manage import *


class ClientsAPI:

    def __init__(self):

        # self.proxy = {
        #     "proxy_type": "socks5",
        #     "addr": "127.0.0.1",
        #     "port": 9050,
        #     "rdns": True
        # }

        self.auth_code_data = {

        }

        self.str_sess = {}

        self.loop = asyncio.new_event_loop()

        self.bot = Bot(
            token=BOT_TOKEN,
            disable_web_page_preview=True,
            parse_mode='html'
        )

        self.thread_loop = KThread(target=self._run_polling)
        self.thread_loop.start()

    async def _polling_processing(self):
        while True:
            await asyncio.sleep(0.1)

    def _run_polling(self):
        self.loop.run_until_complete(self._polling_processing())
    
    async def code_auth_send_code_step(self, phone: str, owner_id: int):

        session_file = f'accounts/tl/{phone}.session'

        # proxy = self.proxy

        # proxy['username'] = f"{random.randint(10000, 2147483647)}"
        # proxy['password'] = '1'

        # proxy = {
        #     "proxy_type": "socks5",
        #     "addr": "lproxy.site",
        #     "port": 14295,
        #     "username": "yG2YC2",
        #     "password": "tyN7As6ADYT2",
        #     "rdns": True
        # }

        # proxy = {
        #     "proxy_type": "socks5",
        #     "addr": "lproxy.site",
        #     "port": 14295,
        #     "username": "bmo",
        #     "password": "123456",
        #     "rdns": True
        # }

        # proxy = {
        #     "proxy_type": "socks5",
        #     "addr": "145.249.253.32",
        #     "port": 52059,
        #     "username": "pr34serv1mart",
        #     "password": "Ki49Fad2",
        #     "rdns": True
        # }

        # socks5://185.241.192.80:14321:duRDUM:PUh9edgAq9Ap

        proxy = {
            "proxy_type": "socks5",
            "addr": "185.241.192.80",
            "port": 14321,
            "username": "duRDUM",
            "password": "PUh9edgAq9Ap",
            "rdns": True
        }

        # proxy = {
        #     "proxy_type": "http",
        #     "addr": "cproxy.site",
        #     "port": 14295,
        #     "username": "bmo",
        #     "password": "123456",
        #     "rdns": True
        # }

        api = API.TelegramMacOS().Generate()

        client = TelegramClient(
            session=session_file,
            api=api
        )

        # str_sess = StringSession.save(client.session)

        # client = TelegramClient(
        #     session=StringSession(str_sess),
        #     api=api,
        #     request_retries=20,
        #     connection_retries=20,
        #     retry_delay=20,
        #     timeout=20,
        #     proxy=proxy
        # )

        await client.connect()

        await client.send_code_request(
            phone=phone
        )

        self.auth_code_data[owner_id] = client
    
    async def code_auth_sign_in_step(self, phone: str, code: str, owner_id: int) -> dict:

        client: TelegramClient = self.auth_code_data[owner_id]

        try:

            await client.sign_in(
                phone=phone,
                code=code
            )

            me = await client.get_me()

            await client.disconnect()
            
            del self.auth_code_data[owner_id]

            if me:
                return {'status': True, 'session_filename': f'accounts/tl/{phone}.session'}
        
        except SessionPasswordNeededError:
            return {'status': False, 'reason': '2FA', 'message': '<b>Необходим 2FA пароль от аккаунта</b>\n\nОтправьте его'}

        except Exception as e:

            await client.disconnect()
            del self.auth_code_data[owner_id]

            if owner_id:

                remove_accounts(
                    user_id=owner_id,
                    account_path=f'accounts/tl/{phone}.session'
                )

                try:

                    shutil.rmtree(f'accounts/tl/{phone}.session')
                
                except:
                    
                    try:
                        os.remove(f'accounts/tl/{phone}.session')
                    except:
                        pass

            return {'status': False, 'reason': 'UNKNOWN', 'message': '<b>Возникла ошибка при авторизации вашего аккаунта</b>\n\nСкорее всего вы ввели код неверно, попробуйте повторить процесс авторизации через несколько минут...'}

    async def code_auth_sign_in_2fa_step(self, phone: str, code: str, owner_id: int, password: str) -> dict:

        client: TelegramClient = self.auth_code_data[owner_id]

        try:

            await client.sign_in(
                password=password
            )

            me = await client.get_me()

            await client.disconnect()
            
            del self.auth_code_data[owner_id]

            if me:
                return {'status': True, 'session_filename': f'accounts/tl/{phone}.session'}

        except PasswordHashInvalidError:
            return {'status': False, 'reason': '2FA', 'message': '<b>Вы ввели неправильный пароль</b>\n\nСверьте коррректность ввода и попробуйте еще раз'}

        except Exception as e:

            await client.disconnect()
            del self.auth_code_data[owner_id]

            if owner_id:

                remove_accounts(
                    user_id=owner_id,
                    account_path=f'accounts/tl/{phone}.session'
                )

                try:

                    shutil.rmtree(f'accounts/tl/{phone}.session')
                
                except:
                    
                    try:
                        os.remove(f'accounts/tl/{phone}.session')
                    except:
                        pass

            return {'status': False, 'reason': 'UNKNOWN', 'message': '<b>Возникла ошибка при авторизации вашего аккаунта</b>\n\nПопробуйте повторить процесс авторизации через несколько минут...'}

    async def fetch_clients_from_tdatas(self, tdatas: list[str], owner_id: int = None) -> list[TelegramClient]:

        results = []

        for tdata in tdatas:

            try:

                tdesk = TDesktop(tdata)

                # proxy = self.proxy

                # proxy['username'] = f"{random.randint(10000, 2147483647)}"
                # proxy['password'] = '1'

                proxy = {
                    "proxy_type": "socks5",
                    "addr": "lproxy.site",
                    "port": 14295,
                    "username": "yG2YC2",
                    "password": "tyN7As6ADYT2",
                    "rdns": True
                }

                client = await tdesk.ToTelethon(
                    session=None,
                    flag=UseCurrentSession,
                    api=tdesk.api,
                    proxy=proxy
                )

                await client.connect()

                me = await client.get_me()

                if not me:
                    raise UserDeactivatedError(client.get_me)
                
                results.append(client)
                
                print(f'{me.phone} подключен')

            except UserDeactivatedError as e:
                
                print(f'{tdata} Ошибка при подключении клиента: {e}')

                if owner_id:

                    kb = bot_types.InlineKeyboardMarkup()

                    kb.add(
                        bot_types.InlineKeyboardButton(
                            text='Удалить аккаунт',
                            callback_data=f'rm_acc|{tdata}'
                        )
                    )

                    try:
                        await self.bot.send_message(
                            chat_id=owner_id,
                            text=f'Аккаунт <b>{tdata}</b> забанен',
                            reply_markup=kb
                        )
                    except:
                        pass
                    
                await client.disconnect()
            
            except Exception as e:

                print(f'{tdata} Ошибка при подключении клиента: {e}')

                try:
                    await client.disconnect()
                except:
                    pass
        
        return results
    
    async def fetch_clients_from_sessions(self, sessions: list[str], owner_id: int = None) -> list[TelegramClient]:

        results = []

        sessions = [session for session in sessions if session.endswith('.session')]

        for session in sessions:

            try:

                api = API.TelegramMacOS().Generate()

                api.lang_code = 'ru-RU'
                api.lang_pack = 'ru-RU'
                api.system_lang_code = 'ru-RU'

                proxy = {
                    "proxy_type": "socks5",
                    "addr": "185.241.192.80",
                    "port": 14321,
                    "username": "duRDUM",
                    "password": "PUh9edgAq9Ap",
                    "rdns": True
                }

                client = TelegramClient(
                    session=session,
                    api=api,
                    proxy=proxy
                )

                str_sess = StringSession.save(client.session)

                client = TelegramClient(
                    session=StringSession(str_sess),
                    api=api,
                    request_retries=20,
                    connection_retries=20,
                    retry_delay=20,
                    timeout=20,
                    proxy=proxy
                )
            
            except Exception as e:
                if owner_id:
                    remove_accounts(
                        user_id=owner_id,
                        account_path=session
                    )
                    try:
                        await self.bot.send_message(
                            chat_id=owner_id,
                            text=f'Аккаунт <b>{session.split("/")[-1]}</b> забанен и не был добавлен', )
                    except:
                        pass
                    try:
                        shutil.rmtree(session)
                    except:
                        try:
                            os.remove(session)
                        except:
                            pass
                print(f'Непредвиденная ошибка при загрузке сессии: {e}')
                continue

            try:

                await client.connect()

                me = await client.get_me()

                if not me:
                    raise UserDeactivatedError(client.get_me)
                
                results.append(client)
                self.str_sess[me.id] = session
                
                print(f'{me.phone} подключен')
            
            except AuthKeyDuplicatedError as e:

                print(f'{session} Ошибка при подключении клиента: {e}')

                await client.disconnect()

                if owner_id:
                    remove_accounts(
                        user_id=owner_id,
                        account_path=session
                    )
                    try:
                        await self.bot.send_message(
                            chat_id=owner_id,
                            text=f'Аккаунт <b>{session.split("/")[-1]}</b> забанен и не был добавлен', )
                    except:
                        pass
                    try:
                        shutil.rmtree(session)
                    except:
                        try:
                            os.remove(session)
                        except:
                            pass
                                
            except OperationalError as e:

                await client.disconnect()

                print(f'{session} Ошибка при подключении клиента: {e}')

                if owner_id:
                    remove_accounts(
                        user_id=owner_id,
                        account_path=session
                    )
                    try:
                        await self.bot.send_message(
                            chat_id=owner_id,
                            text=f'Аккаунт <b>{session.split("/")[-1]}</b> забанен и не был добавлен', )
                    except:
                        pass
                    try:
                        shutil.rmtree(session)
                    except:
                        try:
                            os.remove(session)
                        except:
                            pass  
            
            except UserDeactivatedError as e:

                await client.disconnect()
                
                print(f'{session} Ошибка при подключении клиента: {e}')

                if owner_id:
                    remove_accounts(
                        user_id=owner_id,
                        account_path=session
                    )
                    try:
                        await self.bot.send_message(
                            chat_id=owner_id,
                            text=f'Аккаунт <b>{session.split("/")[-1]}</b> забанен и не был добавлен',)
                    except:
                        pass
                    try:
                        shutil.rmtree(session)
                    except:
                        try:
                            os.remove(session)
                        except:
                            pass

            except Exception as e:

                await client.disconnect()

                print(f'{session} Ошибка при подключении клиента: {e}')
                if owner_id:
                    remove_accounts(
                        user_id=owner_id,
                        account_path=session
                    )
                    try:
                        await self.bot.send_message(
                            chat_id=owner_id,
                            text=f'Аккаунт <b>{session.split("/")[-1]}</b> забанен и не был добавлен',)
                    except:
                        pass
                    try:
                        shutil.rmtree(session)
                    except:
                        try:
                            os.remove(session)
                        except:
                            pass
        
        return results