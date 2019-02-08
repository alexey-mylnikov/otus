# Log Analyzer
## Задача
Реализовать анализатор логов
### Код
Скачать репозиторий:
```bash
$ git clone https://github.com/alexey-mylnikov/otus
# or via ssh
$ git clone ssh://git@github.com/alexey-mylnikov/otus
```
### Запуск
```bash
$ cd otus/01_advanced_basics/homework/01_log_analyzer
```
#### Боевой
```bash
$ python log_analyzer/log_analyzer.py -c config.json
```
#### Юнит-тесты
```bash
$ python -m unittest test.unit.test_log_analyzer
```
#### Интеграционные тесты
```bash
$ python -m unittest tests.integration.test_log_analyzer
```