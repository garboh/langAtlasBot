#!/bin/bash

# --- CONFIGURAZIONE (Modifica se necessario) ---
SERVICE_NAME="langAtlasBot"
PROJECT_DIR="/home/ubuntu/bot/langatlasbot"   # Cartella del pacchetto Python
PARENT_DIR="/home/ubuntu/bot"                 # Cartella padre (da cui si lancia il modulo)
MODULE_NAME="$(basename "$PROJECT_DIR")"      # Nome del modulo = nome esatto della cartella
VENV_DIR="$PARENT_DIR/venv"                   # Virtual Environment condiviso (o cambia in $PROJECT_DIR/venv)
PYTHON_EXEC="$VENV_DIR/bin/python"
PIP_EXEC="$VENV_DIR/bin/pip"
BOT_USER="ubuntu"                             # Utente Linux che eseguirà il bot
ENV_FILE="$PROJECT_DIR/.env"
# -----------------------------------------------

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}╔══════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║   LANG ATLAS BOT — SERVICE SETUP         ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════╝${NC}"
echo ""

# 1. Controllo privilegi di root
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}Errore: devi eseguire questo script con sudo.${NC}"
  echo "  Usa: sudo bash setup_service.sh"
  exit 1
fi

# 2. Verifica esistenza del pacchetto (bot.py come entry point)
if [ ! -f "$PROJECT_DIR/bot.py" ]; then
  echo -e "${RED}Errore: bot.py non trovato in $PROJECT_DIR${NC}"
  echo "  Assicurati che il progetto sia già nella cartella corretta."
  exit 1
fi

# 3. Verifica requirements.txt
if [ ! -f "$PROJECT_DIR/requirements.txt" ]; then
  echo -e "${RED}Errore: requirements.txt non trovato in $PROJECT_DIR${NC}"
  exit 1
fi

# 4. Verifica python3
if ! command -v python3 &> /dev/null; then
  echo -e "${RED}Errore: python3 non trovato.${NC}"
  echo "  Installa con: sudo apt install python3 python3-venv python3-pip"
  exit 1
fi

# 5. Installa dipendenze di sistema necessarie per mysqlclient
echo "Verifica dipendenze di sistema (libmysqlclient-dev, pkg-config)..."
MISSING_PKGS=()
for pkg in libmysqlclient-dev pkg-config python3-venv gettext; do
  dpkg -l "$pkg" 2>/dev/null | grep -q '^ii' || MISSING_PKGS+=("$pkg")
done

