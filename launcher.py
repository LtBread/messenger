import subprocess


PROCESS = []
NUM_SENDERS = 2
NUM_LISTENERS = 3

while True:
    ACTION = input('Выберете действие: q - выход, '
                   's - запустить сервер и клиенты, x - закрыть все окна: ')

    if ACTION == 'q':
        break
    elif ACTION == 's':
        PROCESS.append(subprocess.Popen('python server.py', creationflags=subprocess.CREATE_NEW_CONSOLE))

        # создание клиентов-отправителей
        for item in range(NUM_SENDERS):
            PROCESS.append(subprocess.Popen('python client.py -m send', creationflags=subprocess.CREATE_NEW_CONSOLE))

        # создание клиентов-слушателей
        for item in range(NUM_LISTENERS):
            PROCESS.append(subprocess.Popen('python client.py -m listen', creationflags=subprocess.CREATE_NEW_CONSOLE))

    elif ACTION == 'x':
        while PROCESS:
            VICTIM = PROCESS.pop()
            VICTIM.kill()