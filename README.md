# weather-notifier-bot
Небольшой погодный бот для телеграм с использованием openweathermap API

## Что интересного:
- Использует **openweathermap API** для составления прогнозов на текущий час и на день
- Отправка погоды в заданное время (утром)
- Использование **MongoDB** для хранения записей пользователей и обновления их прогнозов
- Обернут в **docker**-контейнер
- **flake8, isort и black** для чистоты кодовой базы

### Запуск в контейнере
- Создать файл .env скопировав готовый пример:
```shell
cp .env.example .env
```
- Заполнить файл с переменными своими значениями
- Собрать и запустить контейнер командой (опционально
  с ключом _-d_)
```shell
docker compose up 
```

### Локальный запуск
- Заполнить файл ``bot/settings.py`` с переменными ключей своими значениями
- Установить зависимости с помощью Poetry ``poetry install`` (опционально - в виртуальной среде)
- Запустить бота командой ``python main.py``
