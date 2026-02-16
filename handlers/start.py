from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ChatType
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from keyboards import main_menu_keyboard, back_home_keyboard
from services import UserService, GroupService
from states import UserStates
from utils import nav_stack
from config import config

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, session: AsyncSession):
    """Handle /start command"""
    user_id = message.from_user.id
    username = message.from_user.username
    
    # Save user to DB
    await UserService.get_or_create(session, user_id, username)
    
    # Save group if in group
    if message.chat.type in ["group", "supergroup"]:
        await GroupService.get_or_create(session, message.chat.id, message.chat.title)
    
    # Clear navigation stack
    nav_stack.clear(user_id)
    nav_stack.push(user_id, "MAIN_MENU")
    
    # Set state
    await state.set_state(UserStates.U_MAIN)
    
    # Check if admin
    is_admin = (user_id == config.ADMIN_ID)
    
    # Send welcome message
    welcome_text = (
        "👋 <b>Welcome to Credit Card Generator Bot</b>\n\n"
        "This bot provides test payment cards for development and testing purposes only.\n"
        "⚠️ <b>DO NOT use these for real payments</b> - they are for demo/testing only.\n\n"
        "Please select an option from the menu below:"
    )
    
    await message.answer(
        welcome_text,
        reply_markup=main_menu_keyboard(is_admin),
        parse_mode="HTML"
    )

@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command"""
    help_text = (
        "ℹ️ <b>Help & Information</b>\n\n"
        "This bot provides test payment cards for development purposes only.\n\n"
        "<b>Features:</b>\n"
        "• 💳 Create test credit cards (demo only)\n"
        "• 🧪 Generate fake profile information\n"
        "• 🔒 Admin panel (admin only)\n\n"
        "<b>Important:</b>\n"
        "• All cards are TEST cards or masked placeholders\n"
        "• Cannot be used for real payments\n"
        "• No real personal information is stored\n\n"
        "Use the menu buttons to navigate."
    )
    
    await message.answer(help_text, parse_mode="HTML")

@router.callback_query(F.data == "cb_home")
async def go_home(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Handle Home button - return to main menu"""
    user_id = callback.from_user.id
    
    # Clear navigation stack
    nav_stack.clear(user_id)
    nav_stack.push(user_id, "MAIN_MENU")
    
    # Set state
    await state.set_state(UserStates.U_MAIN)
    
    # Check if admin
    is_admin = (user_id == config.ADMIN_ID)
    
    # Edit message or send new one
    try:
        await callback.message.edit_text(
            "🏠 <b>Main Menu</b>\n\nSelect an option:",
            reply_markup=main_menu_keyboard(is_admin),
            parse_mode="HTML"
        )
    except:
        await callback.message.answer(
            "🏠 <b>Main Menu</b>\n\nSelect an option:",
            reply_markup=main_menu_keyboard(is_admin),
            parse_mode="HTML"
        )
    
    await callback.answer()

@router.callback_query(F.data == "cb_back")
async def go_back(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Handle Back button - return to previous screen"""
    user_id = callback.from_user.id
    
    # Get previous screen
    prev_screen = nav_stack.back(user_id)
    
    # Route to appropriate handler based on previous screen
    if prev
