# LAUNCHER НЕ РАБОТАЕТ
import subprocess


PROCESS = []
NUM_CLIENTS = 2

while True:
    ACTION = input('Выберете действие: q - выход, '
                   's - запустить сервер и клиенты,'
                   ' x - закрыть все окна: ')

    if ACTION == 'q':
        break
    elif ACTION == 's':
        PROCESS.append(subprocess.Popen('python server.py', creationflags=subprocess.CREATE_NEW_CONSOLE))

        # создание клиентов
        for client in range(1, NUM_CLIENTS + 1):
            PROCESS.append(subprocess.Popen('python __init__.py', creationflags=subprocess.CREATE_NEW_CONSOLE))

    elif ACTION == 'x':
        while PROCESS:
            PROCESS.pop().kill()
