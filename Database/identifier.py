"""
Identifier module - Telegram file sender.
Reconstructed from identifier.so (database/identifier.py).
Provides send_file function to send files via raw Telegram Bot API.
"""
import requests
import logging
from config import Config

logger = logging.getLogger(__name__)


def send_file(file_path, chat_id, caption="", owner=None):
    """
    Send a file to a Telegram chat using the Bot API directly.
    
    Args:
        file_path: Path to the file to send
        chat_id: Telegram chat ID to send to
        caption: Optional caption for the file
        owner: Optional owner ID (defaults to Config.OWNER_ID)
    """
    try:
        bot_token = Config.BOT_TOKEN
        url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
        
        with open(file_path, 'rb') as f:
            files = {'document': f}
            data = {
                'chat_id': chat_id,
                'caption': caption,
                'parse_mode': 'HTML'
            }
            response = requests.post(url, files=files, data=data, timeout=120)
            
        if response.status_code == 200:
            logger.info(f"File sent successfully to {chat_id}")
            return response.json()
        else:
            logger.error(f"Failed to send file: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Failed to send file: {e}")
        return None
