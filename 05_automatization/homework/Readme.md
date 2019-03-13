# OTUServer
## Задача
Разработать веб-сервер частично реализующий протокол HTTP.
Архитектура: пре-форк (unix), с асинхронной обработкой внутри воркеров.
## Код
Скачать репозиторий:
```bash
$ git clone https://github.com/alexey-mylnikov/otus
# or via ssh
$ git clone ssh://git@github.com/alexey-mylnikov/otus
$ cd otus/05_automatization/homework/
```
### Запуск HTTP сервера:
```bash
$ python httpd/httpd.py -a 127.0.0.1 -p 8080 -r ./rootfs/var/www/
```
### Запуск бенчмарк-тестов:
```bash
$ docker-compose up --build
```
### Результаты apache-bench:
```bash
Finished 50000 requests


Server Software:        OTUServer
Server Hostname:        httpd
Server Port:            8080

Document Path:          /
Document Length:        0 bytes

Concurrency Level:      100
Time taken for tests:   33.183 seconds
Complete requests:      50000
Failed requests:        0
Non-2xx responses:      50000
Total transferred:      5050000 bytes
HTML transferred:       0 bytes
Requests per second:    1506.80 [#/sec] (mean)
Time per request:       66.366 [ms] (mean)
Time per request:       0.664 [ms] (mean, across all concurrent requests)
Transfer rate:          148.62 [Kbytes/sec] received

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0   52 263.4      0    7237
Processing:     0   13  68.3      3    6654
Waiting:        0   12  68.2      2    6653
Total:          0   64 290.5      3    7712

Percentage of the requests served within a certain time (ms)
  50%      3
  66%      8
  75%     10
  80%     12
  90%     20
  95%    219
  98%   1068
  99%   1261
 100%   7712 (longest request)
```
