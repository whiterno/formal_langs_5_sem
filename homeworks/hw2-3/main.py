from pathlib import Path
import subprocess
import sys


def main():
    folder = Path(__file__).resolve().parent
    tasks = sorted(folder.rglob('task[0-9]*.py'))

    if not tasks:
        raise SystemExit('В папке нет файлов задач task*.py')

    for index, task in enumerate(tasks):
        if index:
            print()
        print(f'=== {task.relative_to(folder)} ===', flush=True)
        subprocess.run([sys.executable, str(task)], cwd=folder, check=True)


if __name__ == '__main__':
    main()
