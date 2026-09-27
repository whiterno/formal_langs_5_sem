#!/usr/bin/env bash

set -e

# Все относительные пути к папкам считаются от корня проекта.
project_dir="$(cd "$(dirname "$0")" && pwd)"
work_dir="${1:-.}"
script_name="${2:-main.py}"

if [[ "$work_dir" != /* ]]; then
    work_dir="$project_dir/$work_dir"
fi

# Создаём окружение только при первом запуске.
if [[ ! -d "$project_dir/.venv" ]]; then
    python3 -m venv "$project_dir/.venv"
fi

source "$project_dir/.venv/bin/activate"

# Пока внешних Python-зависимостей нет. Если они появятся,
# добавьте их в requirements.txt — скрипт установит их при запуске.
if [[ -s "$project_dir/requirements.txt" ]]; then
    python -m pip install -r "$project_dir/requirements.txt"
fi

# Теперь пакет language виден из любой папки домашки.
export PYTHONPATH="$project_dir${PYTHONPATH:+:$PYTHONPATH}"

cd "$work_dir"

# Всё после имени файла передаём как аргументы Python-программы.
if [[ $# -ge 2 ]]; then
    shift 2
else
    set --
fi

exec python "$script_name" "$@"
