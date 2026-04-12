#!/usr/bin/env bash
set -euo pipefail

MODEL="${VIBEVOICE_MODEL:-microsoft/VibeVoice-1.5B}"
LANGUAGE="${VIBEVOICE_LANGUAGE:-zh}"
SEED="${VIBEVOICE_SEED:-1227}"
DEPLOY_DIR="${VIBEVOICE_DEPLOY_DIR:-$HOME/.cache/nick-skills/vibevoice}"
SOURCE_DIR="${VIBEVOICE_SOURCE_DIR:-$DEPLOY_DIR/source}"
VENV_DIR="${VIBEVOICE_VENV:-$DEPLOY_DIR/.venv}"
SOURCE_REPO="${VIBEVOICE_SOURCE_REPO:-https://github.com/vibevoice-community/VibeVoice.git}"
SOURCE_ZIP_URL="${VIBEVOICE_SOURCE_ZIP_URL:-https://github.com/vibevoice-community/VibeVoice/archive/refs/heads/main.zip}"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ADAPTER="$SCRIPT_DIR/vibevoice_tts_adapter.py"
ENV_FILE="$DEPLOY_DIR/env.sh"

log() {
  printf '[ensure-vibevoice] %s\n' "$*"
}

remove_path() {
  local path="$1"
  if [[ ! -e "$path" && ! -L "$path" ]]; then
    return
  fi
  if command -v trash >/dev/null 2>&1; then
    trash "$path"
  else
    rm -rf "$path"
  fi
}

python_version_ok() {
  "$1" - "$2" <<'PY' >/dev/null 2>&1
import sys

minimum = tuple(int(part) for part in sys.argv[1].split("."))
raise SystemExit(0 if sys.version_info[:2] >= minimum else 1)
PY
}

pick_python() {
  if [[ -n "${PYTHON:-}" ]]; then
    python_version_ok "$PYTHON" "3.10" || {
      echo "PYTHON must point to Python 3.10 or newer for VibeVoice dependencies: $PYTHON" >&2
      exit 1
    }
    printf '%s\n' "$PYTHON"
    return
  fi

  local candidates=(
    python3.12
    python3.11
    python3.10
    /opt/homebrew/opt/python@3.12/bin/python3.12
    /opt/homebrew/opt/python@3.11/bin/python3.11
    "$HOME/miniconda3/bin/python3.12"
    python3
  )
  local candidate
  for candidate in "${candidates[@]}"; do
    if command -v "$candidate" >/dev/null 2>&1 && python_version_ok "$candidate" "3.10"; then
      command -v "$candidate"
      return
    fi
  done

  echo "Python 3.10 or newer is required to install VibeVoice dependencies." >&2
  exit 1
}

endpoint_is_usable() {
  local endpoint="${VIBEVOICE_ENDPOINT:-}"
  if [[ -z "$endpoint" ]]; then
    return 1
  fi
  curl -fsS --max-time 5 "${endpoint%/}" >/dev/null 2>&1
}

download_source_zip() {
  local zip_path="$DEPLOY_DIR/source.zip"
  command -v curl >/dev/null 2>&1 || {
    echo "curl is required to download VibeVoice source." >&2
    exit 1
  }
  command -v unzip >/dev/null 2>&1 || {
    echo "unzip is required to unpack VibeVoice source." >&2
    exit 1
  }
  remove_path "$SOURCE_DIR"
  remove_path "$DEPLOY_DIR/VibeVoice-main"
  curl -L --fail --retry 2 --connect-timeout 20 -o "$zip_path" "$SOURCE_ZIP_URL"
  unzip -q "$zip_path" -d "$DEPLOY_DIR"
  mv "$DEPLOY_DIR/VibeVoice-main" "$SOURCE_DIR"
}

ensure_source() {
  if [[ -f "$SOURCE_DIR/demo/inference_from_file.py" && -f "$SOURCE_DIR/pyproject.toml" ]]; then
    log "VibeVoice source already exists: $SOURCE_DIR"
    return
  fi

  mkdir -p "$DEPLOY_DIR"
  if command -v git >/dev/null 2>&1; then
    log "Cloning VibeVoice source into $SOURCE_DIR"
    if git clone --depth 1 "$SOURCE_REPO" "$SOURCE_DIR"; then
      return
    fi
    log "git clone failed; falling back to zip download"
  fi
  download_source_zip
}

ensure_venv() {
  local python_bin
  python_bin="$(pick_python)"
  if [[ -x "$VENV_DIR/bin/python" ]] && ! python_version_ok "$VENV_DIR/bin/python" "3.10"; then
    log "Existing venv uses Python older than 3.10; recreating: $VENV_DIR"
    remove_path "$VENV_DIR"
  fi
  if [[ ! -x "$VENV_DIR/bin/python" ]]; then
    log "Creating Python venv: $VENV_DIR"
    "$python_bin" -m venv "$VENV_DIR"
  fi

  log "Installing VibeVoice Python dependencies"
  "$VENV_DIR/bin/python" -m pip install --upgrade pip wheel "setuptools<82"
  "$VENV_DIR/bin/python" -m pip install -e "$SOURCE_DIR" "huggingface_hub>=0.24.0"
}

ensure_model() {
  if [[ "${VIBEVOICE_SKIP_MODEL_DOWNLOAD:-0}" == "1" ]]; then
    log "Skipping model download because VIBEVOICE_SKIP_MODEL_DOWNLOAD=1"
    return
  fi

  log "Ensuring Hugging Face model is cached: $MODEL"
  "$VENV_DIR/bin/python" - "$MODEL" <<'PY'
import sys
from huggingface_hub import snapshot_download

model = sys.argv[1]
snapshot_download(repo_id=model)
print(f"cached {model}")
PY
}

write_env_file() {
  mkdir -p "$DEPLOY_DIR"
  local speaker_id="${VIBEVOICE_SPEAKER_ID:-}"
  if [[ -z "$speaker_id" ]]; then
    case "$LANGUAGE" in
      zh*|ZH*) speaker_id="Bowen" ;;
      *) speaker_id="Alice" ;;
    esac
  fi
  cat >"$ENV_FILE" <<EOF
export TEACHING_VIDEO_TTS_ENGINE="vibevoice"
export VIBEVOICE_MODEL="$MODEL"
export VIBEVOICE_LANGUAGE="$LANGUAGE"
export VIBEVOICE_SPEAKER_ID="$speaker_id"
export VIBEVOICE_SEED="$SEED"
export VIBEVOICE_SOURCE_DIR="$SOURCE_DIR"
export VIBEVOICE_VENV="$VENV_DIR"
export VIBEVOICE_TTS_CMD="$VENV_DIR/bin/python $ADAPTER --source-dir $SOURCE_DIR --model {model} --text-file {text_file} --output {output} --voice-ref {voice_ref} --language {language} --speaker-id {speaker_id} --seed {seed}"
EOF
  log "Wrote environment file: $ENV_FILE"
}

main() {
  if endpoint_is_usable; then
    log "VibeVoice endpoint is already usable: ${VIBEVOICE_ENDPOINT%/}"
    exit 0
  fi

  if [[ -n "${VIBEVOICE_TTS_CMD:-}" ]]; then
    log "VIBEVOICE_TTS_CMD is already configured"
    exit 0
  fi

  ensure_source
  ensure_venv
  ensure_model
  write_env_file

  cat <<EOF

VibeVoice local command deployment is ready.

Load it in the current shell before generating teaching-video audio:

  source "$ENV_FILE"

EOF
}

main "$@"
