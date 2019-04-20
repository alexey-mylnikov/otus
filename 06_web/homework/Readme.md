# IP2W
## Задача
Написать uWSGI демон для CentOS/7, который по запросу на IPv4 адрес возвращает текущую погоду в городе, к которому относится IP, в виде json.

### Код
Скачать репозиторий:
```bash
$ git clone https://github.com/alexey-mylnikov/otus
# or via ssh
$ git clone ssh://git@github.com/alexey-mylnikov/otus
$ cd otus/06_web/homework/
```

Содержимое папки homework:
* `ip2w.py` - исходный код приложения,
* `test.py` - исходный код функциональных тестов,
* `ip2w.conf` - конфигурационный файл приложения,
* `ip2w.ini` - конфигурационный файл uWSGI,
* `ip2w.nginx.conf` - конфигурационный файл nginx,
* `ip2w.service` - сервисный файл systemd,
* `ip2w.spec` - инструкции по сборке .rpm пакета,
* `ip2w-0.0.1-1.noarch.rpm` - пакет с программой,


### Необходимые зависимости
* `python`
* `python-requests`
* `uwsgi`
* `uwsgi-plugin-python2`
* `uwsgi-logger-file`

### Установка
```bash
$ sudo rpm -U ip2w-0.0.1-1.noarch.rpm
$ sudo cp ip2w.nginx.conf /etc/nginx/conf.d/
```

### Настройка
Перед запуском необходимо сгенерировать API токен на сайте [openweathermap](https://openweathermap.org/api "OpenWeatherMap")
и поместить в файл `/usr/local/etc/ip2w.conf` в формате `OPENWEATHER_TOKEN=123456`.

### Запуск
```bash
$ sudo systemctl enable ip2w.service
$ sudo systemctl start ip2w.service
$ sudo systemctl enable nginx.service
$ sudo systemctl start nginx.service
```

### Запуск тестов
```bash
$ python test.py
```

### Пример запроса
```bash
$ curl -v -X GET http://127.0.0.1:8080/ip2w/176.14.221.123
*   Trying 127.0.0.1...
* TCP_NODELAY set
* Connected to 127.0.0.1 (127.0.0.1) port 8080 (#0)
> GET /ip2w/176.14.221.123 HTTP/1.1
> Host: 127.0.0.1:8080
> User-Agent: curl/7.54.0
> Accept: */*
> 
< HTTP/1.1 200 OK
< Server: nginx/1.12.2
< Date: Sat, 20 Apr 2019 20:46:28 GMT
< Content-Type: application/json
< Transfer-Encoding: chunked
< Connection: keep-alive
< 
* Connection #0 to host 127.0.0.1 left intact
{"city": "Sviblovo", "conditions": "clear sky", "temp": 7.17}
```

### Примечание
Если на все запросы, сервис отвечает 502 ошибкой, нужно проделать шаги из данного [ответа](https://stackoverflow.com/a/24830777 "StackOverflow").
