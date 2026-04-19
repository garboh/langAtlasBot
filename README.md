# 🌐 Telegram Linguistic Atlas Bot

> Hosts and promotes all available Telegram language localizations, with alphabetic and geo-political search.

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python)](https://www.python.org/)
[![python-telegram-bot](https://img.shields.io/badge/python--telegram--bot-21.5-blue)](https://python-telegram-bot.org/)
[![License: GNU GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
[![Telegram](https://img.shields.io/badge/Telegram-@langAtlasBot-blue?logo=telegram)](https://t.me/langAtlasBot)

**@langAtlasBot** is a Telegram bot that lets users discover, search, and install Telegram language localizations. Through an inline button interface, users can browse hundreds of languages and apply them to the app in a single click.

---

## Features

| Feature | Description |
|---|---|
| 🔠 **Alphabetic catalogue** | Browse languages by their initial letter |
| 🌍 **Geo-political catalogue** | Navigate by continent → country → languages |
| ➕ **Language request** | Propose a missing language for inclusion in the Atlas |
| 💬 **Feedback** | Send comments and suggestions to administrators |
| 🔍 **Inline mode** | Search and share languages directly in any chat |
| 🗣 **Multilingual UI** | The bot interface itself is available in 6 languages |

### Supported UI languages

| Code | Language |
|---|---|
| `it` | Italiano |
| `en` | English |
| `fur` | Furlan (Friulian) |
| `vec` | Vèneto (Venetian) |
| `es` | Español |
| `cat` | Català |

---

## Tech stack

- **[python-telegram-bot 21.5](https://python-telegram-bot.org/)** — async Telegram Bot API library
- **MySQL** — database for users, languages, countries and requests
- **GNU gettext** — internationalisation (i18n) system
- **python-dotenv** — secure environment variable management

---

## Project structure

```
langAtlasBot/
├── bot.py                  # Entry point — handler registration and polling
├── config.py               # Loads configuration from .env
├── database.py             # Database layer (context manager, parameterised queries)
├── handlers.py             # All bot logic (callbacks, conversations, inline mode)
├── broadcast.py            # Async broadcast to all users when a new language is added
├── utils.py                # get_translator() — thread-safe i18n with English fallback
├── .env.example            # Environment variable template
├── requirements.txt
├── setup_service.sh        # Installs the bot as a systemd service
├── update_translations.sh  # Extracts, merges and compiles .po/.mo files
└── locale/
    ├── it/LC_MESSAGES/langAtlasBot.{po,mo}
    ├── en/LC_MESSAGES/langAtlasBot.{po,mo}
    ├── fur/LC_MESSAGES/langAtlasBot.{po,mo}
    ├── vec/LC_MESSAGES/langAtlasBot.{po,mo}
    ├── es/LC_MESSAGES/langAtlasBot.{po,mo}
    └── cat/LC_MESSAGES/langAtlasBot.{po,mo}
```

---

## Installation

### Prerequisites

- Python 3.11+
- MySQL 8+
- `libmysqlclient-dev` (required to build `mysqlclient`)
- `gettext` (required for translations)

```bash
sudo apt install python3 python3-venv libmysqlclient-dev gettext
```

### 1. Clone the repository

```bash
git clone https://github.com/garboh/langAtlasBot.git
cd langAtlasBot
```

### 2. Create a virtual environment and install dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r langAtlasBot/requirements.txt
```

### 3. Configure environment variables

```bash
cp langAtlasBot/.env.example langAtlasBot/.env
nano langAtlasBot/.env
```

```env
BOT_TOKEN=your_token_from_BotFather
DB_HOST=127.0.0.1
DB_USER=your_db_user
DB_PASS=your_db_password
DB_NAME=langAtlasBot
ADMIN_GROUP_ID=-100xxxxxxxxx
```

### 4. Initialise the database

Import the SQL schema into your MySQL database:

```bash
mysql -u root -p langAtlasBot < schema.sql
```

### 5. Compile translation files

```bash
bash langAtlasBot/update_translations.sh compile
```

### 6. Start the bot

```bash
python -m langAtlasBot
```

---

## Deploy as a systemd service

For a production Linux deployment with automatic restarts:

```bash
sudo bash langAtlasBot/setup_service.sh
```

The script will:
- Create the virtual environment and install dependencies
- Compile translation files
- Register and start the `langAtlasBot` systemd service

Useful commands after installation:

```bash
sudo journalctl -u langAtlasBot -f        # live logs
sudo systemctl restart langAtlasBot       # restart
sudo systemctl stop langAtlasBot          # stop
```

---

## Translations

Bot UI strings use **GNU gettext**. To update or add a language:

```bash
# Extract strings from source, update .po files and recompile .mo files
bash langAtlasBot/update_translations.sh

# Recompile only, after editing a .po file manually
bash langAtlasBot/update_translations.sh compile
```

`.po` files are located at `locale/<lang_code>/LC_MESSAGES/langAtlasBot.po` and can be edited with **[Poedit](https://poedit.net/)** or any text editor.

To contribute a translation, fork the repository, edit the relevant `.po` file and open a Pull Request.
If you'd like to add a new language, create the directory `locale/<lang_code>/LC_MESSAGES/`, copy `locale/en/LC_MESSAGES/langAtlasBot.po` as a starting point, translate the strings and submit a PR.

> **Note:** We are looking for a free hosted translation platform (e.g. [Weblate](https://hosted.weblate.org)) to make contributing easier. Contributions via GitHub PR are welcome in the meantime.

---

## Database schema

| Table | Description |
|---|---|
| `user` | Registered users, preferred language, conversation state |
| `lang` | Languages with localised names in 6 languages, flag and code |
| `customLang` | Non-standard / custom languages |
| `continent` | Continents with localised names |
| `country` | Countries with localised names and continent association |
| `country_lang` | Country ↔ language mapping |
| `richieste` | User-submitted language inclusion requests |
| `feedback` | User feedback messages |

---

## Security

- All credentials are loaded exclusively from `.env` — no secrets in source code
- SQL column names are resolved from internal whitelist dictionaries, never interpolated from user input
- All queries use parameterised placeholders (`%s`)
- Every database connection is managed via a context manager with automatic rollback on error

---

## Contributing

1. Fork the repository
2. Create a branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add ...'`)
4. Open a Pull Request

To propose a new language for the Atlas, use the bot directly: [@langAtlasBot](https://t.me/langAtlasBot)

---

## Authors

- **Federico Campagnolo** — concept and design
- **Francesco Garbo** — development and maintenance
- **[Còdaze Veneto](https://t.me/LenguaVeneta)** — localisation and outreach

---

## License

Distributed under the **GNU General Public License v3.0** License. See [LICENSE](LICENSE) for details.
