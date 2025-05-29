# Weather App

Приложение для просмотра прогноза погоды с использованием OpenWeatherMap API. Позволяет получать прогноз на 1–5 дней с детализацией по времени суток (утро, день, вечер, ночь). Поддерживает автодополнение городов, историю поиска и перевод описаний погоды на русский язык.

## Требования

- Python 3.13
- Docker и Docker Compose (для запуска в контейнере)
- API-ключ от OpenWeatherMap (получите на https://openweathermap.org/)

## Установка и запуск без Docker

### 1. Клонируйте репозиторий

```bash
git clone https://github.com/<your-username>/weather_app.git
cd weather_app
