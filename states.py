from aiogram.dispatcher.filters.state import State, StatesGroup


class EditCommentForm(StatesGroup):
    new_content = State()

class GPTTokens(StatesGroup):
    new_tokens = State()

class AddAccountsForm(StatesGroup):

    # account_type -> ('tdata', 'session')
    account_type = State()

    # accounts_paths -> ['path/to/account']
    accounts_paths = State()

    account_phone_num = State()
    account_code = State()
    account_2fa_code = State()

class PopupBalanceForm(StatesGroup):
    summ = State()

class AccountsJoinForm(StatesGroup):
    channels = State()
    phone = State()

class SupportForm(StatesGroup):

    message = State()

class EditAccountAvatar(StatesGroup):
    photo = State()
    phone = State()

class EditAccountBio(StatesGroup):
    bio = State()
    phone = State()

class EditAccountFirstName(StatesGroup):
    fname = State()
    phone = State()

class EditAccountLastName(StatesGroup):
    lname = State()
    phone = State()

class EditAccountUsername(StatesGroup):
    username = State()
    phone = State()

class AdminAddKeys(StatesGroup):
    keys = State()