import subprocess


PROCESS = []
NUM_CLIENTS = 3

while True:
    ACTION = input('Выберете действие: q - выход, '
                   's - запустить сервер и клиенты, x - закрыть все окна: ')

    if ACTION == 'q':
        break
    elif ACTION == 's':
        PROCESS.append(subprocess.Popen('python server.py', creationflags=subprocess.CREATE_NEW_CONSOLE))

        # создание клиентов
        for client in range(1, NUM_CLIENTS + 1):
            PROCESS.append(
                subprocess.Popen(f'python client.py -n test_client_{client}',
                                 creationflags=subprocess.CREATE_NEW_CONSOLE)
            )

    elif ACTION == 'x':
        while PROCESS:
            VICTIM = PROCESS.pop()
            VICTIM.kill()
