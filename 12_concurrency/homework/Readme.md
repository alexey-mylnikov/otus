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
[2019.04.29 22:05:06] I Processed: 3422026, errors: 0
[2019.04.29 22:05:06] I Processing /data/appsinstalled/20170929000100.tsv.gz
[2019.04.29 22:19:52] I Acceptable error rate (0.0). Successfull load
[2019.04.29 22:19:52] I Processed: 3424477, errors: 0
[2019.04.29 22:19:52] I Processing /data/appsinstalled/20170929000000.tsv.gz
[2019.04.29 22:34:35] I Acceptable error rate (0.0). Successfull load
[2019.04.29 22:34:35] I Processed: 3422995, errors: 0

real    44m23,154s
user    40m26,621s
sys     3m54,913s
```
#### Асинхронный вариант вариант (8 процессов)
```bash
$ time python memc_load.py --processes 8
[2019.04.29 21:30:00] I Memc loader started with options: {'dry': False, 'processes': '8', 'log': None, 'pattern': '/data/appsinstalled/*.gz', 'idfa': '127.0.0.1:11211', 'dvid': '127.0.0.1:11211', 'test': False, 'adid': '127.0.0.1:11211', 'gaid': '127.0.0.1:11211'}
[2019.04.29 21:30:00] I Processing: /data/appsinstalled/20170929000000.tsv.gz
[2019.04.29 21:35:34] I Acceptable error rate (0.0). Successfull load
[2019.04.29 21:35:34] I /data/appsinstalled/20170929000000.tsv.gz processed: 3422995, errors: 0
[2019.04.29 21:35:34] I Processing: /data/appsinstalled/20170929000100.tsv.gz
[2019.04.29 21:41:13] I Acceptable error rate (0.0). Successfull load
[2019.04.29 21:41:13] I /data/appsinstalled/20170929000100.tsv.gz processed: 3424477, errors: 0
[2019.04.29 21:41:13] I Processing: /data/appsinstalled/20170929000200.tsv.gz
[2019.04.29 21:47:17] I Acceptable error rate (0.0). Successfull load
[2019.04.29 21:47:17] I /data/appsinstalled/20170929000200.tsv.gz processed: 3422026, errors: 0

real    17m16,924s
user    47m18,614s
sys     6m17,333s
```

