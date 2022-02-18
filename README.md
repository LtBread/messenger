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
