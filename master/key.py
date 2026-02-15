"""
Master key module - Appx Free UI/Keyboard functionality.
Reconstructed from key.so (master/key.py).
Handles /app command, paginated APPX free app menus, random photos,
join/contact keyboards.
"""
import logging
import aiohttp
import math
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import Config

logger = logging.getLogger(__name__)

# Number of apps per page in pagination
APPS_PER_PAGE = 6

# App identifier map: maps callback_data prefixes to module names
# This maps the button callback data to the actual appx app identifiers
app_identifier_map = {}


async def get_appx_api():
    """
    Fetch all APPX API entries from database.
    Returns list of dicts with 'app_name' and 'api_url'.
    """
    try:
        from Database import standarddb
        apis = await standarddb.db_instance.get_all_appx_apis()
        return apis if apis else []
    except Exception as e:
        logger.error(f"Error fetching APPX APIs: {e}")
        return []


async def gen_apps_free_kb(page=0):
    """
    Generate paginated inline keyboard for APPX free apps.
    Fetches app list from database and creates paginated buttons.
    
    Args:
        page: Current page number (0-indexed)
    
    Returns:
        InlineKeyboardMarkup with app buttons and navigation
    """
    try:
        apis = await get_appx_api()
        
        if not apis:
            return InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ No Apps Available", callback_data="none")],
                [InlineKeyboardButton("🏠 Menu", callback_data="home")]
            ])
        
        # Sort apps by name
        sorted_apps = sorted(apis, key=lambda x: x.get('app_name', '').lower())
        
        # Build app_identifier_map
        global app_identifier_map
        app_identifier_map = {}
        for app in sorted_apps:
            app_name = app.get('app_name', '')
            # Create safe callback data prefix
            safe_id = f"free_{app_name[:20].replace(' ', '_').lower()}"
            app_identifier_map[safe_id] = {
                'app_name': app_name,
                'api_url': app.get('api_url', '')
            }
        
        # Paginate
        total_apps = len(sorted_apps)
        total_pages = math.ceil(total_apps / APPS_PER_PAGE)
        
        # Clamp page number
        page = max(0, min(page, total_pages - 1))
        
        start_idx = page * APPS_PER_PAGE
        end_idx = min(start_idx + APPS_PER_PAGE, total_apps)
        paginated_apps = sorted_apps[start_idx:end_idx]
        
        # Build keyboard rows (2 buttons per row)
        keyboard = []
        row = []
        for i, app in enumerate(paginated_apps):
            app_name = app.get('app_name', 'Unknown')
            safe_id = f"free_{app_name[:20].replace(' ', '_').lower()}"
            row.append(InlineKeyboardButton(
                f"📱 {app_name}",
                callback_data=safe_id
            ))
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        
        # Navigation buttons
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️ Back", callback_data=f"appx_page_{page - 1}"))
        
        nav_buttons.append(InlineKeyboardButton(f"📄 {page + 1}/{total_pages}", callback_data="none"))
        
        if page < total_pages - 1:
            nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"appx_page_{page + 1}"))
        
        keyboard.append(nav_buttons)
        keyboard.append([InlineKeyboardButton("🏠 Menu", callback_data="home")])
        
        return InlineKeyboardMarkup(keyboard)
        
    except Exception as e:
        logger.error(f"Error generating apps keyboard: {e}")
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Error Loading Apps", callback_data="none")],
            [InlineKeyboardButton("🏠 Menu", callback_data="home")]
        ])


async def handle_app(bot, msg):
    """
    Handle the /app command.
    Shows initial APPX free apps menu with paginated keyboard.
    """
    try:
        user_id = msg.chat.id
        photo = await send_random_photo()
        markup = await gen_apps_free_kb(page=0)
        
        caption = (
            "<b>📱 APPX Free Apps</b>\n\n"
            "Select an app from the list below to extract content.\n"
            "These extractors work <b>without login credentials</b>.\n\n"
            "<b>Current page: </b>1"
        )
        
        await bot.send_photo(
            chat_id=user_id,
            photo=photo,
            caption=caption,
            reply_markup=markup
        )
    except Exception as e:
        logger.error(f"Error in handle_app: {e}")
        await msg.reply_text(f"⚠️ Error loading apps: {e}")


async def appx_page(bot, callback_query, page):
    """
    Handle page navigation in APPX free apps menu.
    Called when user clicks Back/Next page buttons.
    """
    try:
        markup = await gen_apps_free_kb(page=page)
        apis = await get_appx_api()
        total_pages = math.ceil(len(apis) / APPS_PER_PAGE) if apis else 1
        
        caption = (
            "<b>📱 APPX Free Apps</b>\n\n"
            "Select an app from the list below to extract content.\n"
            "These extractors work <b>without login credentials</b>.\n\n"
            f"<b>Current page: </b>{page + 1}/{total_pages}"
        )
        
        await callback_query.message.edit_caption(
            caption=caption,
            reply_markup=markup
        )
    except Exception as e:
        logger.error(f"Error in appx_page: {e}")
        try:
            await callback_query.answer(f"Error: {e}", show_alert=True)
        except:
            pass


async def send_random_photo():
    """
    Fetch a random photo from picsum.photos.
    Returns URL of a random image.
    """
    try:
        # picsum.photos returns a random image
        return f"https://picsum.photos/500/300?random={__import__('random').randint(1, 10000)}"
    except Exception as e:
        logger.error(f"Error getting random photo: {e}")
        # Fallback to thumbnail
        return getattr(Config, 'THUMB_URL', "https://picsum.photos/500/300")


def join_user():
    """
    Generate join channel + contact admin keyboard markup.
    Returns InlineKeyboardMarkup for /start command.
    """
    buttons = [
        [InlineKeyboardButton("📢 Join Our Channel", url=Config.CH_URL)],
        [InlineKeyboardButton("👤 Contact Admin", url=Config.OWNER)]
    ]
    return InlineKeyboardMarkup(buttons)


def contact():
    """
    Generate contact admin keyboard markup.
    Returns InlineKeyboardMarkup for /upgrade command.
    """
    buttons = [
        [InlineKeyboardButton("👤 Contact Admin", url=Config.OWNER)],
        [InlineKeyboardButton("📢 Join Our Channel", url=Config.CH_URL)]
    ]
    return InlineKeyboardMarkup(buttons)


def get_handle_appx_free_data(data):
    """
    Resolve callback data to APPX app info.
    
    Args:
        data: callback_data string from button press
        
    Returns:
        dict with 'app_name' and 'api_url' or None
    """
    if data in app_identifier_map:
        return app_identifier_map[data]
    
    # Search by prefix match
    for key, value in app_identifier_map.items():
        if data.startswith("free_") and key == data:
            return value
    
    logger.error(f"Error: app_id {data} not found in app_identifier_map. Restart Markup Keyboard by /app")
    return None
