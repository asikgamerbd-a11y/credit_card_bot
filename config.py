import os
from dataclasses import dataclass

@dataclass
class Config:
    BOT_TOKEN: str = os.getenv('BOT_TOKEN', '8527092463:AAGKBsBqSTu9m_vBuS23o1sj-j7cPCi62rM')
    ADMIN_ID: int = int(os.getenv('ADMIN_ID', '8197284774'))
    IMAGE_URL: str = os.getenv('IMAGE_URL', 'https://res.cloudinary.com/dv6ugwzk8/image/upload/v1758564178/jnzm7tnz7qyab3jionie.jpg')
    DB_URL: str = os.getenv('DB_URL', 'sqlite+aiosqlite:///bot_database.db')

config = Config()