if [ ${#MISSING_PKGS[@]} -gt 0 ]; then
  echo "  Installazione pacchetti mancanti: ${MISSING_PKGS[*]}"
  apt-get install -y "${MISSING_PKGS[@]}"
  if [ $? -ne 0 ]; then
    echo -e "${RED}Errore: impossibile installare le dipendenze di sistema.${NC}"
    echo "  Prova manualmente: sudo apt install ${MISSING_PKGS[*]}"
    exit 1
  fi
fi

echo -e "${GREEN}[1/6] Prerequisiti verificati.${NC}"

# 6. Proprietà della cartella
echo "Impostazione proprietà di $PARENT_DIR → $BOT_USER..."
chown -R "$BOT_USER:$BOT_USER" "$PARENT_DIR"

# 7. Crea il virtual environment se non esiste
if [ ! -d "$VENV_DIR" ]; then
  echo "Creazione virtual environment in $VENV_DIR..."
  sudo -u "$BOT_USER" python3 -m venv "$VENV_DIR"
  if [ $? -ne 0 ]; then
    echo -e "${RED}Errore: impossibile creare il virtual environment.${NC}"
    echo "  Installa python3-venv con: sudo apt install python3-venv"
    exit 1
  fi
  echo -e "${GREEN}[2/6] Virtual environment creato.${NC}"
else
  echo -e "${GREEN}[2/6] Virtual environment già esistente — riutilizzato.${NC}"
fi

# 8. Installa / aggiorna le dipendenze
echo "Installazione dipendenze da requirements.txt..."
sudo -u "$BOT_USER" "$PIP_EXEC" install --upgrade pip -q
sudo -u "$BOT_USER" "$PIP_EXEC" install -r "$PROJECT_DIR/requirements.txt" -q
if [ $? -ne 0 ]; then
  echo -e "${RED}Errore durante l'installazione delle dipendenze.${NC}"
  echo "  Controlla che libmysqlclient-dev sia installato."
  exit 1
fi
echo -e "${GREEN}[3/6] Dipendenze installate.${NC}"

# 9. Verifica file .env
if [ ! -f "$ENV_FILE" ]; then
  echo -e "${YELLOW}[4/6] Attenzione: file .env non trovato in $PROJECT_DIR${NC}"
  if [ -f "$PROJECT_DIR/.env.example" ]; then
    echo "  Copia il template e compila le variabili:"
    echo "    cp $PROJECT_DIR/.env.example $PROJECT_DIR/.env"
    echo "    nano $PROJECT_DIR/.env"
  else
    echo "  Crea $ENV_FILE con le seguenti variabili:"
    echo "    BOT_TOKEN=..."
    echo "    DB_HOST=127.0.0.1"
    echo "    DB_USER=..."
    echo "    DB_PASS=..."
    echo "    DB_NAME=langAtlasBot"
    echo "    ADMIN_GROUP_ID=..."
  fi
  echo ""
else
  echo -e "${GREEN}[4/6] File .env trovato.${NC}"
fi

# 10. Compilazione file .mo per le traduzioni (se msgfmt è disponibile)
if command -v msgfmt &> /dev/null; then
  echo "Compilazione file di traduzione .po → .mo..."
  for po_file in "$PROJECT_DIR"/locale/*/LC_MESSAGES/langAtlasBot.po; do
    mo_file="${po_file%.po}.mo"
    sudo -u "$BOT_USER" msgfmt "$po_file" -o "$mo_file" 2>/dev/null && \
      echo "  Compilato: $po_file" || \
      echo -e "  ${YELLOW}Saltato (errore): $po_file${NC}"
  done
else
  echo -e "${YELLOW}[!] msgfmt non trovato — file .mo non ricompilati.${NC}"
  echo "  Se le traduzioni non funzionano: sudo apt install gettext"
fi

# 11. Scrittura del file .service
echo "Creazione del file di servizio /etc/systemd/system/$SERVICE_NAME.service..."

cat <<EOF > /etc/systemd/system/$SERVICE_NAME.service
[Unit]
Description=Lang Atlas Bot — Telegram Linguistic Atlas bot
Documentation=https://github.com/garboh/langAtlasBot
After=network.target mysql.service
Requires=mysql.service

[Service]
User=$BOT_USER
Group=$BOT_USER
WorkingDirectory=$PARENT_DIR
ExecStart=$PYTHON_EXEC -m $MODULE_NAME
Restart=always
RestartSec=10
StartLimitInterval=60
StartLimitBurst=5

StandardOutput=journal
StandardError=journal
SyslogIdentifier=$SERVICE_NAME

Environment=PYTHONUNBUFFERED=1
EnvironmentFile=-$ENV_FILE

# Hardening di sicurezza
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=$PARENT_DIR

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}[5/6] File di servizio creato.${NC}"

# 12. Attivazione e avvio
echo "Ricaricamento demone systemd..."
systemctl daemon-reload

echo "Abilitazione avvio automatico al boot..."
systemctl enable "$SERVICE_NAME"

echo "Avvio del servizio..."
systemctl restart "$SERVICE_NAME"

# 13. Verifica finale
sleep 2
echo -e "${GREEN}[6/6] Installazione completata.${NC}"
echo ""
echo -e "${CYAN}╔══════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║          STATO DEL SERVIZIO              ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════╝${NC}"
systemctl status "$SERVICE_NAME" --no-pager
echo ""
echo -e "  Log in tempo reale : ${GREEN}sudo journalctl -u $SERVICE_NAME -f${NC}"
echo -e "  Riavvia il servizio: ${GREEN}sudo systemctl restart $SERVICE_NAME${NC}"
echo -e "  Ferma il servizio  : ${GREEN}sudo systemctl stop $SERVICE_NAME${NC}"
echo -e "  Disabilita boot    : ${GREEN}sudo systemctl disable $SERVICE_NAME${NC}"
