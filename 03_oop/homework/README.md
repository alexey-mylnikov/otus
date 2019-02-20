# Scoring API
## Задача
Реализовать декларированный язык описания и систему валидации запросов к HTTP API сервиса скоринга. Покрыть API тестами.
### Код
Скачать репозиторий:
```bash
$ git clone https://github.com/alexey-mylnikov/otus
# or via ssh
$ git clone ssh://git@github.com/alexey-mylnikov/otus
$ cd otus/03_oop/homework/
```
##### Подготовка окружения:
Установить python 2.7 и pip для вашей OS.

Установить необходимые зависимости:
```bash
$ pip install -r requirements.txt
```
##### Запуск тестов:
```bash
$ python -m unittest discover -s tests/
```
##### Запуск HTTP сервера:
```bash
$ python app/app.py -p 8080
```
##### Запуск HTTP сервера в докер контейнере:
```bash
$ docker-compose up --build
```
### Примеры запросов
```bash
# client interests
$ curl -X POST -H "Content-Type: application/json" -d '{"arguments": {"date": "27.01.2019", "client_ids": [1, 2, 3]}, "account": "horns&hoofs", "login": "h&f", "token": "55cc9ce545bcd144300fe9efc28e65d415b923ebb6be1e19d2750a2c03e80dd209a27954dca045e5bb12418e7d89b6d718a9e35af34e14e1d5bcd5a08f21fc95", "method": "clients_interests"}' http://127.0.0.1:8080/method/
```
```bash
# online score
$ curl -X POST -H "Content-Type: application/json" -d '{"arguments": {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1}, "account": "horns&hoofs", "login": "h&f", "token": "55cc9ce545bcd144300fe9efc28e65d415b923ebb6be1e19d2750a2c03e80dd209a27954dca045e5bb12418e7d89b6d718a9e35af34e14e1d5bcd5a08f21fc95", "method": "online_score"}' http://127.0.0.1:8080/method/
```
