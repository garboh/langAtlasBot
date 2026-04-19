# -*- coding: utf-8 -*-
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.environ["BOT_TOKEN"]
DB_HOST: str = os.getenv("DB_HOST", "127.0.0.1")
DB_USER: str = os.environ["DB_USER"]
DB_PASS: str = os.environ["DB_PASS"]
DB_NAME: str = os.getenv("DB_NAME", "langAtlasBot")
ADMIN_GROUP_ID: int = int(os.getenv("ADMIN_GROUP_ID", "-1001198344093"))
