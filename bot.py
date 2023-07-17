from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext

import asyncio
import random
from datetime import datetime

from aiogram.dispatcher.filters import IsReplyFilter, BoundFilter

from config import *
from states import *
from kb import *
from db_manage import *
from utils import *

bot = Bot(
    token=BOT_TOKEN,
    disable_web_page_preview=True,
    parse_mode='HTML'
)

dp = Dispatcher(bot, storage=MemoryStorage())


@dp.message_handler(lambda message: message.text == '🏘 Главное меню', state='*')
async def start_message_handler(message: types.Message, state: FSMContext):
    create_user_if_not_exist(message.from_user.id)
    await state.finish()
    user_data = get_user(message.chat.id)

    await message.answer(
        '<b>🏡 Главное меню</b>\n\n' +
        f'<b>👀 Ваш ID:</b> {message.chat.id}\n' +
        f'<b>💰 Баланс:</b> {user_data["balance"]} ₽\n' +
        f'<b>⏳ Ваша подписка истекает:</b> {convert_timestamp_to_dt(user_data["sub_data_dt_expire"]).strftime("%d.%m.%Y")}\n' +
        f'<b>🔋 Лимит на аккаунты:</b> {user_data["sub_data_account_limit"]}\n\n' +
        f'<b>👥 Добавлено аккаунтов:</b>\n' +
        # f'  -> TDATA: {len(user_data["accounts"]["td"])}\n'+
        f'  -> SESSION: {len(user_data["accounts"]["tl"])}\n' +
        f'  -> GPT: {len(get_user_tokens(message.chat.id))}',
        reply_markup=start_kb
    )


@dp.message_handler(commands=['start'], state='*')
async def start_command_handler(message: types.Message, state: FSMContext):
    referal_id = message.get_args()
    if referal_id:
        if referal_id!=str(message.chat.id):
            await bot.send_message(referal_id, f'По вашей ссылке присоединился <a href="tg://user?id={referal_id}">пользователь</a>! После того как его баланс пополнится, вы получите 10%, от суммы пополнения.')
        else:
            referal_id = None
    create_user_if_not_exist(
        user_id=message.from_user.id,
        referal_id=int(referal_id) if referal_id else None
    )
    
    user_data = get_user(message.chat.id)

    await message.answer(
        '<b>🏡 Главное меню</b>\n\n' +
        f'<b>👀 Ваш ID:</b> {message.chat.id}\n' +
        f'<b>💰 Баланс:</b> {user_data["balance"]} ₽\n' +
        f'<b>⏳ Ваша подписка истекает:</b> {convert_timestamp_to_dt(user_data["sub_data_dt_expire"]).strftime("%d.%m.%Y")}\n' +
        f'<b>🔋 Лимит на аккаунты:</b> {user_data["sub_data_account_limit"]}\n\n' +
        f'<b>👥 Добавлено аккаунтов:</b>\n' +
        # f'  -> TDATA: {len(user_data["accounts"]["td"])}\n'+
        f'  -> SESSION: {len(user_data["accounts"]["tl"])}\n' +
        f'  -> GPT: {len(get_user_tokens(message.chat.id))}',
        reply_markup=start_kb
    )


