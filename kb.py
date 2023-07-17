from aiogram import types


start_reply_kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
start_reply_kb.add(
    '🏘 Главное меню'
)

accounts_edit_kb = types.InlineKeyboardMarkup()
accounts_edit_kb.add(
    types.InlineKeyboardButton(
        text='🎨 Редактировать аватарку',
        callback_data='account_edit_avatar'
    )
)
accounts_edit_kb.add(
    types.InlineKeyboardButton(
        text='🖇 Редактировать описание',
        callback_data='account_edit_bio'
    )
)
accounts_edit_kb.add(
    types.InlineKeyboardButton(
        text='Редактировать Имя',
        callback_data='account_edit_fname'
    )
)
accounts_edit_kb.add(
    types.InlineKeyboardButton(
        text='Редактировать Фамилию',
        callback_data='account_edit_lname'
    )
)

append_accounts_independ_kb = types.InlineKeyboardMarkup()
append_accounts_independ_kb.add(
    types.InlineKeyboardButton(
        text='⤴️ Добавить аккаунты',
        callback_data='append_accounts'
    )
)

accounts_manage_kb = types.InlineKeyboardMarkup()
accounts_manage_kb.row(
    types.InlineKeyboardButton(
        text='⤴️ Добавить аккаунты',
        callback_data='append_accounts'
    )
)
accounts_manage_kb.add(
    types.InlineKeyboardButton(
        text='⤵️ Выгрузить аккаунты',
        callback_data='dump_accounts'
    )
)

gpt_tokens_kb = types.InlineKeyboardMarkup()

gpt_tokens_kb.add(
    types.InlineKeyboardButton(
        text='Добавить',
        callback_data="add_gpt_tokens"
    )
)
gpt_tokens_kb.add(
        types.InlineKeyboardButton(
            text='⬅️ Назад',
            callback_data='move_to_main_menu'
        )
    )
start_kb = types.InlineKeyboardMarkup()

start_kb.add(
    types.InlineKeyboardButton(
        text='👥 Аккаунты',
        callback_data='move_to_accounts_menu'
    )
)
start_kb.add(
    types.InlineKeyboardButton(
        text='Токены GPT',
        callback_data='move_to_accounts_gpt_menu'
    )
)
start_kb.add(
    types.InlineKeyboardButton(
        text='🪪 Подписка',
        callback_data='my_sub'
    )
)
start_kb.add(
    types.InlineKeyboardButton(
        text='💬 Поддержка',
        callback_data='support'
    )
)
start_kb.add(
    types.InlineKeyboardButton(
        text='🔗 Реферальная ссылка',
        callback_data='my_referal_link'
    )
)
start_kb.add(
    types.InlineKeyboardButton(
        text='📄 Инструкция',
        url='https://teletype.in/@akaevskaya/rEE9u_rmt6o'
    )
)

cancel_btn = types.InlineKeyboardButton(
    text='Отмена',
    callback_data='cancel'
)
cancel_kb = types.InlineKeyboardMarkup()
cancel_kb.add(cancel_btn)

accounts_type_kb = types.InlineKeyboardMarkup()
# accounts_type_kb.add(
#     types.InlineKeyboardButton(
#         text='💻 TData',
#         callback_data='account_type_choice|tdata'
#     )
# )
accounts_type_kb.add(
    types.InlineKeyboardButton(
        text='🈁 Session',
        callback_data='account_type_choice|session'
    )
)
accounts_type_kb.add(
    types.InlineKeyboardButton(
        text='🔤 Через код',
        callback_data='account_type_choice|via_code'
    )
)

accounts_dump_kb = types.InlineKeyboardMarkup()
# accounts_dump_kb.add(
#     types.InlineKeyboardButton(
#         text='💻 Выгрузить TDATA',
#         callback_data='dump_tdata'
#     )
# )
accounts_dump_kb.add(
    types.InlineKeyboardButton(
        text='🈁 Выгрузить Session',
        callback_data='dump_session'
    )
)

payment_kb = types.InlineKeyboardMarkup()
payment_kb.add(
    types.InlineKeyboardButton(
        text='💳 Пополнить баланс',
        callback_data='popup_balance'
    )
)
payment_kb.add(
    types.InlineKeyboardButton(
        text='📂 Подписка и тарифы',
        callback_data='sub_menu'
    )
)


code_input_kb = [
    [
        types.InlineKeyboardButton("1", callback_data='1'),
        types.InlineKeyboardButton("2", callback_data='2'),
        types.InlineKeyboardButton("3", callback_data='3'),
    ],
    [
        types.InlineKeyboardButton("4", callback_data='4'),
        types.InlineKeyboardButton("5", callback_data='5'),
        types.InlineKeyboardButton("6", callback_data='6'),
    ],
    [
        types.InlineKeyboardButton("7", callback_data='7'),
        types.InlineKeyboardButton("8", callback_data='8'),
        types.InlineKeyboardButton("9", callback_data='9'),
    ],
    [
        types.InlineKeyboardButton("⬅️", callback_data='delete'),
        types.InlineKeyboardButton("0", callback_data='0'),
        types.InlineKeyboardButton("✅", callback_data='confirm'),
    ]
]

code_input_kb = types.InlineKeyboardMarkup(inline_keyboard=code_input_kb)




admin_kb = types.InlineKeyboardMarkup()
# admin_kb.add(
#     types.InlineKeyboardButton(
#         text='Рассылка',
#         callback_data='admin_spam'
#     )
# )
# admin_kb.add(
#     types.InlineKeyboardButton(
#         text='Статистика',
#         callback_data='admin_stats'
#     )
# )
admin_kb.add(
    types.InlineKeyboardButton(
        text='Разослать сообщение',
        callback_data='admin_add_keys'
    )
)