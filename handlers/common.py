from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from keyboards import back_home_keyboard

router = Router()

@router.message()
async def handle_unknown(message: Message, state: FSMContext, session: AsyncSession):
    """Handle unknown messages"""
    current_state = await state.get_state()
    
    if current_state:
        # If in a state, state handlers should have caught this
        await message.answer(
            "❓ <b>Unexpected Input</b>\n\n"
            "Please use the buttons to navigate.",
            reply_markup=back_home_keyboard(),
            parse_mode="HTML"
        )
    else:
        # Not in any state, show main menu
        from handlers.start import cmd_start
        await cmd_start(message, state, session)

@router.callback_query()
async def handle_unknown_callback(callback: CallbackQuery, state: FSMContext):
    """Handle unknown callbacks"""
    await callback.answer("This button is not available right now.", show_alert=True)
