from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ChatType
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
import random

from keyboards import (
    cards_menu_keyboard, back_home_keyboard, templates_pagination_keyboard,
    country_picker_keyboard, gender_picker_keyboard
)
from services import TemplateService, RequestLogService
from states import UserStates
from utils import (
    is_bin_like_input, parse_template_input, format_expiry, 
    get_demo_profile, generate_masked_cards, format_private_card_output,
    format_group_card_output, rate_limiter, nav_stack, TEST_CARDS
)
from config import config

router = Router()

@router.callback_query(F.data == "cb_cards")
async def cards_menu(callback: CallbackQuery, state: FSMContext):
    """Show Create Credit Card menu"""
    user_id = callback.from_user.id
    
    nav_stack.push(user_id, "CARDS_MENU")
    await state.set_state(UserStates.U_CARDS_MENU)
    
    await callback.message.edit_text(
        "💳 <b>Create Credit Card</b>\n\n"
        "Choose how you'd like to generate a test card:",
        reply_markup=cards_menu_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "cb_cards_choice_admin")
async def choice_admin_card(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Show admin templates for selection"""
    user_id = callback.from_user.id
    
    # Get templates
    templates, total_pages = await TemplateService.get_paginated(session, page=0)
    
    if not templates:
        await callback.message.edit_text(
            "📂 <b>No Templates Available</b>\n\n"
            "No admin templates found. Please use 'Create Your Card Template' option.",
            reply_markup=back_home_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer()
        return
    
    template_list = [(t.id, f"{t.country} • {t.label} • {t.name}") for t in templates]
    
    nav_stack.push(user_id, "TEMPLATE_LIST")
    await state.set_state(UserStates.U_PICK_TEMPLATE)
    
    await callback.message.edit_text(
        "📂 <b>Select a Template</b>\n\n"
        "Choose a template to generate a test card:",
        reply_markup=templates_pagination_keyboard(template_list, 0, total_pages),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("cb_tpl_pick:"))
async def pick_template(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Handle template selection"""
    template_id = int(callback.data.split(":")[1])
    
    # Store template ID in state
    await state.update_data(selected_template_id=template_id)
    
    nav_stack.push(callback.from_user.id, "PICK_COUNTRY")
    await state.set_state(UserStates.U_PICK_COUNTRY)
    
    await callback.message.edit_text(
        "🌍 <b>Select Country</b>\n\n"
        "Choose a country for the card profile:",
        reply_markup=country_picker_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("cb_tpl_prev:"))
@router.callback_query(F.data.startswith("cb_tpl_next:"))
async def paginate_templates(callback: CallbackQuery, session: AsyncSession):
    """Handle template pagination"""
    action, page_str = callback.data.split(":")
    page = int(page_str)
    
    if action == "cb_tpl_prev":
        page -= 1
    else:
        page += 1
    
    templates, total_pages = await TemplateService.get_paginated(session, page=page)
    template_list = [(t.id, f"{t.country} • {t.label} • {t.name}") for t in templates]
    
    await callback.message.edit_text(
        "📂 <b>Select a Template</b>",
        reply_markup=templates_pagination_keyboard(template_list, page, total_pages),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "cb_cards_template_input")
async def template_input(callback: CallbackQuery, state: FSMContext):
    """Enter template input mode"""
    user_id = callback.from_user.id
    
    nav_stack.push(user_id, "TEMPLATE_INPUT")
    await state.set_state(UserStates.U_TEMPLATE_INPUT_WAIT)
    
    await callback.message.edit_text(
        "✍️ <b>Enter Template Key</b>\n\n"
        "Please enter a template key (e.g., <code>stripe_visa</code> or <code>template_us_01|05|2030</code>)\n\n"
        "<b>Examples:</b>\n"
        "• <code>stripe_visa</code>\n"
        "• <code>template_us_01|05|30</code>\n"
        "• <code>stripe_mastercard|12|2025</code>\n\n"
        "⚠️ <b>BIN-based generation is not supported.</b>",
        reply_markup=back_home_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(UserStates.U_TEMPLATE_INPUT_WAIT)
async def process_template_input(message: Message, state: FSMContext, session: AsyncSession):
    """Process template input from user"""
    user_id = message.from_user.id
    text = message.text.strip()
    
    # Check rate limit
    if not rate_limiter.check(user_id):
        await message.answer(
            "⏳ <b>Rate Limit Exceeded</b>\n\n"
            "Please wait a moment before trying again.",
            parse_mode="HTML"
        )
        return
    
    # Check for BIN-like input
    if is_bin_like_input(text):
        await message.answer(
            "❌ <b>Invalid Input</b>\n\n"
            "BIN-based generation is not supported. Please use a template key "
            "(e.g., <code>stripe_visa</code>) or choose from Admin Card List.",
            parse_mode="HTML"
        )
        return
    
    # Parse input
    key, month, year = parse_template_input(text)
    
    # Check if it's a known test card
    if key in TEST_CARDS:
        card_number = TEST_CARDS[key]
        template_name = key.replace("_", " ").title()
    else:
        # Check database for template
        template = await TemplateService.get_by_key(session, key)
        if template:
            card_number = template.display_card
            template_name = template.name
            if not month or not year:
                exp_parts = template.default_exp.split('/')
                if len(exp_parts) == 2:
                    month, year = exp_parts
        else:
            await message.answer(
                f"❌ <b>Template Not Found</b>\n\n"
                f"Template key '{key}' not found. Please check and try again.",
                parse_mode="HTML"
            )
            return
    
    # Set expiry
    if month and year:
        expiry = format_expiry(month, year)
    else:
        # Default expiry
        expiry = "05/30"
        month, year = "05", "2030"
    
    # Set CVV
    cvv = "123"
    
    # Store in state for next step
    await state.update_data(
        card_number=card_number,
        expiry=expiry,
        cvv=cvv,
        template_name=template_name,
        month=month,
        year=year
    )
    
    nav_stack.push(user_id, "PICK_COUNTRY")
    await state.set_state(UserStates.U_PICK_COUNTRY)
    
    await message.answer(
        "🌍 <b>Select Country</b>\n\n"
        "Choose a country for the card profile:",
        reply_markup=country_picker_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("cb_country_pick:"))
async def pick_country(callback: CallbackQuery, state: FSMContext):
    """Handle country selection"""
    country_code = callback.data.split(":")[1]
    
    await state.update_data(selected_country=country_code)
    
    nav_stack.push(callback.from_user.id, "PICK_GENDER")
    await state.set_state(UserStates.U_PICK_GENDER)
    
    await callback.message.edit_text(
        "👤 <b>Select Gender</b>\n\n"
        "Choose a gender for the profile:",
        reply_markup=gender_picker_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "cb_country_text")
async def country_text_input(callback: CallbackQuery, state: FSMContext):
    """Handle text input for country"""
    await state.set_state(UserStates.U_INFO_COUNTRY_WAIT)
    
    await callback.message.edit_text(
        "🌍 <b>Type Country</b>\n\n"
        "Please type the country name (e.g., United States, UK, Canada):",
        reply_markup=back_home_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("cb_gender_"))
async def pick_gender(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Handle gender selection and generate card"""
    gender = callback.data.replace("cb_gender_", "")
    
    user_id = callback.from_user.id
    is_private = callback.message.chat.type == "private"
    
    # Get data from state
    data = await state.get_data()
    country_code = data.get("selected_country", "US")
    card_number = data.get("card_number", "4242 4242 4242 4242")
    expiry = data.get("expiry", "05/30")
    cvv = data.get("cvv", "123")
    template_name = data.get("template_name", "Test Card")
    
    # Log request
    await RequestLogService.log(session, user_id, "generate_card")
    
    # Generate profile
    profile = get_demo_profile(country_code, gender)
    
    # Check if in group
    if is_private:
        # Private chat - full output
        output_text = format_private_card_output(card_number, expiry, cvv, profile)
        
        # Send image + text
        await callback.message.answer_photo(
            photo=config.IMAGE_URL,
            caption=output_text,
            parse_mode="HTML"
        )
    else:
        # Group chat - masked list only
        masked_cards = generate_masked_cards(3)  # Generate 3 masked cards
        output_text = format_group_card_output(template_name, masked_cards)
        
        # Send image with caption only
        await callback.message.answer_photo(
            photo=config.IMAGE_URL,
            caption=output_text,
            parse_mode="HTML"
        )
    
    # Return to cards menu
    nav_stack.clear(user_id)
    nav_stack.push(user_id, "CARDS_MENU")
    await state.set_state(UserStates.U_CARDS_MENU)
    
    await callback.message.answer(
        "💳 <b>Create Credit Card</b>\n\n"
        "Choose an option to generate another card:",
        reply_markup=cards_menu_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()
