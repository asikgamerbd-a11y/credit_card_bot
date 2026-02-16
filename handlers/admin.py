from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ChatType
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
import datetime

from keyboards import (
    admin_menu_keyboard, back_home_keyboard, confirm_keyboard,
    admin_templates_keyboard, broadcast_mode_keyboard
)
from services import (
    TemplateService, UserService, GroupService, 
    BroadcastService, RequestLogService
)
from states import AdminStates, UserStates
from utils import nav_stack, is_bin_like_input
from config import config

router = Router()

# Admin check filter
async def admin_only(message: Message | CallbackQuery) -> bool:
    user_id = message.from_user.id if isinstance(message, Message) else message.from_user.id
    return user_id == config.ADMIN_ID

@router.callback_query(F.data == "cb_admin")
async def admin_panel(callback: CallbackQuery, state: FSMContext):
    """Show Admin Panel menu"""
    user_id = callback.from_user.id
    
    # Check if admin
    if user_id != config.ADMIN_ID:
        await callback.answer("⛔ Access denied", show_alert=True)
        return
    
    nav_stack.push(user_id, "ADMIN_MENU")
    await state.set_state(AdminStates.A_ADMIN_MENU)
    
    await callback.message.edit_text(
        "🔒 <b>Admin Panel</b>\n\n"
        "Select an option:",
        reply_markup=admin_menu_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

# ========== Add Template Wizard ==========

@router.callback_query(F.data == "cb_admin_add")
async def admin_add_start(callback: CallbackQuery, state: FSMContext):
    """Start add template wizard"""
    user_id = callback.from_user.id
    if user_id != config.ADMIN_ID:
        await callback.answer("⛔ Access denied", show_alert=True)
        return
    
    await state.set_state(AdminStates.A_ADD_NAME)
    await state.update_data(template_data={})
    
    await callback.message.edit_text(
        "➕ <b>Add Card Template - Step 1/7</b>\n\n"
        "Enter template name (display name):",
        reply_markup=back_home_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(AdminStates.A_ADD_NAME)
async def admin_add_name(message: Message, state: FSMContext):
    """Get template name"""
    if message.from_user.id != config.ADMIN_ID:
        return
    
    await state.update_data(template_data={"name": message.text})
    await state.set_state(AdminStates.A_ADD_COUNTRY)
    
    await message.answer(
        "➕ <b>Step 2/7 - Enter Country</b>\n\n"
        "Enter country code (e.g., US, UK, CA):",
        reply_markup=back_home_keyboard(),
        parse_mode="HTML"
    )

@router.message(AdminStates.A_ADD_COUNTRY)
async def admin_add_country(message: Message, state: FSMContext):
    """Get country"""
    if message.from_user.id != config.ADMIN_ID:
        return
    
    data = await state.get_data()
    data["template_data"]["country"] = message.text.upper()
    await state.update_data(data)
    await state.set_state(AdminStates.A_ADD_LABEL)
    
    await message.answer(
        "➕ <b>Step 3/7 - Enter Service/Brand Label</b>\n\n"
        "Enter label (e.g., MasterCard Premium, Visa Classic):",
        reply_markup=back_home_keyboard(),
        parse_mode="HTML"
    )

@router.message(AdminStates.A_ADD_LABEL)
async def admin_add_label(message: Message, state: FSMContext):
    """Get label"""
    if message.from_user.id != config.ADMIN_ID:
        return
    
    data = await state.get_data()
    data["template_data"]["label"] = message.text
    await state.update_data(data)
    await state.set_state(AdminStates.A_ADD_KEY)
    
    await message.answer(
        "➕ <b>Step 4/7 - Enter Template Key</b>\n\n"
        "Enter unique template key (e.g., template_us_01):",
        reply_markup=back_home_keyboard(),
        parse_mode="HTML"
    )

@router.message(AdminStates.A_ADD_KEY)
async def admin_add_key(message: Message, state: FSMContext, session: AsyncSession):
    """Get template key"""
    if message.from_user.id != config.ADMIN_ID:
        return
    
    key = message.text.strip()
    
    # Check if key exists
    existing = await TemplateService.get_by_key(session, key)
    if existing:
        await message.answer(
            "❌ <b>Template Key Already Exists</b>\n\n"
            "This key is already in use. Please choose another:",
            parse_mode="HTML"
        )
        return
    
    data = await state.get_data()
    data["template_data"]["template_key"] = key
    await state.update_data(data)
    await state.set_state(AdminStates.A_ADD_DISPLAY_CARD)
    
    await message.answer(
        "➕ <b>Step 5/7 - Enter Display Card</b>\n\n"
        "Enter card number to display (must be test card or masked):\n"
        "• Test card: 4242 4242 4242 4242\n"
        "• Masked: 4242XXXXXXXX4242\n\n"
        "⚠️ <b>No real card numbers allowed!</b>",
        reply_markup=back_home_keyboard(),
        parse_mode="HTML"
    )

@router.message(AdminStates.A_ADD_DISPLAY_CARD)
async def admin_add_display_card(message: Message, state: FSMContext):
    """Get display card"""
    if message.from_user.id != config.ADMIN_ID:
        return
    
    card = message.text.strip()
    
    # Basic validation - warn if looks like real card
    digits_only = ''.join(filter(str.isdigit, card))
    if len(digits_only) == 16 and not any(test in card for test in ["4242", "5555", "3782", "6011"]):
        await message.answer(
            "⚠️ <b>Warning: This looks like a real card number!</b>\n\n"
            "Please use only test cards or masked placeholders.\n"
            "Continue anyway? (Yes/No)",
            reply_markup=confirm_keyboard("continue_card"),
            parse_mode="HTML"
        )
        return
    
    data = await state.get_data()
    data["template_data"]["display_card"] = card
    await state.update_data(data)
    await state.set_state(AdminStates.A_ADD_EXP)
    
    await message.answer(
        "➕ <b>Step 6/7 - Enter Default Expiry</b>\n\n"
        "Enter default expiry (MM/YYYY, e.g., 05/2030):",
        reply_markup=back_home_keyboard(),
        parse_mode="HTML"
    )

@router.message(AdminStates.A_ADD_EXP)
async def admin_add_exp(message: Message, state: FSMContext):
    """Get default expiry"""
    if message.from_user.id != config.ADMIN_ID:
        return
    
    exp = message.text.strip()
    if '/' not in exp:
        await message.answer(
            "❌ Invalid format. Please use MM/YYYY format:",
            parse_mode="HTML"
        )
        return
    
    data = await state.get_data()
    data["template_data"]["default_exp"] = exp
    await state.update_data(data)
    await state.set_state(AdminStates.A_ADD_CVV)
    
    await message.answer(
        "➕ <b>Step 7/7 - Enter Default CVV</b>\n\n"
        "Enter default CVV (e.g., 123):",
        reply_markup=back_home_keyboard(),
        parse_mode="HTML"
    )

@router.message(AdminStates.A_ADD_CVV)
async def admin_add_cvv(message: Message, state: FSMContext):
    """Get default CVV"""
    if message.from_user.id != config.ADMIN_ID:
        return
    
    cvv = message.text.strip()
    if not cvv.isdigit() or len(cvv) not in [3, 4]:
        await message.answer(
            "❌ Invalid CVV. Please enter 3 or 4 digits:",
            parse_mode="HTML"
        )
        return
    
    data = await state.get_data()
    data["template_data"]["default_cvv"] = cvv
    await state.update_data(data)
    
    # Show confirmation
    tpl = data["template_data"]
    summary = (
        f"📋 <b>Template Summary</b>\n\n"
        f"<b>Name:</b> {tpl['name']}\n"
        f"<b>Country:</b> {tpl['country']}\n"
        f"<b>Label:</b> {tpl['label']}\n"
        f"<b>Key:</b> {tpl['template_key']}\n"
        f"<b>Card:</b> {tpl['display_card']}\n"
        f"<b>Expiry:</b> {tpl['default_exp']}\n"
        f"<b>CVV:</b> {tpl['default_cvv']}\n\n"
        f"Save this template?"
    )
    
    await state.set_state(AdminStates.A_ADD_CONFIRM)
    
    await message.answer(
        summary,
        reply_markup=confirm_keyboard("save_template"),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "cb_save_template_yes")
async def admin_save_template(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Save template to database"""
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("⛔ Access denied", show_alert=True)
        return
    
    data = await state.get_data()
    template_data = data["template_data"]
    
    # Save to DB
    await TemplateService.create(session, template_data)
    
    await state.set_state(AdminStates.A_ADMIN_MENU)
    
    await callback.message.edit_text(
        "✅ <b>Template Saved Successfully!</b>",
        reply_markup=admin_menu_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "cb_save_template_no")
async def admin_cancel_save(callback: CallbackQuery, state: FSMContext):
    """Cancel template save"""
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("⛔ Access denied", show_alert=True)
        return
    
    await state.set_state(AdminStates.A_ADMIN_MENU)
    
    await callback.message.edit_text(
        "❌ Template creation cancelled.",
        reply_markup=admin_menu_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

# ========== Delete Template ==========

@router.callback_query(F.data == "cb_admin_del_list")
async def admin_delete_list(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Show templates for deletion"""
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("⛔ Access denied", show_alert=True)
        return
    
    templates, total_pages = await TemplateService.get_paginated(session, page=0)
    
    if not templates:
        await callback.message.edit_text(
            "📋 <b>No Templates Found</b>",
            reply_markup=admin_menu_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer()
        return
    
    template_list = [(t.id, t.name) for t in templates]
    
    await callback.message.edit_text(
        "❌ <b>Delete Template</b>\n\n"
        "Select a template to delete:",
        reply_markup=admin_templates_keyboard(template_list, 0, total_pages, for_delete=True),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("cb_admin_tpl_del:"))
async def admin_confirm_delete(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Confirm template deletion"""
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("⛔ Access denied", show_alert=True)
        return
    
    template_id = int(callback.data.split(":")[1])
    template = await TemplateService.get_by_id(session, template_id)
    
    if not template:
        await callback.message.edit_text(
            "❌ Template not found.",
            reply_markup=admin_menu_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer()
        return
    
    await state.update_data(delete_template_id=template_id)
    
    await callback.message.edit_text(
        f"❓ <b>Confirm Delete</b>\n\n"
        f"Are you sure you want to delete template:\n"
        f"<b>{template.name}</b> ({template.template_key})?",
        reply_markup=confirm_keyboard("confirm_delete"),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "cb_confirm_delete_yes")
async def admin_execute_delete(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Execute template deletion"""
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("⛔ Access denied", show_alert=True)
        return
    
    data = await state.get_data()
    template_id = data.get("delete_template_id")
    
    if template_id:
        await TemplateService.delete(session, template_id)
    
    await state.set_state(AdminStates.A_ADMIN_MENU)
    
    await callback.message.edit_text(
        "✅ <b>Template Deleted Successfully!</b>",
        reply_markup=admin_menu_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "cb_confirm_delete_no")
async def admin_cancel_delete(callback: CallbackQuery, state: FSMContext):
    """Cancel deletion"""
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("⛔ Access denied", show_alert=True)
        return
    
    await state.set_state(AdminStates.A_ADMIN_MENU)
    
    await callback.message.edit_text(
        "❌ Deletion cancelled.",
        reply_markup=admin_menu_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

# ========== Template List ==========

@router.callback_query(F.data == "cb_admin_list_tpl")
async def admin_list_templates(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Show template list"""
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("⛔ Access denied", show_alert=True)
        return
    
    templates, total_pages = await TemplateService.get_paginated(session, page=0)
    
    if not templates:
        await callback.message.edit_text(
            "📋 <b>No Templates Found</b>",
            reply_markup=admin_menu_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer()
        return
    
    template_list = [(t.id, f"{t.country} • {t.label} • {t.name}") for t in templates]
    
    await callback.message.edit_text(
        "📋 <b>Template List</b>",
        reply_markup=admin_templates_keyboard(template_list, 0, total_pages, for_delete=False),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("cb_admin_tpl_prev:"))
@router.callback_query(F.data.startswith("cb_admin_tpl_next:"))
async def admin_paginate_templates(callback: CallbackQuery, session: AsyncSession):
    """Handle template pagination"""
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("⛔ Access denied", show_alert=True)
        return
    
    action, page_str = callback.data.split(":")
    page = int(page_str)
    
    if action == "cb_admin_tpl_prev":
        page -= 1
    else:
        page += 1
    
    templates, total_pages = await TemplateService.get_paginated(session, page=page)
    template_list = [(t.id, f"{t.country} • {t.label} • {t.name}") for t in templates]
    
    await callback.message.edit_text(
        "📋 <b>Template List</b>",
        reply_markup=admin_templates_keyboard(template_list, page, total_pages, for_delete=False),
        parse_mode="HTML"
    )
    await callback.answer()

# ========== Broadcast ==========

@router.callback_query(F.data == "cb_admin_broadcast")
async def admin_broadcast(callback: CallbackQuery, state: FSMContext):
    """Start broadcast process"""
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("⛔ Access denied", show_alert=True)
        return
    
    await state.set_state(AdminStates.A_BC_MODE_PICK)
    
    await callback.message.edit_text(
        "📢 <b>Broadcast</b>\n\n"
        "Choose broadcast mode:",
        reply_markup=broadcast_mode_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "cb_bc_text")
async def admin_broadcast_text(callback: CallbackQuery, state: FSMContext):
    """Text broadcast mode"""
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("⛔ Access denied", show_alert=True)
        return
    
    await state.set_state(AdminStates.A_BC_TEXT_WAIT)
    await state.update_data(broadcast_mode="text")
    
    await callback.message.edit_text(
        "📢 <b>Send Broadcast Text</b>\n\n"
        "Please send the message you want to broadcast:",
        reply_markup=back_home_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "cb_bc_forward")
async def admin_broadcast_forward(callback: CallbackQuery, state: FSMContext):
    """Forward broadcast mode"""
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("⛔ Access denied", show_alert=True)
        return
    
    await state.set_state(AdminStates.A_BC_FORWARD_WAIT)
    await state.update_data(broadcast_mode="forward")
    
    await callback.message.edit_text(
        "📢 <b>Forward Message</b>\n\n"
        "Please forward a message to broadcast:",
        reply_markup=back_home_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(AdminStates.A_BC_TEXT_WAIT)
async def admin_execute_text_broadcast(message: Message, state: FSMContext, session: AsyncSession, bot):
    """Execute text broadcast"""
    if message.from_user.id != config.ADMIN_ID:
        return
    
    users = await UserService.get_all_users(session)
    
    broadcast = await BroadcastService.create_log(
        session, 
        message.from_user.id, 
        "text"
    )
    
    success = 0
    fail = 0
    
    status_msg = await message.answer("📢 Broadcasting... 0%")
    
    for i, user in enumerate(users):
        try:
            await bot.send_message(
                user.id,
                message.text,
                parse_mode="HTML"
            )
            success += 1
        except Exception as e:
            fail += 1
        
        # Update status every 10 users
        if i % 10 == 0:
            progress = int((i + 1) / len(users) * 100)
            await status_msg.edit_text(f"📢 Broadcasting... {progress}%")
    
    await BroadcastService.update_stats(session, broadcast.id, success, fail)
    
    await state.set_state(AdminStates.A_ADMIN_MENU)
    
    await status_msg.edit_text(
        f"✅ <b>Broadcast Complete</b>\n\n"
        f"✅ Success: {success}\n"
        f"❌ Failed: {fail}",
        parse_mode="HTML"
    )
    
    await message.answer(
        "🔒 <b>Admin Panel</b>",
        reply_markup=admin_menu_keyboard(),
        parse_mode="HTML"
    )

@router.message(AdminStates.A_BC_FORWARD_WAIT, F.forward_date)
async def admin_execute_forward_broadcast(message: Message, state: FSMContext, session: AsyncSession, bot):
    """Execute forward broadcast"""
    if message.from_user.id != config.ADMIN_ID:
        return
    
    users = await UserService.get_all_users(session)
    
    broadcast = await BroadcastService.create_log(
        session, 
        message.from_user.id, 
        "forward"
    )
    
    success = 0
    fail = 0
    
    status_msg = await message.answer("📢 Broadcasting forwarded message... 0%")
    
    for i, user in enumerate(users):
        try:
            await bot.forward_message(
                chat_id=user.id,
                from_chat_id=message.chat.id,
                message_id=message.message_id
            )
            success += 1
        except Exception as e:
            fail += 1
        
        # Update status every 10 users
        if i % 10 == 0:
            progress = int((i + 1) / len(users) * 100)
            await status_msg.edit_text(f"📢 Broadcasting... {progress}%")
    
    await BroadcastService.update_stats(session, broadcast.id, success, fail)
    
    await state.set_state(AdminStates.A_ADMIN_MENU)
    
    await status_msg.edit_text(
        f"✅ <b>Broadcast Complete</b>\n\n"
        f"✅ Success: {success}\n"
        f"❌ Failed: {fail}",
        parse_mode="HTML"
    )
    
    await message.answer(
        "🔒 <b>Admin Panel</b>",
        reply_markup=admin_menu_keyboard(),
        parse_mode="HTML"
    )

# ========== Stats ==========

@router.callback_query(F.data == "cb_admin_stats")
async def admin_stats(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Show statistics"""
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("⛔ Access denied", show_alert=True)
        return
    
    # Gather stats
    total_users = await UserService.count_users(session)
    total_groups = await GroupService.count_groups(session)
    templates = await TemplateService.get_all(session)
    total_templates = len(templates)
    today_requests = await RequestLogService.count_today(session)
    
    # Get bot uptime (simplified - you'd store start time in app)
    uptime = "N/A"  # You can implement this
    
    stats_text = (
        f"📊 <b>Bot Statistics</b>\n\n"
        f"👥 <b>Total Users:</b> {total_users}\n"
        f"👥 <b>Total Groups:</b> {total_groups}\n"
        f"📋 <b>Total Templates:</b> {total_templates}\n"
        f"📝 <b>Today's Requests:</b> {today_requests}\n"
        f"⏱️ <b>Uptime:</b> {uptime}\n\n"
        f"🕐 <b>Last Updated:</b> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    
    await callback.message.edit_text(
        stats_text,
        reply_markup=admin_menu_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

# ========== Country Labels ==========

@router.callback_query(F.data == "cb_admin_country_labels")
async def admin_country_labels(callback: CallbackQuery, state: FSMContext):
    """Placeholder for country labels feature"""
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("⛔ Access denied", show_alert=True)
        return
    
    await callback.message.edit_text(
        "💾 <b>Save Country + Service Labels</b>\n\n"
        "This feature is under development.\n\n"
        "It will allow you to map countries to available service labels.",
        reply_markup=admin_menu_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()
