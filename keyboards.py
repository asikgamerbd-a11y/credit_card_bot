from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Optional, Tuple

from config import config
from utils import TOP_COUNTRIES, GENDERS

def main_menu_keyboard(is_admin: bool = False) -> InlineKeyboardMarkup:
    """Main menu keyboard with 3 buttons"""
    builder = InlineKeyboardBuilder()
    
    builder.row(InlineKeyboardButton(text="💳 Create Credit Card", callback_data="cb_cards"))
    builder.row(InlineKeyboardButton(text="🧾 Create Card Info", callback_data="cb_info"))
    
    if is_admin:
        builder.row(InlineKeyboardButton(text="🔒 Admin Panel", callback_data="cb_admin"))
    
    return builder.as_markup()

def back_home_keyboard() -> InlineKeyboardMarkup:
    """Standard Back/Home keyboard"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔙 Back", callback_data="cb_back"),
        InlineKeyboardButton(text="🏠 Home", callback_data="cb_home")
    )
    return builder.as_markup()

def cards_menu_keyboard() -> InlineKeyboardMarkup:
    """Create Credit Card submenu"""
    builder = InlineKeyboardBuilder()
    
    builder.row(InlineKeyboardButton(text="📂 Choice Admin Card", callback_data="cb_cards_choice_admin"))
    builder.row(InlineKeyboardButton(text="✍️ Create Your Card Template", callback_data="cb_cards_template_input"))
    builder.row(
        InlineKeyboardButton(text="🔙 Back", callback_data="cb_back"),
        InlineKeyboardButton(text="🏠 Home", callback_data="cb_home")
    )
    
    return builder.as_markup()

def info_menu_keyboard() -> InlineKeyboardMarkup:
    """Create Card Info submenu"""
    builder = InlineKeyboardBuilder()
    
    builder.row(InlineKeyboardButton(text="🌍 Card Country Info", callback_data="cb_info_country"))
    builder.row(InlineKeyboardButton(text="🪪 Create Fake Profile Info", callback_data="cb_info_profile"))
    builder.row(
        InlineKeyboardButton(text="🔙 Back", callback_data="cb_back"),
        InlineKeyboardButton(text="🏠 Home", callback_data="cb_home")
    )
    
    return builder.as_markup()

def admin_menu_keyboard() -> InlineKeyboardMarkup:
    """Admin Panel menu"""
    builder = InlineKeyboardBuilder()
    
    builder.row(InlineKeyboardButton(text="➕ Add Card Template", callback_data="cb_admin_add"))
    builder.row(InlineKeyboardButton(text="❌ Delete Template", callback_data="cb_admin_del_list"))
    builder.row(InlineKeyboardButton(text="📋 Template List", callback_data="cb_admin_list_tpl"))
    builder.row(InlineKeyboardButton(text="💾 Save Country + Service Labels", callback_data="cb_admin_country_labels"))
    builder.row(InlineKeyboardButton(text="📢 Broadcast", callback_data="cb_admin_broadcast"))
    builder.row(InlineKeyboardButton(text="📊 Stats", callback_data="cb_admin_stats"))
    builder.row(
        InlineKeyboardButton(text="🔙 Back", callback_data="cb_back"),
        InlineKeyboardButton(text="🏠 Home", callback_data="cb_home")
    )
    
    return builder.as_markup()

def templates_pagination_keyboard(templates: List[Tuple[int, str]], page: int, total_pages: int) -> InlineKeyboardMarkup:
    """Paginated template list keyboard"""
    builder = InlineKeyboardBuilder()
    
    for tpl_id, tpl_name in templates:
        builder.row(InlineKeyboardButton(
            text=tpl_name,
            callback_data=f"cb_tpl_pick:{tpl_id}"
        ))
    
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Prev", callback_data=f"cb_tpl_prev:{page}"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton(text="Next ➡️", callback_data=f"cb_tpl_next:{page}"))
    
    if nav_buttons:
        builder.row(*nav_buttons)
    
    builder.row(
        InlineKeyboardButton(text="🔙 Back", callback_data="cb_back"),
        InlineKeyboardButton(text="🏠 Home", callback_data="cb_home")
    )
    
    return builder.as_markup()

def admin_templates_keyboard(templates: List[Tuple[int, str]], page: int, total_pages: int, for_delete: bool = False) -> InlineKeyboardMarkup:
    """Admin template list keyboard with delete buttons"""
    builder = InlineKeyboardBuilder()
    
    for tpl_id, tpl_name in templates:
        if for_delete:
            builder.row(InlineKeyboardButton(
                text=f"❌ {tpl_name}",
                callback_data=f"cb_admin_tpl_del:{tpl_id}"
            ))
        else:
            builder.row(InlineKeyboardButton(
                text=tpl_name,
                callback_data=f"cb_admin_tpl_view:{tpl_id}"
            ))
    
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Prev", callback_data=f"cb_admin_tpl_prev:{page}"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton(text="Next ➡️", callback_data=f"cb_admin_tpl_next:{page}"))
    
    if nav_buttons:
        builder.row(*nav_buttons)
    
    builder.row(
        InlineKeyboardButton(text="🔙 Back", callback_data="cb_back"),
        InlineKeyboardButton(text="🏠 Home", callback_data="cb_home")
    )
    
    return builder.as_markup()

def country_picker_keyboard() -> InlineKeyboardMarkup:
    """Country picker keyboard with top countries"""
    builder = InlineKeyboardBuilder()
    
    # Add top countries in 2 columns
    for i in range(0, len(TOP_COUNTRIES), 2):
        row = []
        row.append(InlineKeyboardButton(
            text=TOP_COUNTRIES[i][0],
            callback_data=f"cb_country_pick:{TOP_COUNTRIES[i][1]}"
        ))
        if i + 1 < len(TOP_COUNTRIES):
            row.append(InlineKeyboardButton(
                text=TOP_COUNTRIES[i + 1][0],
                callback_data=f"cb_country_pick:{TOP_COUNTRIES[i + 1][1]}"
            ))
        builder.row(*row)
    
    builder.row(InlineKeyboardButton(text="⌨️ Type Country", callback_data="cb_country_text"))
    builder.row(
        InlineKeyboardButton(text="🔙 Back", callback_data="cb_back"),
        InlineKeyboardButton(text="🏠 Home", callback_data="cb_home")
    )
    
    return builder.as_markup()

def gender_picker_keyboard() -> InlineKeyboardMarkup:
    """Gender picker keyboard"""
    builder = InlineKeyboardBuilder()
    
    for gender_text, gender_cb in GENDERS:
        builder.row(InlineKeyboardButton(
            text=gender_text,
            callback_data=f"cb_gender_{gender_cb}"
        ))
    
    builder.row(
        InlineKeyboardButton(text="🔙 Back", callback_data="cb_back"),
        InlineKeyboardButton(text="🏠 Home", callback_data="cb_home")
    )
    
    return builder.as_markup()

def broadcast_mode_keyboard() -> InlineKeyboardMarkup:
    """Broadcast mode selection keyboard"""
    builder = InlineKeyboardBuilder()
    
    builder.row(InlineKeyboardButton(text="📢 Broadcast Text", callback_data="cb_bc_text"))
    builder.row(InlineKeyboardButton(text="📨 Broadcast Forward", callback_data="cb_bc_forward"))
    builder.row(
        InlineKeyboardButton(text="🔙 Back", callback_data="cb_back"),
        InlineKeyboardButton(text="🏠 Home", callback_data="cb_home")
    )
    
    return builder.as_markup()

def confirm_keyboard(action: str) -> InlineKeyboardMarkup:
    """Yes/No confirmation keyboard"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="✅ Yes", callback_data=f"cb_{action}_yes"),
        InlineKeyboardButton(text="❌ No", callback_data=f"cb_{action}_no")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Back", callback_data="cb_back"),
        InlineKeyboardButton(text="🏠 Home", callback_data="cb_home")
    )
    
    return builder.as_markup()
