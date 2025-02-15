import datetime
import os

file_path = None


def error(text: str, on_console: bool = True):
    global file_path

    text = f'[ERROR][{datetime.datetime.now().isoformat()}]: {text}\n'
    with open(file_path, 'a') as file:
        file.write(text)
    
    if on_console:
        print(text, end='')


def init():
    global file_path

    os.makedirs('logs/', exist_ok=True)

    start_time = datetime.datetime.now().isoformat()
    file_path = os.path.normpath(f'logs/{start_time}.log'.replace(':', ''))
    with open(file_path, 'w') as file:
        file.write(f'[INFO][{start_time}]: Logger started!\n')


def info(text: str, on_console: bool = True):
    global file_path

    text = f'[INFO][{datetime.datetime.now().isoformat()}]: {text}\n'
    with open(file_path, 'a') as file:
        file.write(text)
    
    if on_console:
        print(text, end='')


def warning(text: str, on_console: bool = True):
    global file_path

    text = f'[WARNING][{datetime.datetime.now().isoformat()}]: {text}\n'
    with open(file_path, 'a') as file:
        file.write(text)
    
    if on_console:
        print(text, end='')
