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

Урок 6. Декораторы и продолжение работы с сетью

    1. Продолжая задачу логирования, реализовать декоратор @log, фиксирующий обращение к декорируемой функции. Он сохраняет ее имя и аргументы.
    2. В декораторе @log реализовать фиксацию функции, из которой была вызвана декорированная. Если имеется такой код:        
        @log
        def func_z():
         pass        
        def main():
         func_z()
    ...в логе должна быть отражена информация: "<дата-время> Функция func_z() вызвана из функции main"

Урок 7. Модуль select, слоты

    1. Реализовать обработку нескольких клиентов на сервере, используя функцию select. 
    Клиенты должны общаться в «общем чате»: каждое сообщение участника отправляется всем, подключенным к серверу.
    2. Реализовать функции отправки/приема данных на стороне клиента. Чтобы упростить разработку на данном этапе, 
    пусть клиентское приложение будет либо только принимать, либо только отправлять сообщения в общий чат. 
    Эти функции надо реализовать в рамках отдельных скриптов.

Урок 8. Потоки

    1. На клиентской стороне реализовать прием и отправку сообщений с помощью потоков в P2P-формате (обмен сообщениями между двумя пользователями).
    Итогом выполнения домашних заданий первой части продвинутого курса Python стал консольный мессенджер. 
    Усовершенствуем его во второй части: реализуем взаимосвязь мессенджера с базами данных и создадим для него графический пользовательский интерфейс.

Урок 1(9). Полезные модули

    5. *В следующем уроке мы будем изучать дескрипторы и метаклассы. Но вы уже сейчас можете перевести часть кода из
    функционального стиля в объектно-ориентированный. Создайте классы «Клиент» и «Сервер», а используемые функции превратите в методы классов.

Урок 2(10). Дескрипторы и метаклассы

    Продолжение работы с проектом «Мессенджер»:

    1. Реализовать метакласс ClientVerifier, выполняющий базовую проверку класса «Клиент» (для некоторых проверок уместно использовать модуль dis):

        отсутствие вызовов accept и listen для сокетов;
        использование сокетов для работы по TCP;

    2. Реализовать метакласс ServerVerifier, выполняющий базовую проверку класса «Сервер»:

        отсутствие вызовов connect для сокетов;
        использование сокетов для работы по TCP.

    3. Реализовать дескриптор для класса серверного сокета, а в нем — проверку номера порта. Это должно быть целое
    число (>=0). Значение порта по умолчанию равняется 7777. Дескриптор надо создать в отдельном классе.
    Его экземпляр добавить в пределах класса серверного сокета. Номер порта передается в экземпляр дескриптора
    при запуске сервера.

Урок 3(11). Хранение данных в БД. ORM SQLAlchemy

    Опорная схема базы данных:
    На стороне сервера БД содержит следующие таблицы:
    a) клиент:
    * логин;
    * информация.
    b) историяклиента:
    * время входа;
    * ip-адрес.
    c) списокактивныхпользователей (составляется на основании выборки всех записей с idвладельца):
    * id_владельца;
    * id_клиента.

Урок 4. Хранение данных в БД (продолжение) и основы Qt

    1. Продолжить реализацию класса хранилища для серверной стороны.
    a) Реализовать функционал работы со списком контактов по протоколу JIM:
    Получение списка контактов
    Запрос к серверу:

    {
    "action": "get_contacts",
    "time": <unix timestamp>,
    "user_login": "login"
    }

    Положительный ответ сервера будет содержать список контактов:
    {
    "response": "202",
    "alert": "[‘nick_1’, ‘nick_2’,...]"
    }
    Получение списка контактов — не самая частая операция при взаимодействии с сервером. Она должна выполняться после подключения и авторизации клиента. Инициируется им же. В процессе получения списка контактов клиент не должен инициировать другие запросы.
    Добавление/удаление контакта в список контактов
    Запрос к серверу:
    {
    "action": "add_contact" | "del_contact",
    "user_id": "nickname",
    "time": <unix timestamp>,
    "user_login": "login"
    }
    Ответ сервера будет содержать одно сообщение с кодом результата и необязательной расшифровкой:
    {
    "response": xxx,
    }

    b) Реализовать хранение информации в БД на стороне клиента:
    * списокконтактов;
    * историясообщений.

    2. Реализовать графический интерфейс для мессенджера, используя библиотеку PyQt. Реализовать графический интерфейс администратора сервера:
    * отображение списка всех клиентов;
    * отображение статистики клиентов;
    * настройка сервера (подключение к БД, идентификация).

Урок 5. Qt (продолжение), Qt и потоки

    Продолжаем работать над мессенджером:

    1. Реализовать графический интерфейс пользователя на стороне клиента:
    Отображение списка контактов;
    Выбор чата двойным кликом на элементе списка контактов;
    Добавление нового контакта в локальный список контактов;
    Отображение сообщений в окне чата;
    Набор сообщения в окне ввода сообщения;
    Отправка введенного сообщения.

Урок 6. Безопасность

    1. Реализовать аутентификацию пользователей на сервере.
    2. *Реализовать декоратор @login_required, проверяющий авторизованность пользователя для выполнения той или иной функции.
    3. Реализовать хранение паролей в БД сервера (пароли не хранятся в открытом виде — хранится хэш-образ от пароля с добавлением криптографической соли).
    4. *Реализовать возможность сквозного шифрования сообщений (использовать асимметричный шифр, ключи которого хранятся только у клиентов).

Урок 7. PEP-8, подготовка документации

    1. Для проекта «Мессенджер» подготовить документацию с использованием sphinx-doc.
    2. Проверить программный код домашних заданий текущего курса и курса Python-1 на соответствие положениям PEP-8. При необходимости выполнить преобразования.

Урок 8. Подготовка дистрибутива

    1. Для разработанного проекта «Мессенджер» сформировать whl-пакеты с дистрибутивами сервера и клиента.
    2. *Выполнить процедуру сборки созданного проекта «Мессенджер» с помощью утилиты cx_Freeze.
    3. Выполнить загрузку сформированных whl-пакетов с дистрибутивами сервера и клиента в репозиторий сервиса PyPi и прислать ссылки на эти пакеты (а не ссылку на репозиторий!)
    4. *В качестве защиты курсового проекта необходимо записать в любой удобной для вас программе видеоролик (скринкаст) продолжительностью 1-5 минут. Представьте, что вам необходимо презентовать вашу работу заказчику или аудитории. В скринкасте расскажите о вашем проекте, продемонстрируйте его возможности и функционал. Ссылку на видео приложите к практическому заданию, например, в комментарии к уроку. И не забудьте открыть доступ на просмотр! :) Видеопрезентация продукта развивает у вас дополнительные мягкие навыки и является обязательной для засчитывания курсового проекта.