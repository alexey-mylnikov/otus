# MemcLoad
## Задача
Написать более производительную версию memc_load.py.
## Код
Скачать репозиторий:
```bash
$ git clone https://github.com/alexey-mylnikov/otus
# or via ssh
$ git clone ssh://git@github.com/alexey-mylnikov/otus
$ cd otus/12_concurrency/homework/
```
### Запуск
```bash
$ python memc_load.py --pattern /data/appsinstalled/*.gz --processes 8
```
### Время выполнения
#### Система
```bash
CPU: Intel(R) Core(TM) i5-4460  CPU @ 3.20GHz
HDD: ADATA SP550 (SSD)
```
#### Оригинальный вариант
```bash
$ time python memc_load.orig.py
[2019.04.29 21:50:12] I Memc loader started with options: {'dry': False, 'log': None, 'pattern': '/data/appsinstalled/*.tsv.gz', 'idfa': '127.0.0.1:33013', 'dvid': '127.0.0.1:33016', 'test': False, 'adid': '127.0.0.1:33015', 'gaid': '127.0.0.1:33014'}
[2019.04.29 21:50:12] I Processing /data/appsinstalled/20170929000200.tsv.gz
[2019.04.29 22:05:06] I Acceptable error rate (0.0). Successfull load
[2019.04.29 22:05:06] I Processing /data/appsinstalled/20170929000100.tsv.gz
[2019.04.29 22:19:52] I Acceptable error rate (0.0). Successfull load
[2019.04.29 22:19:52] I Processing /data/appsinstalled/20170929000000.tsv.gz
[2019.04.29 22:34:35] I Acceptable error rate (0.0). Successfull load

real    44m23,154s
user    40m26,621s
sys     3m54,913s
```
#### Асинхронный вариант вариант (8 процессов)
```bash
$ time python memc_load.py
[2019.06.08 18:46:27] I Memc loader started with options: {'dry': False, 'processes': 4, 'log': None, 'pattern': '/data/appsinstalled/*.tsv.gz', 'idfa': '127.0.0.1:33013', 'dvid': '127.0.0.1:33016', 'timeout': 30, 'test': False, 'adid': '127.0.0.1:33015', 'gaid': '127.0.0.1:33014'}
[2019.06.08 18:46:27] I Processing /data/appsinstalled/20170929000200.tsv.gz
[2019.06.08 18:52:39] I Acceptable error rate (0.0). Successfull load
[2019.06.08 18:52:39] I Processing /data/appsinstalled/20170929000100.tsv.gz
[2019.06.08 18:59:26] I Acceptable error rate (0.0). Successfull load
[2019.06.08 18:59:26] I Processing /data/appsinstalled/20170929000000.tsv.gz
[2019.06.08 19:05:58] I Acceptable error rate (0.0). Successfull load

real    19m31,062s
user    44m34,490s
sys     6m42,012s
```

