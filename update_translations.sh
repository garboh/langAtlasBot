#!/bin/bash
# Aggiorna il template .pot dal codice sorgente, fonde le stringhe nuove
# in tutti i .po esistenti e ricompila i .mo.
#
# Uso:
#   bash update_translations.sh          # estrai + merge + compila tutto
#   bash update_translations.sh compile  # solo ricompila i .mo (dopo aver tradotto)

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

DOMAIN="langAtlasBot"
POT_FILE="$DOMAIN.pot"
LOCALE_DIR="locale"
LANGS=(it en fur vec es cat)

# File sorgente da cui estrarre le stringhe _() e __()
SOURCES=(
  "langAtlasBot/handlers.py"
  "langAtlasBot/broadcast.py"
)

# ---------------------------------------------------------------------------
check_tools() {
  local missing=()
  for tool in xgettext msgmerge msgfmt; do
    command -v "$tool" &>/dev/null || missing+=("$tool")
  done
  if [ ${#missing[@]} -gt 0 ]; then
    echo -e "${RED}Errore: strumenti mancanti: ${missing[*]}${NC}"
    echo "  Installa con: sudo apt install gettext"
    exit 1
  fi
}

# ---------------------------------------------------------------------------
extract_pot() {
  echo -e "${CYAN}[1/3] Estrazione stringhe dal codice sorgente...${NC}"

  # Verifica che i file sorgente esistano
  local found=()
  for src in "${SOURCES[@]}"; do
    [ -f "$src" ] && found+=("$src")
  done

  if [ ${#found[@]} -eq 0 ]; then
    echo -e "${RED}Errore: nessun file sorgente trovato. Esegui lo script dalla root del progetto.${NC}"
    exit 1
  fi

  xgettext \
    --language=Python \
    --keyword=_:1 \
    --keyword=__:1,2 \
    --from-code=UTF-8 \
    --add-comments="# Translators:" \
    --package-name="$DOMAIN" \
    --output="$POT_FILE" \
    "${found[@]}"

  # Aggiorna la data nel .pot
  sed -i "s/POT-Creation-Date:.*$/POT-Creation-Date: $(date '+%Y-%m-%d %H:%M%z')\\\\n/" "$POT_FILE" 2>/dev/null || true

  local count
  count=$(grep -c '^msgid' "$POT_FILE" || echo 0)
  echo -e "${GREEN}  ✓ Template aggiornato: $POT_FILE ($((count - 1)) stringhe)${NC}"
}

# ---------------------------------------------------------------------------
merge_po() {
  echo -e "${CYAN}[2/3] Aggiornamento file .po per ogni lingua...${NC}"
  local updated=0
  local skipped=0

  for lang in "${LANGS[@]}"; do
    local po_file="$LOCALE_DIR/$lang/LC_MESSAGES/$DOMAIN.po"

    if [ ! -f "$po_file" ]; then
      # Crea nuovo .po dal template
      echo -e "  ${YELLOW}[nuovo]${NC} $lang — creazione $po_file"
      mkdir -p "$(dirname "$po_file")"
      msginit \
        --input="$POT_FILE" \
        --locale="$lang" \
        --output="$po_file" \
        --no-translator 2>/dev/null || cp "$POT_FILE" "$po_file"
      updated=$((updated + 1))
    else
      # Fonde le stringhe nuove/cambiate senza perdere le traduzioni esistenti
      msgmerge \
        --update \
        --backup=none \
        --quiet \
        "$po_file" "$POT_FILE"

      # Conta stringhe non tradotte e fuzzy
      local untranslated fuzzy
      untranslated=$(msgattrib --untranslated "$po_file" 2>/dev/null | grep -c '^msgid' || echo 0)
      fuzzy=$(msgattrib --only-fuzzy "$po_file" 2>/dev/null | grep -c '^msgid' || echo 0)

      if [ "$untranslated" -gt 0 ] || [ "$fuzzy" -gt 0 ]; then
        echo -e "  ${YELLOW}[attenzione]${NC} $lang — ${untranslated} non tradotte, ${fuzzy} fuzzy → $po_file"
      else
        echo -e "  ${GREEN}[ok]${NC} $lang — completo"
      fi
      updated=$((updated + 1))
    fi
  done

  echo -e "${GREEN}  ✓ $updated file .po aggiornati.${NC}"
}

# ---------------------------------------------------------------------------
compile_mo() {
  echo -e "${CYAN}[3/3] Compilazione .po → .mo...${NC}"
  local compiled=0
  local errors=0

  for lang in "${LANGS[@]}"; do
    local po_file="$LOCALE_DIR/$lang/LC_MESSAGES/$DOMAIN.po"
    local mo_file="$LOCALE_DIR/$lang/LC_MESSAGES/$DOMAIN.mo"

    if [ ! -f "$po_file" ]; then
      echo -e "  ${YELLOW}[salta]${NC} $lang — $po_file non trovato"
      continue
    fi

    if msgfmt --check "$po_file" -o "$mo_file" 2>/dev/null; then
      echo -e "  ${GREEN}[ok]${NC} $lang → $mo_file"
      compiled=$((compiled + 1))
    else
      echo -e "  ${RED}[errore]${NC} $lang — controlla $po_file per errori di sintassi"
      errors=$((errors + 1))
    fi
  done

  echo -e "${GREEN}  ✓ $compiled .mo compilati.${NC}"
  [ "$errors" -gt 0 ] && echo -e "${RED}  ✗ $errors errori — il bot userà la versione precedente per quelle lingue.${NC}"
}

# ---------------------------------------------------------------------------
main() {
  echo -e "${CYAN}╔══════════════════════════════════════════╗${NC}"
  echo -e "${CYAN}║   LANG ATLAS BOT — TRADUZIONE STRINGHE  ║${NC}"
  echo -e "${CYAN}╚══════════════════════════════════════════╝${NC}"
  echo ""

  check_tools

  case "${1:-all}" in
    compile)
      compile_mo
      ;;
    merge)
      extract_pot
      merge_po
      ;;
    all|*)
      extract_pot
      merge_po
      compile_mo
      ;;
  esac

  echo ""
  echo -e "${CYAN}Passo successivo: apri i file .po con Poedit e traduci le stringhe vuote.${NC}"
  echo ""
  for lang in "${LANGS[@]}"; do
    echo -e "  ${YELLOW}$lang${NC}: $LOCALE_DIR/$lang/LC_MESSAGES/$DOMAIN.po"
  done
  echo ""
  echo -e "  Dopo aver tradotto, ricompila con: ${GREEN}bash update_translations.sh compile${NC}"
}

main "$@"
