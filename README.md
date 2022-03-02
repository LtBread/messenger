messenger

Клиент-серверные приложения на Python

Урок 3. Основы сетевого программирования

    1. Реализовать простое клиент-серверное взаимодействие по протоколу JIM (JSON instant messaging):
        a. клиент отправляет запрос серверу;
        b. сервер отвечает соответствующим кодом результата. 
    
    Клиент и сервер должны быть реализованы в виде отдельных скриптов, содержащих соответствующие функции. 
    
    Функции клиента:
        сформировать presence-сообщение; 
        отправить сообщение серверу;
        получить ответ сервера; 
        разобрать сообщение сервера; 
        параметры командной строки скрипта client.py <addr> [<port>]: 
            addr — ip-адрес сервера; 
            port — tcp-порт на сервере, по умолчанию 7777. 

    Функции сервера: 
        принимает сообщение клиента; 
        формирует ответ клиенту; 
        отправляет ответ клиенту; 
        имеет параметры командной строки:
            -p <port> — TCP-порт для работы (по умолчанию использует 7777); 
            -a <addr> — IP-адрес для прослушивания (по умолчанию слушает все доступные адреса).

Урок 4. Основы тестирования
    
    1. Для всех функций из урока 3 написать тесты с использованием unittest. Они должны быть оформлены в 
    отдельных скриптах с префиксом test_ в имени файла (например, test_client.py).

    2. * Написать тесты для домашних работ из курса «Python 1».

Урок 5. Логирование

    Для проекта «Мессенджер» реализовать логирование с использованием модуля logging:

    1. В директории проекта создать каталог log, в котором для клиентской и серверной сторон в отдельных модулях формата client_log_config.py и server_log_config.py создать логгеры;
    2. В каждом модуле выполнить настройку соответствующего логгера по следующему алгоритму:

        Создание именованного логгера;
        Сообщения лога должны иметь следующий формат: "<дата-время> <уровеньважности> <имямодуля> <сообщение>";
        Журналирование должно производиться в лог-файл;
        На стороне сервера необходимо настроить ежедневную ротацию лог-файлов.

    3. Реализовать применение созданных логгеров для решения двух задач:

        Журналирование обработки исключений try/except. Вместо функции print() использовать журналирование и обеспечить вывод служебных сообщений в лог-файл;
        Журналирование функций, исполняемых на серверной и клиентской сторонах при работе мессенджера.
