from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from keyboards import info_menu_keyboard, country_picker_keyboard, gender_picker_keyboard, back_home_keyboard
from services import RequestLogService
from states import UserStates
from utils import get_demo_profile, format_profile_output, rate_limiter, nav_stack

router = Router()

@router.callback_query(F.data == "cb_info")
async def info_menu(callback: CallbackQuery, state: FSMContext):
    """Show Create Card Info menu"""
    user_id = callback.from_user.id
    
    nav_stack.push(user_id, "INFO_MENU")
    await state.set_state(UserStates.U_INFO_MENU)
    
    await callback.message.edit_text(
        "🧾 <b>Create Card Info</b>\n\n"
        "Choose what information you'd like to generate:",
        reply_markup=info_menu_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "cb_info_country")
async def info_country(callback: CallbackQuery, state: FSMContext):
    """Start country info flow"""
    user_id = callback.from_user.id
    
    nav_stack.push(user_id, "INFO_COUNTRY")
    await state.set_state(UserStates.U_INFO_COUNTRY_WAIT)
    
    await callback.message.edit_text(
        "🌍 <b>Card Country Info</b>\n\n"
        "Select a country for the profile:",
        reply_markup=country_picker_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "cb_info_profile")
async def info_profile(callback: CallbackQuery, state: FSMContext):
    """Start fake profile info flow (country optional)"""
    user_id = callback.from_user.id
    
    nav_stack.push(user_id, "INFO_COUNTRY")
    await state.set_state(UserStates.U_INFO_COUNTRY_WAIT)
    
    await callback.message.edit_text(
        "🪪 <b>Create Fake Profile Info</b>\n\n"
        "Select a country (or type any country):",
        reply_markup=country_picker_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("cb_country_pick:"))
async def info_pick_country(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Handle country selection for info"""
    country_code = callback.data.split(":")[1]
    
    await state.update_data(selected_country=country_code)
    
    nav_stack.push(callback.from_user.id, "INFO_GENDER")
    await state.set_state(UserStates.U_INFO_GENDER_WAIT)
    
    await callback.message.edit_text(
        "👤 <b>Select Gender</b>\n\n"
        "Choose a gender for the profile:",
        reply_markup=gender_picker_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(UserStates.U_INFO_COUNTRY_WAIT)
async def info_country_text(message: Message, state: FSMContext):
    """Handle text input for country"""
    country_text = message.text.strip()
    
    # Simple mapping - in production, use a proper country mapping service
    country_map = {
        "united states": "US", "usa": "US", "us": "US",
        "united kingdom": "UK", "uk": "UK", "england": "UK",
        "canada": "CA", "can": "CA",
        "australia": "AU", "aus": "AU",
        "germany": "DE", "ger": "DE",
        "france": "FR", "fra": "FR",
        "japan": "JP", "jpn": "JP",
        "italy": "IT", "ita": "IT",
        "spain": "ES", "esp": "ES",
        "brazil": "BR", "bra": "BR",
        "india": "IN", "ind": "IN",
    }
    
    country_code = country_map.get(country_text.lower(), "US")
    await state.update_data(selected_country=country_code)
    
    nav_stack.push(message.from_user.id, "INFO_GENDER")
    await state.set_state(UserStates.U_INFO_GENDER_WAIT)
    
    await message.answer(
        "👤 <b>Select Gender</b>\n\n"
        "Choose a gender for the profile:",
        reply_markup=gender_picker_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("cb_gender_"), UserStates.U_INFO_GENDER_WAIT)
async def info_pick_gender(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Handle gender selection and generate profile"""
    gender = callback.data.replace("cb_gender_", "")
    
    user_id = callback.from_user.id
    
    # Check rate limit
    if not rate_limiter.check(user_id):
        await callback.message.edit_text(
            "⏳ <b>Rate Limit Exceeded</b>\n\n"
            "Please wait a moment before trying again.",
            reply_markup=back_home_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer()
        return
    
    # Get country from state
    data = await state.get_data()
    country_code = data.get("selected_country", "US")
    
    # Log request
    await RequestLogService.log(session, user_id, "generate_profile")
    
    # Generate profile
    profile = get_demo_profile(country_code, gender)
    
    # Format output
    output_text = format_profile_output(profile)
    
    # Send profile info
    await callback.message.edit_text(
        output_text,
        parse_mode="HTML"
    )
    
    # Return to info menu
    nav_stack.clear(user_id)
    nav_stack.push(user_id, "INFO_MENU")
    await state.set_state(UserStates.U_INFO_MENU)
    
    await callback.message.answer(
        "🧾 <b>Create Card Info</b>\n\n"
        "Choose an option to generate more information:",
        reply_markup=info_menu_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()
