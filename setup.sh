#!/usr/bin/env bash
set -euo pipefail

APP_FILE="${APP_FILE:-app.py}"
REQ_FILE="${REQ_FILE:-requirements.txt}"
ENV_FILE="${ENV_FILE:-.env}"
ENV_EXAMPLE_FILE="${ENV_EXAMPLE_FILE:-.env.example}"
SEED_MARKER_FILE="${SEED_MARKER_FILE:-.seeded}"
VENV_DIR="${VENV_DIR:-.venv}"

echo "== Cafe Fusion setup =="

# 1) Venv (skip if SKIP_VENV=1)
if [[ "${SKIP_VENV:-0}" != "1" ]]; then
  if [[ ! -d "$VENV_DIR" ]]; then
    echo "Creating venv in $VENV_DIR ..."
    python3 -m venv "$VENV_DIR"
  fi

  echo "Activating venv ..."
  # shellcheck disable=SC1090
  source "$VENV_DIR/bin/activate"
fi

# 2) Install deps
if [[ ! -f "$REQ_FILE" ]]; then
  echo "ERROR: $REQ_FILE not found."
  exit 1
fi

echo "Installing requirements ..."
python -m pip install --upgrade pip >/dev/null 2>&1 || true
python -m pip install -r "$REQ_FILE"

# 3) Create .env if missing
if [[ ! -f "$ENV_FILE" ]]; then
  if [[ -f "$ENV_EXAMPLE_FILE" ]]; then
    echo "Creating $ENV_FILE from $ENV_EXAMPLE_FILE ..."
    cp "$ENV_EXAMPLE_FILE" "$ENV_FILE"
  else
    echo "Creating $ENV_FILE ..."
    cat > "$ENV_FILE" <<EOF
SECRET_KEY=
STAFF_SETUP_CODE=
DATABASE_URL=sqlite:///cafe_fusion.db
EOF
  fi
fi

# 4) Ensure SECRET_KEY exists
if ! grep -qE '^SECRET_KEY=.+' "$ENV_FILE"; then
  echo "Generating SECRET_KEY ..."
  SECRET_KEY="$(python - <<'PY'
import secrets
print(secrets.token_urlsafe(32))
PY
)"
  # Replace if exists empty, else append
  if grep -qE '^SECRET_KEY=' "$ENV_FILE"; then
    # macOS sed needs -i ''
    sed -i '' "s/^SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" "$ENV_FILE"
  else
    echo "SECRET_KEY=$SECRET_KEY" >> "$ENV_FILE"
  fi
fi

# 5) Ensure STAFF_SETUP_CODE exists
if ! grep -qE '^STAFF_SETUP_CODE=.+' "$ENV_FILE"; then
  echo "Setting default STAFF_SETUP_CODE=iamstaff (change it in .env if you want)"
  if grep -qE '^STAFF_SETUP_CODE=' "$ENV_FILE"; then
    sed -i '' "s/^STAFF_SETUP_CODE=.*/STAFF_SETUP_CODE=iamstaff/" "$ENV_FILE"
  else
    echo "STAFF_SETUP_CODE=iamstaff" >> "$ENV_FILE"
  fi
fi

# 6) Seed once (guarded)
if [[ -f "$SEED_MARKER_FILE" ]]; then
  echo "Seed already ran (found $SEED_MARKER_FILE). Skipping."
else
  echo "Seeding database ..."
  python -m flask --app "$APP_FILE" seed
  date > "$SEED_MARKER_FILE"
  echo "Seed done. Marker created: $SEED_MARKER_FILE"
fi

echo ""
echo "Setup complete."
echo "Run the app:"
echo "  python -m flask --app $APP_FILE run"