@dp.callback_query_handler(lambda call: call.data == 'move_to_accounts_gpt_menu', state='*')
async def move_to_accounts_gpt_menu(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer(f"Количетво gpt токенов: {len(get_user_tokens(call.message.chat.id))}",
                              reply_markup=gpt_tokens_kb
                              )


@dp.callback_query_handler(lambda call: call.data == 'add_gpt_tokens', state='*')
async def add_gpt_tokens(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer('<b>Отправьте список из ключей (каждый с новой строки)</b>\n\n' +
                              '* ключ начинается с "sk-"',
                              reply_markup=cancel_kb
                              )
    await state.set_state(GPTTokens.new_tokens)


@dp.message_handler(state=GPTTokens.new_tokens)
async def new_tokens(message: types.Message, state: FSMContext):
    tokens_all = get_user_tokens(message.chat.id)
    tokens = message.text.split()
    for token in tokens:
        if token.startswith("sk-") and token.count("sk-") == 1:
            tokens_all.append(token)
    set_user_tokens(message.chat.id, tokens_all)
    await message.answer(f"Количетво gpt токенов: {len(tokens_all)}",
                         reply_markup=gpt_tokens_kb
                         )
    await state.finish()


@dp.callback_query_handler(lambda call: call.data == 'my_referal_link', state='*')
async def my_referal_link_handler(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer(
        '<b>🔗 Ваша реферальная ссылка:</b>\n\n' +
        f'https://t.me/NeyroComment_bot?start={call.message.chat.id}\n\n' +
        f'Приглашая по ней пользователей, вы будете получать 10% от суммы их каждого пополнения баланса'
    )


@dp.callback_query_handler(lambda call: call.data == 'cancel', state='*')
async def cancel_handler(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await call.message.edit_text('Отменено')


@dp.callback_query_handler(lambda call: call.data == 'support', state='*')
async def support_handler(call: types.CallbackQuery, state: FSMContext):
    await SupportForm.message.set()

    await call.message.answer(
        'Отправьте ваше сообщение для поддержки',
        reply_markup=cancel_kb
    )


@dp.message_handler(state=SupportForm.message)
async def support_form_message_step_handler(message: types.Message, state: FSMContext):
    for admin in ADMINS:
        await bot.send_message(chat_id=admin,
                               text=f'Обращение в поддержку от пользователя <tg-spoiler>[@{message.from_user.username}] |{message.chat.id}| ~{message.message_id}~</tg-spoiler>, ответьте на это сообщение, чтобы переслать его пользователю\n\n{message.text}')
    await message.reply("Сообщение отправлено", reply_markup=start_reply_kb)


class ReplyForwardFilterBot(BoundFilter):
    async def check(self, msg: types.Message):
        try:
            if msg.reply_to_message.text:
                return True
        except Exception:
            pass


@dp.message_handler(ReplyForwardFilterBot())
async def support_send_answer(message: types.Message, state: FSMContext):
    if message.chat.id in ADMINS:
        rtm = message.reply_to_message.text
        await bot.send_message(chat_id=rtm.split("|")[1],
                               text=f"Ответ от поддержки:\n\n{message.text}",
                               reply_to_message_id=rtm.split("~")[1])
        for admin in ADMINS:
            if admin != message.chat.id:
                await bot.send_message(chat_id=admin,
                                       text=f"Один из админов ответил на вопрос: "
        await message.reply("Ваше сообщение отправлено")


@dp.callback_query_handler(lambda call: call.data == 'sub_menu', state='*')
async def sub_menu_handler(call: types.CallbackQuery, state: FSMContext):
    subs = get_all_subs()

    subs_kb = types.InlineKeyboardMarkup()

    for sub in subs:
        subs_kb.add(
            types.InlineKeyboardButton(
                text=f'{int(sub["sub_data_dt_delta_expire"] / 86400)} дней · {sub["sub_data_account_limit"]} аккаунтов · {sub["price"]} ₽',
                callback_data=f'buy_sub|{sub["id"]}'
            )
        )

    await call.message.answer(
        '<b>☘️ Тарифные планы</b>\n\n' +
        '⊢ рекомендация по работе:\n\n' +
        '〉 1 аккаунт ≤ 25 каналов\n' +
        '〉 не дублировать каналы',
        reply_markup=subs_kb
    )


@dp.callback_query_handler(lambda call: call.data.startswith('buy_sub'), state='*')
async def buy_sub_handler(call: types.CallbackQuery, state: FSMContext):
    _, sub_id = call.data.split('|')

    sub_id = int(sub_id)
    sub = get_sub_by_id(sub_id)

    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton(
            text='🤑 Приобрести',
            callback_data=f'take_sub_choice|{sub["id"]}'
        )
    )
    kb.add(
        types.InlineKeyboardButton(
            text='⬅️ Назад',
            callback_data='sub_menu'
        )
    )

    await call.message.edit_text(
        '<b>Тарифный план</b>\n\n' +
        f'<b>Количество дней</b> · {int(sub["sub_data_dt_delta_expire"] / 86400)} дней\n' +
        f'<b>Лимит по аккаунтам</b> · {sub["sub_data_account_limit"]} аккаунтов\n' +
        f'<b>Стоимость</b> · {sub["price"]} ₽',
        reply_markup=kb
    )


@dp.callback_query_handler(lambda call: call.data == 'popup_balance', state='*')
async def popup_balance_handler(call: types.CallbackQuery, state: FSMContext):
    await PopupBalanceForm.summ.set()

    await call.message.answer(
        '<b>🚀 Пополнить баланс </b>\n\n' +
        '∟ Введите сумму пополнения\n' +
        f'Минимальная сумма пополнения - <b>{MIN_PAYMENT_SUMM} ₽</b>',
        reply_markup=cancel_kb
    )


@dp.message_handler(lambda message: message.text.isdigit, state=PopupBalanceForm.summ)
async def popup_balance_form_step_summ_handler(message: types.Message, state: FSMContext):
    summ = float(message.text)

    if summ < MIN_PAYMENT_SUMM:
        await message.answer(f'Сумма пополнения должна быть не меньше <b>{MIN_PAYMENT_SUMM} ₽</b>')
        return

    payment_data = await create_payment(
        amount=summ,
        user_id=message.chat.id
    )

    await state.finish()

    kb = types.InlineKeyboardMarkup()

    kb.add(
        types.InlineKeyboardButton(
            text='Оплатить',
            url=payment_data["url"]
        )
    )

    kb.add(
        types.InlineKeyboardButton(
            text='Я оплатил',
            callback_data=f'check_payment|{payment_data["bill_id"]}'
        )
    )

    await message.answer(
        '<b>Ваша платежная ссылка готова</b>\n\n' +
        f'К оплате <b>{summ} ₽</b>\n\n' +
        'После проведения платежа нажмите на кнопку ниже <b>Я оплатил</b>',
        reply_markup=kb
    )


@dp.callback_query_handler(lambda call: call.data.startswith('check_payment'), state='*')
async def check_payment_handler(call: types.CallbackQuery, state: FSMContext):
    _, bill_id = call.data.split('|')

    status = await check_payment(bill_id)

    if status is False:
        await call.answer('Оплата еще не поступила на счет')
        return
    user = get_user(call.message.chat.id)
    user["referal_id"]
    amount = status
    if user:
        await bot.send_message(
            chat_id=user['referal_id'],
            text=f'💰 На ваш баланс зачислено <b>{amount/10} ₽</b> по реферальной системе'
        )
        update_user_balance(
            user_id=user['referal_id'],
            value=amount/10
        )
    await call.message.edit_text(
        '<b>Оплата прошла успешно! Благодарим вас за покупку!</b>\n\nПроверьте состояние вашего баланса' +
        '\n\n<b>Не забудьте приобрести один из представленных в боте тарифных планов, иначе бот работать не будет !</b>'
    )


@dp.callback_query_handler(lambda call: call.data.startswith('take_sub_choice'), state='*')
async def take_sub_choice(call: types.CallbackQuery, state: FSMContext):
    _, sub_id = call.data.split('|')
    sub_id = int(sub_id)

    user = get_user(call.message.chat.id)
    sub = get_sub_by_id(sub_id)

    if user["balance"] < sub["price"]:
        await call.answer(
            'На вашем балансе недостаточно средств для приобретения этого тарифного плана\n\nПополните баланс в разделе Мой профиль',
            show_alert=True)
        return

    update_user_sub(
        user_id=call.message.chat.id,
        sub_data_dt_expire=sub["sub_data_dt_delta_expire"] + int(datetime.now().timestamp()),
        sub_data_account_limit=sub["sub_data_account_limit"]
    )

    r = update_user_balance(
        user_id=call.message.chat.id,
        value=sub["price"] * -1
    )

    await call.message.edit_text(
        '<b>✅ Тарифный план успешно оформлен</b>\n\n' +
        'Благодарим вас за покупку!'
    )


@dp.callback_query_handler(lambda call: call.data == 'my_sub', state='*')
async def my_sub_handler(call: types.CallbackQuery, state: FSMContext):
    user_data = get_user(call.message.chat.id)

    await call.message.answer(
        f'<b>💰 Баланс:</b> {user_data["balance"]} ₽\n' +
        f'<b>⏳ Ваша подписка истекает:</b> {convert_timestamp_to_dt(user_data["sub_data_dt_expire"]).strftime("%d.%m.%Y")}\n' +
        f'<b>🔋 Лимит на аккаунты:</b> {user_data["sub_data_account_limit"]}\n\n',
        reply_markup=payment_kb
    )


@dp.callback_query_handler(lambda call: call.data == 'remove_accounts', state='*')
async def remove_accounts_handler(call: types.CallbackQuery, state: FSMContext):
    old_remove_accounts(call.message.chat.id)
    await call.answer('Ваши аккаунты были успешно удалены')


@dp.callback_query_handler(lambda call: call.data == 'dump_accounts', state='*')
async def dump_accounts_handler(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer(
        'Выберите тип аккаунтов',
        reply_markup=accounts_dump_kb
    )


@dp.callback_query_handler(lambda call: call.data == 'dump_tdata', state='*')
async def dump_accounts_tdata_handler(call: types.CallbackQuery, state: FSMContext):
    user = get_user(call.message.chat.id)

    temp_arch_name = f'temp/{call.message.chat.id}_{random.randint(1, 99999999)}.zip'

    dump_accounts(
        file_paths=user["accounts"]["td"],
        zip_path=temp_arch_name
    )

    await call.message.answer_document(
        document=types.InputFile(temp_arch_name),
        caption='Ваши аккаунты формата TDATA'
    )

    os.remove(temp_arch_name)


@dp.callback_query_handler(lambda call: call.data == 'dump_session', state='*')
async def dump_accounts_session_handler(call: types.CallbackQuery, state: FSMContext):
    user = get_user(call.message.chat.id)

    temp_arch_name = f'temp/{call.message.chat.id}_{random.randint(1, 99999999)}.zip'

    dump_accounts(
        file_paths=user["accounts"]["tl"],
        zip_path=temp_arch_name
    )

    await call.message.answer_document(
        document=types.InputFile(temp_arch_name),
        caption='Ваши аккаунты формата Session'
    )

    os.remove(temp_arch_name)


@dp.callback_query_handler(lambda call: call.data.startswith('join_accounts'), state='*')
async def join_accounts_handler(call: types.CallbackQuery, state: FSMContext):
    _, phone = call.data.split('|')

    if not can_user_working(call.message.chat.id):
        await call.message.answer('Вам необходимо приобрести подписку перед тем как воспользоваться функционалом бота')
        return

    await AccountsJoinForm.channels.set()
    await state.update_data(phone=phone)

    await call.message.answer(
        text='<b>Отправьте список из ссылок на каналы</b>',
        reply_markup=cancel_kb
    )


@dp.message_handler(state=AccountsJoinForm.channels)
async def accounts_join_form_channels_step_handler(message: types.Message, state: FSMContext):
    links = message.text.splitlines()

    data = await state.get_data()
    await state.finish()

    asyncio.ensure_future(join_channels(phone=data['phone'], channels=links, owner_id=message.chat.id),
                          loop=asyncio.get_event_loop())
    await back_to_account_edit(message=message, data=data)


@dp.callback_query_handler(lambda call: call.data == 'append_accounts', state='*')
async def append_accounts_handler(call: types.CallbackQuery, state: FSMContext):
    if not can_user_add_accounts(call.message.chat.id):
        await call.message.answer('Вы исчерпали лимит на добавление аккаунтов')
        return

    if not can_user_working(call.message.chat.id):
        await call.message.answer('Вам необходимо приобрести подписку перед тем как воспользоваться функционалом бота')
        return

    await AddAccountsForm.account_type.set()

    await call.message.edit_text(
        text='<b>Выберите тип загружаемых вами аккаунтов</b>',
        reply_markup=accounts_type_kb
    )


@dp.callback_query_handler(lambda call: call.data.startswith('account_type_choice'), state=AddAccountsForm.account_type)
async def add_acccount_form_account_type_step_handler(call: types.CallbackQuery, state: FSMContext):
    _, account_type = call.data.split('|')

    await state.update_data(account_type=account_type)
    await AddAccountsForm.accounts_paths.set()

    if account_type == 'tdata':

        await call.message.edit_text(
            '<b>Отправьте архив с аккаунтами</b>\n\n' +
            'Обращаем ваше внимание на то, что в архиве не должно быть никаких подпапок\n' +
            'Аккаунты формата TDATA должны быть в предоставлены в следующем формате:\n\n' +
            'archive.zip/xxxx/tdata\n' +
            'archive.zip/xxxxx/tdata\n',
            reply_markup=cancel_kb
        )

    elif account_type == 'session':

        await call.message.edit_text(
            '<b>Отправьте архив с аккаунтами</b>\n\n' +
            'Обращаем ваше внимание на то, что в архиве не должно быть никаких подпапок\n',
            reply_markup=cancel_kb
        )

    elif account_type == 'via_code':

        await AddAccountsForm.account_phone_num.set()

        await call.message.edit_text(
            '<b>Отправьте номер телефона, привязанный к вашему аккаунту</b>',
            reply_markup=cancel_kb
        )


@dp.message_handler(state=AddAccountsForm.account_phone_num)
async def add_accounts_form_account_phone_num_step_handler(message: types.Message, state: FSMContext):
    await state.update_data(account_phone_num=message.text)

    await code_auth_send_code_step(
        phone=message.text,
        owner_id=message.chat.id
    )

    await AddAccountsForm.account_code.set()
    await state.update_data(account_code='')

    await message.answer(
        '<b>Наберите код, который вам пришел, используя клавиатуру ниже</b>\n\n' +
        f'Текущий код: ',
        reply_markup=code_input_kb
    )


@dp.callback_query_handler(lambda call: call.data.isdigit(), state=AddAccountsForm.account_code)
async def add_accounts_form_account_code_step_handler(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.update_data(account_code=data['account_code'] + call.data)

    data = await state.get_data()

    await call.message.edit_text(
        '<b>Наберите код, который вам пришел, используя клавиатуру ниже</b>\n\n' +
        f'Текущий код: {data["account_code"]}',
        reply_markup=code_input_kb
    )


@dp.callback_query_handler(lambda call: call.data == 'delete', state=AddAccountsForm.account_code)
async def add_accounts_form_account_code_step_handler(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.update_data(account_code=data['account_code'][:-1])

    data = await state.get_data()

    await call.message.edit_text(
        '<b>Наберите код, который вам пришел, используя клавиатуру ниже</b>\n\n' +
        f'Текущий код: {data["account_code"]}',
        reply_markup=code_input_kb
    )


@dp.callback_query_handler(lambda call: call.data == 'confirm', state=AddAccountsForm.account_code)
async def add_accounts_form_account_code_step_handler(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()

    session_data = await code_auth_sign_in_step(
        phone=data['account_phone_num'],
        code=data['account_code'],
        owner_id=call.message.chat.id
    )

    if session_data['status']:

        update_user_accounts(
            user_id=call.message.chat.id,
            accounts=[session_data['session_filename']],
            account_type='session'
        )

        await split_run_task(accounts=[session_data['session_filename']], type='session', owner_id=call.message.chat.id)

        await state.finish()
        await call.message.edit_text('Аккаунт успешно добавлен!', reply_markup=append_accounts_independ_kb)

    elif not session_data['status'] and session_data['reason'] == '2FA':

        await AddAccountsForm.account_2fa_code.set()
        await call.message.edit_text(session_data['message'], reply_markup=cancel_kb)

    elif not session_data['status'] and session_data['reason'] == 'UNKNOWN':

        await state.finish()
        await call.message.edit_text(session_data['message'])


@dp.message_handler(state=AddAccountsForm.account_2fa_code)
async def add_accounts_form_account_2fa_code_step_handler(message: types.Message, state: FSMContext):
    password = message.text

    data = await state.get_data()

    session_data = await code_auth_sign_in_2fa_step(
        phone=data['account_phone_num'],
        code=data['account_code'],
        owner_id=message.chat.id,
        password=password
    )

    if session_data['status']:

        update_user_accounts(
            user_id=message.chat.id,
            accounts=[session_data['session_filename']],
            account_type='session'
        )

        await split_run_task(accounts=[session_data['session_filename']], type='session', owner_id=message.chat.id)

        await state.finish()
        await message.answer('Аккаунт успешно добавлен!', reply_markup=append_accounts_independ_kb)

    elif not session_data['status'] and session_data['reason'] == '2FA':

        await AddAccountsForm.account_2fa_code.set()
        await message.answer(session_data['message'], reply_markup=cancel_kb)

    elif not session_data['status'] and session_data['reason'] == 'UNKNOWN':

        await state.finish()
        await message.answer(session_data['message'])


@dp.message_handler(state=AddAccountsForm.accounts_paths, content_types=['document'])
async def add_accounts_form_accounts_paths_step_handler(message: types.Message, state: FSMContext):
    filters = [
        not ".zip" in message.document.file_name,
        not ".rar" in message.document.file_name
    ]

    if all(filters):
        await message.answer('Такой формат архива не поддерживается')
        return

    form_data = await state.get_data()

    if form_data["account_type"] == 'tdata':

        rnd_temp_path = f'temp/{message.chat.id}_{random.randint(1, 9999999999)}.{"zip" if message.document.mime_type == "application/zip" else "rar"}'

        await message.document.download(rnd_temp_path)
        accounts = unpack_archive(rnd_temp_path, 'accounts/td')

        update_user_accounts(
            user_id=message.chat.id,
            accounts=accounts,
            account_type='tdata'
        )

    elif form_data["account_type"] == "session":

        rnd_temp_path = f'temp/{message.chat.id}_{random.randint(1, 9999999999)}.{"zip" if message.document.mime_type == "application/zip" else "rar"}'

        await message.document.download(rnd_temp_path)
        accounts = unpack_archive(rnd_temp_path, 'accounts/tl')
        update_user_accounts(
            user_id=message.chat.id,
            accounts=accounts,
            account_type='session'
        )

    await state.finish()
    await message.answer('Аккаунты успешно добавлены!', reply_markup=append_accounts_independ_kb)

    # asyncio.ensure_future(run_user_tasks([get_user(message.chat.id)]), loop=asyncio.get_event_loop())
    await split_run_task(accounts=accounts, type=form_data["account_type"], owner_id=message.chat.id)

    os.remove(rnd_temp_path)


@dp.callback_query_handler(lambda call: call.data.startswith('rcomm'), state='*')
async def remove_comment_handler(call: types.CallbackQuery, state: FSMContext):
    _, account_id, channel_id, message_id = call.data.split('|')

    await remove_comment(
        account_id=int(account_id),
        channel_id=int(channel_id),
        message_id=int(message_id)
    )

    await call.message.edit_text('<b>Комментарий удален</b>')


@dp.callback_query_handler(lambda call: call.data.startswith('ecomm'), state='*')
async def edit_comment_handler(call: types.CallbackQuery, state: FSMContext):
    _, account_id, channel_id, message_id = call.data.split('|')

    await EditCommentForm.new_content.set()

    await state.update_data(account_id=int(account_id))
    await state.update_data(channel_id=int(channel_id))
    await state.update_data(message_id=int(message_id))

    await call.message.answer(
        'Отправьте новое содержание для комментария',
        reply_markup=cancel_kb
    )


@dp.message_handler(state=EditCommentForm.new_content)
async def edit_comment_form_new_content_step_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await state.finish()

    await edit_comment(
        account_id=data['account_id'],
        channel_id=data['channel_id'],
        message_id=data['message_id'],
        new_content=message.text
    )

    await message.answer(
        'Отредактировано'
    )


@dp.callback_query_handler(lambda call: call.data.startswith('rm_acc'), state='*')
async def remove_account_handler(call: types.CallbackQuery, state: FSMContext):
    _, account_path = call.data.split('|')

    await remove_account(
        account_path=account_path,
        owner_id=call.message.chat.id
    )

    await call.message.edit_text(
        text='Аккаунт удален'
    )


@dp.callback_query_handler(lambda call: call.data.startswith('account_edit_lname'), state='*')
async def account_edit_lname_handler(call: types.CallbackQuery, state: FSMContext):
    _, phone = call.data.split('|')

    if not can_user_working(call.message.chat.id):
        await call.message.answer('Вам необходимо приобрести подписку перед тем как воспользоваться функционалом бота')
        return

    await EditAccountLastName.lname.set()
    await state.update_data(phone=phone)

    await call.message.answer(
        '<b>Отправьте новую Фамилию</b>\n\n' +
        'Фамилия не должна быть больше 20 символов',
        reply_markup=cancel_kb
    )


@dp.message_handler(state=EditAccountLastName.lname)
async def edit_account_last_name_lname_step_handler(message: types.Message, state: FSMContext):
    if len(message.text) > 20:
        await message.answer('Фамилия не должна быть больше 20 символов')

    data = await state.get_data()
    await state.finish()

    await update_last_name(phone=data['phone'], last_name=message.text, owner_id=message.chat.id)
    await back_to_account_edit(message=message, data=data)

@dp.callback_query_handler(lambda call: call.data.startswith('account_edit_uname'), state='*')
async def account_edit_uname_handler(call: types.CallbackQuery, state: FSMContext):
    _, phone = call.data.split('|')

    if not can_user_working(call.message.chat.id):
        await call.message.answer('Вам необходимо приобрести подписку перед тем как воспользоваться функционалом бота')
        return

    await EditAccountUsername.username.set()
    await state.update_data(phone=phone)

    await call.message.answer(
        '<b>Отправьте ноывый Юзернейм</b>\n\n' +
        'Юзернейм не должен быть от 5 до 20 символов',
        reply_markup=cancel_kb
    )

@dp.message_handler(state=EditAccountUsername.username)
async def editaccountusername_username(message: types.Message, state: FSMContext):
    if len(message.text) > 20 and len(message.text) < 5:
        await message.answer('Юзернейм должен быть от 5 до 20 симовлов!')
        return

    data = await state.get_data()
    await state.finish()

    await update_username(phone=data['phone'], username=message.text.replace("@", ""), owner_id=message.chat.id)
    await back_to_account_edit(message=message, data=data)


@dp.callback_query_handler(lambda call: call.data.startswith('account_edit_fname'), state='*')
async def account_edit_fname_handler(call: types.CallbackQuery, state: FSMContext):
    _, phone = call.data.split('|')

    if not can_user_working(call.message.chat.id):
        await call.message.answer('Вам необходимо приобрести подписку перед тем как воспользоваться функционалом бота')
        return

    await EditAccountFirstName.fname.set()
    await state.update_data(phone=phone)

    await call.message.answer(
        '<b>Отправьте новое Имя</b>\n\n' +
        'Имя не должно быть больше 20 символов',
        reply_markup=cancel_kb
    )


@dp.message_handler(state=EditAccountFirstName.fname)
async def edit_account_first_name_fname_step_handler(message: types.Message, state: FSMContext):
    if len(message.text) > 20:
        await message.answer('Имя не должно быть больше 20 символов!')
        return

    data = await state.get_data()
    await state.finish()

    await update_first_name(phone=data['phone'], first_name=message.text, owner_id=message.chat.id)
    await back_to_account_edit(message=message, data=data)


@dp.callback_query_handler(lambda call: call.data.startswith('account_edit_bio'), state='*')
async def account_edit_bio_handler(call: types.CallbackQuery, state: FSMContext):
    _, phone = call.data.split('|')

    if not can_user_working(call.message.chat.id):
        await call.message.answer('Вам необходимо приобрести подписку перед тем как воспользоваться функционалом бота')
        return

    await EditAccountBio.bio.set()
    await state.update_data(phone=phone)

    await call.message.answer(
        '<b>🖇 Отправьте новое описание</b>\n\n' +
        'Описание не должно быть больше 70 символов',
        reply_markup=cancel_kb
    )


@dp.message_handler(state=EditAccountBio.bio)
async def edit_account_bio_bio_step_handler(message: types.Message, state: FSMContext):
    if len(message.text) > 70:
        await message.answer('Описание должно быть не более 70 символов')
        return

    data = await state.get_data()
    await state.finish()

    await update_bio(phone=data['phone'], bio=message.text, owner_id=message.chat.id)
    await back_to_account_edit(message=message, data=data)


@dp.callback_query_handler(lambda call: call.data.startswith('account_edit_avatar'), state='*')
async def account_edit_avatar_handler(call: types.CallbackQuery, state: FSMContext):
    _, phone = call.data.split('|')

    if not can_user_working(call.message.chat.id):
        await call.message.answer('Вам необходимо приобрести подписку перед тем как воспользоваться функционалом бота')
        return

    await EditAccountAvatar.photo.set()
    await state.update_data(phone=phone)

    await call.message.answer(
        '<b>🎨 Отправьте новую аватарку</b>',
        reply_markup=cancel_kb
    )


@dp.callback_query_handler(lambda call: call.data.startswith('leave_channel_accounts'), state='*')
async def leave_channel_accounts_hanlder(call: types.CallbackQuery, state: FSMContext):
    _, phone = call.data.split('|')

    if not can_user_working(call.message.chat.id):
        await call.message.answer('Вам необходимо приобрести подписку перед тем как воспользоваться функционалом бота')
        return

    channels = await get_channels_data(
        phone=phone,
        owner_id=call.message.chat.id
    )

    kb = types.InlineKeyboardMarkup(row_width=5)

    for channel in channels:
        kb.add(
            types.InlineKeyboardButton(
                text=channel['name'],
                callback_data=f'leave_channel|{phone}|{channel["id"]}'
            )
        )

    kb.add(cancel_btn)

    await call.message.answer(
        text='<b>🗑 Выберите канал, который хотите покинуть</b>',
        reply_markup=kb
    )


@dp.callback_query_handler(lambda call: call.data.startswith('check_spam'), state='*')
async def check_spam_handler(call: types.CallbackQuery, state: FSMContext):
    _, phone = call.data.split('|')

    m = await call.message.answer('<b>Проверка на спам блок может занять некоторое время...</b>')

    status = await check_spam_block(
        phone=phone,
        owner_id=call.message.chat.id
    )

    if not status:

        await m.edit_text(
            f'✅ Аккаунт <b>{phone}</b> свободен от ограничений'
        )

    else:

        await m.edit_text(
            f'🚫 Аккаунт <b>{phone}</b> попал под спам блок'
        )


@dp.callback_query_handler(lambda call: call.data.startswith('leave_channel'), state='*')
async def leave_channel_handler(call: types.CallbackQuery, state: FSMContext):
    _, phone, channel_id = call.data.split('|')

    await leave_channel(
        phone=phone,
        owner_id=call.message.chat.id,
        channel_id=int(channel_id)
    )

    await back_to_account_edit(
        message=call.message,
        data={"phone": phone}
    )


async def back_to_account_edit(message: types.Message, data: dict):
    m = await message.answer('<b>🕖 Подождите немного...</b>')

    r = await get_account_info(
        phone=data['phone'],
        owner_id=message.chat.id
    )

    await m.delete()

    kb = types.InlineKeyboardMarkup()
    kb.row(
        types.InlineKeyboardButton(
            text='🎨 Аватарка',
            callback_data=f'account_edit_avatar|{data["phone"]}'
        ),
        types.InlineKeyboardButton(
            text='🖇 Описание',
            callback_data=f'account_edit_bio|{data["phone"]}'
        )
    )

    kb.row(
        types.InlineKeyboardButton(
            text='👔 Имя',
            callback_data=f'account_edit_fname|{data["phone"]}'
        ),
        types.InlineKeyboardButton(
            text='🎽 Фамилия',
            callback_data=f'account_edit_lname|{data["phone"]}'
        )
    )
    kb.row(
        types.InlineKeyboardButton(
            text='📝 Юзернейм',
            callback_data=f'account_edit_uname|{data["phone"]}'
        )
    )
    kb.row(
        types.InlineKeyboardButton(
            text='↩️ Подписать',
            callback_data=f'join_accounts|{data["phone"]}'
        ),
        types.InlineKeyboardButton(
            text='🗑 Отписать',
            callback_data=f'leave_channel_accounts|{data["phone"]}'
        )
    )
    kb.add(
        types.InlineKeyboardButton(
            text='🔒 Проверить спам блок',
            callback_data=f'check_spam|{data["phone"]}'
        )
    )
    kb.add(
        types.InlineKeyboardButton(
            text='❌ Удалить аккаунт',
            callback_data=f'rm_sess|{data["phone"]}'
        )
    )

    kb.add(
        types.InlineKeyboardButton(
            text='⬅️ Назад',
            callback_data='move_to_accounts_menu'
        )
    )

    if r['photo']:

        await bot.send_photo(
            chat_id=message.chat.id,
            photo=types.InputFile(r['photo']),
            caption=f'<b>Аккаунт +{data["phone"]}</b>\n\n' +
                    f"Имя: {r['first_name']}\n" +
                    f"Фамилия: {r['last_name']}\n" +
                    f"Юзернейм: @{r['username']}\n" +
                    f"Описание: {r['about']}\n\n" +
                    f"<b>Список каналов:</b> {len(r['channels'])}",
            reply_markup=kb
        )

    else:

        await bot.send_message(
            chat_id=message.chat.id,
            text=f'<b>Аккаунт +{data["phone"]}</b>\n\n' +
                 f"Имя: {r['first_name']}\n" +
                 f"Фамилия: {r['last_name']}\n" +
                 f"Юзернейм: @{r['username']}\n" +
                 f"Описание: {r['about']}\n\n" +
                 f"<b>Список каналов:</b> {len(r['channels'])}",
            reply_markup=kb
        )


@dp.message_handler(state=EditAccountAvatar.photo, content_types=['photo'])
async def account_edit_avatar_photo_step_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()

    await state.finish()

    dest = await message.photo[-1].download('temp')
    dest = dest.name

    await update_profile_photo(phone=data['phone'], photo_path=dest, owner_id=message.chat.id)
    await back_to_account_edit(message, data)


@dp.callback_query_handler(lambda call: call.data == 'edit_accounts_menu', state='*')
async def edit_accounts_menu_handler(call: types.CallbackQuery, state: FSMContext):
    await call.message.edit_text(
        '<b>✏️ Редактор аккаунтов</b>',
        reply_markup=accounts_edit_kb
    )


@dp.callback_query_handler(lambda call: call.data == 'move_to_main_menu', state='*')
async def move_to_main_menu_handler(call: types.CallbackQuery, state: FSMContext):
    user_data = get_user(call.message.chat.id)

    await call.message.edit_text(
        '<b>🏡 Главное меню</b>\n\n' +
        f'<b>👀 Ваш ID:</b> {call.message.chat.id}\n' +
        f'<b>💰 Баланс:</b> {user_data["balance"]} ₽\n' +
        f'<b>⏳ Ваша подписка истекает:</b> {convert_timestamp_to_dt(user_data["sub_data_dt_expire"]).strftime("%d.%m.%Y")}\n' +
        f'<b>🔋 Лимит на аккаунты:</b> {user_data["sub_data_account_limit"]}\n\n' +
        f'<b>👥 Добавлено аккаунтов:</b>\n'
        # f'  -> TDATA: {len(user_data["accounts"]["td"])}\n'+
        f'  -> SESSION: {len(user_data["accounts"]["tl"])}\n' +
        f'  -> GPT: {len(get_user_tokens(call.message.chat.id))}',
        reply_markup=start_kb
    )


@dp.callback_query_handler(lambda call: call.data == 'move_to_accounts_menu', state='*')
async def move_to_accounts_menu_handler(call: types.CallbackQuery, state: FSMContext):
    if not can_user_working(call.message.chat.id):
        await call.answer('Необходимо приобрести подписку')
        return

    m = await call.message.answer(
        '<b>🕖 Мы собираем данные по вашим аккаунтам...</b>\n\nЭто может занять некоторое время...')
    await call.message.delete()

    accounts = await get_accounts_info(call.message.chat.id)
    accounts_kb = types.InlineKeyboardMarkup()

    for account in accounts:
        accounts_kb.add(
            types.InlineKeyboardButton(
                text=f'🫡 {account["phone"]} {account["first_name"]} {account["last_name"]}',
                callback_data=f'm_account|{account["phone"]}'
            )
        )

    accounts_kb.row(
        types.InlineKeyboardButton(
            text='⤴️ Добавить аккаунты',
            callback_data='append_accounts'
        )
    )
    accounts_kb.add(
        types.InlineKeyboardButton(
            text='⤵️ Выгрузить аккаунты',
            callback_data='dump_accounts'
        )
    )
    accounts_kb.add(
        types.InlineKeyboardButton(
            text='⬅️ Назад',
            callback_data='move_to_main_menu'
        )
    )

    await m.edit_text(
        '<b>👥 Меню аккаунтов</b>',
        reply_markup=accounts_kb
    )


@dp.callback_query_handler(lambda call: call.data.startswith('rm_sess'), state='*')
async def rm_sess(call: types.CallbackQuery, state: FSMContext):
    _, phone = call.data.split('|')

    await close_client(
        phone=phone,
        owner_id=call.message.chat.id
    )

    await call.message.delete()
    await call.message.answer(f'Аккаунт <b>{phone}</b> был удален')


@dp.callback_query_handler(lambda call: call.data.startswith('m_account'), state='*')
async def m_account_handler(call: types.CallbackQuery, state: FSMContext):
    _, phone = call.data.split('|')

    await call.message.edit_text('<b>🕖 Подождите немного...</b>')

    r = await get_account_info(
        phone=phone,
        owner_id=call.message.chat.id
    )

    await call.message.delete()

    kb = types.InlineKeyboardMarkup()
    kb.row(
        types.InlineKeyboardButton(
            text='🎨 Аватарка',
            callback_data=f'account_edit_avatar|{phone}'
        ),
        types.InlineKeyboardButton(
            text='🖇 Описание',
            callback_data=f'account_edit_bio|{phone}'
        )
    )

    kb.row(
        types.InlineKeyboardButton(
            text='👔 Имя',
            callback_data=f'account_edit_fname|{phone}'
        ),
        types.InlineKeyboardButton(
            text='🎽 Фамилия',
            callback_data=f'account_edit_lname|{phone}'
        )
    )
    kb.row(
        types.InlineKeyboardButton(
            text='📝 Юзернейм',
            callback_data=f'account_edit_uname|{phone}'
        )
    )
    kb.row(
        types.InlineKeyboardButton(
            text='↩️ Подписать',
            callback_data=f'join_accounts|{phone}'
        ),
        types.InlineKeyboardButton(
            text='🗑 Отписать',
            callback_data=f'leave_channel_accounts|{phone}'
        )
    )
    kb.add(
        types.InlineKeyboardButton(
            text='🔒 Проверить спам блок',
            callback_data=f'check_spam|{phone}'
        )
    )
    kb.add(
        types.InlineKeyboardButton(
            text='❌ Удалить аккаунт',
            callback_data=f'rm_sess|{phone}'
        )
    )

    kb.add(
        types.InlineKeyboardButton(
            text='⬅️ Назад',
            callback_data='move_to_accounts_menu'
        )
    )

    if len(r['channels']) > 20:
        r['channels'] = r['channels'][:20]

    if r['photo']:

        await bot.send_photo(
            chat_id=call.message.chat.id,
            photo=types.InputFile(r['photo']),
            caption=f'<b>Аккаунт +{phone}</b>\n\n' +
                    f"Имя: {r['first_name']}\n" +
                    f"Фамилия: {r['last_name']}\n" +
                    f"Описание: {r['about']}\n\n" +
                    f"<b>Список каналов:</b>\n\n" +
                    '\n'.join([f'<i>{channel}</i>' for channel in r['channels']]),
            reply_markup=kb
        )

    else:

        await bot.send_message(
            chat_id=call.message.chat.id,
            text=f'<b>Аккаунт +{phone}</b>\n\n' +
                 f"Имя: {r['first_name']}\n" +
                 f"Фамилия: {r['last_name']}\n" +
                 f"Описание: {r['about']}\n\n" +
                 f"<b>Список каналов:</b>\n\n" +
                 '\n'.join([f'<i>{channel}</i>' for channel in r['channels']]),
            reply_markup=kb
        )

@dp.message_handler(commands=['admin'], state='*')
async def admin_command_handler(message: types.Message, state: FSMContext):
    if message.chat.id in ADMINS:
        await message.answer('Админ-панель', reply_markup=admin_kb)


@dp.callback_query_handler(lambda call: call.data == 'admin_add_keys' and call.message.chat.id in ADMINS, state='*')
async def admin_send_message_for_all(call: types.CallbackQuery, state: FSMContext):
    await AdminAddKeys.keys.set()

    await call.message.answer(
        '<b>Отправьте сообщение, чтобы разослать его всем пользователям, которые были авторизованы в боте</b>',
        reply_markup=cancel_kb
    )


@dp.message_handler(state=AdminAddKeys.keys)
async def admin_add_keys_keys_step_handler(message: types.Message, state: FSMContext):
    users = get_all_users()
    await state.finish()
    for user in users:
        try:
            await bot.send_message(chat_id=user["user_id"], text=message.text)
        except:
            print(user["user_id"], "error")


async def on_bot_startup_handler(*args):
    users = get_all_users()
    await run_user_tasks(users)
    print("bot_started!")


if __name__ == "__main__":
    executor.start_polling(dp, on_startup=on_bot_startup_handler)
