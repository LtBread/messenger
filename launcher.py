import subprocess


def main():
    """ Функция для тестового пуска приложения """
    process = []
    while True:
        action = input('Выберете действие: q - выход, '
                       's - запустить сервер и клиенты, '
                       'l - запустить клиенты, '
                       'x - закрыть все окна: ')

        if action == 'q':
            break
        elif action == 's':
            process.append(
                subprocess.Popen(
                    'python server_main.py',
                    creationflags=subprocess.CREATE_NEW_CONSOLE))
        elif action == 'k':
            print('Убедитесь, что на сервере зарегистрировано необходимое количество клиентов с паролем 123456')
            clients_count = int(input('Введите количество тестовых клиентов: '))
            # создание клиентов
            for client in range(clients_count):
                process.append(
                    subprocess.Popen(
                        f'python client_main.py -n test{client + 1} -p 123456',
                        creationflags=subprocess.CREATE_NEW_CONSOLE))

        elif action == 'x':
            while process:
                process.pop().kill()


if __name__ == '__main__':
    main()
