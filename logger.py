import datetime
import os

file_name = None

def init():
    global file_name

    os.makedirs('logs/', exist_ok=True)

    start_time = datetime.datetime.now().isoformat()
    file_name = f'logs/{start_time}.log'
    with open(file_name, 'w') as file:
        file.write(f'[{start_time}]: Logger started!\n')


def info(text: str, on_console: bool = True):
    global file_name

    text = f'[INFO][{datetime.datetime.now().isoformat()}]: {text}\n'
    with open(file_name, 'a') as file:
        file.write(text)
    
    if on_console:
        print(text, end='')
