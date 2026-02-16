from aiogram.fsm.state import State, StatesGroup

class UserStates(StatesGroup):
    # User states
    U_IDLE = State()
    U_MAIN = State()
    U_CARDS_MENU = State()
    U_PICK_TEMPLATE = State()
    U_TEMPLATE_INPUT_WAIT = State()
    U_PICK_COUNTRY = State()
    U_PICK_GENDER = State()
    U_SHOW_CARD_RESULT = State()
    U_INFO_MENU = State()
    U_INFO_COUNTRY_WAIT = State()
    U_INFO_GENDER_WAIT = State()
    U_INFO_RESULT = State()

class AdminStates(StatesGroup):
    # Admin states
    A_ADMIN_MENU = State()
    A_ADD_NAME = State()
    A_ADD_COUNTRY = State()
    A_ADD_LABEL = State()
    A_ADD_KEY = State()
    A_ADD_DISPLAY_CARD = State()
    A_ADD_EXP = State()
    A_ADD_CVV = State()
    A_ADD_CONFIRM = State()
    A_BC_MODE_PICK = State()
    A_BC_TEXT_WAIT = State()
    A_BC_FORWARD_WAIT = State()
