from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.sessions.middleware import SessionMiddleware
from django.test.client import RequestFactory
from unittest.mock import patch, MagicMock
from weather.models import SearchHistory
from weather.views import weather_view

class WeatherAppTests(TestCase):
    def setUp(self):
        # Настройка тестового клиента и пользователя
        self.client = Client()
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.login(username='testuser', password='testpass')

    # Тест 1: Проверка отображения главной страницы
    def test_weather_page_loads(self):
        response = self.client.get(reverse('weather:weather'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'weather/weather.html')

    # Тест 2: Проверка отправки формы и получения прогноза
    @patch('requests.get')
    def test_weather_forecast_request(self, mock_get):
        # Подменяем ответ от OpenWeatherMap API
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'list': [
                {
                    'dt_txt': '2025-05-28 00:00:00',
                    'main': {'temp': 20.0},
                    'weather': [{'description': 'clear sky', 'icon': '01d'}]
                },
                {
                    'dt_txt': '2025-05-28 03:00:00',
                    'main': {'temp': 21.0},
                    'weather': [{'description': 'few clouds', 'icon': '02d'}]
                },
                {
                    'dt_txt': '2025-05-28 06:00:00',
                    'main': {'temp': 22.0},
                    'weather': [{'description': 'scattered clouds', 'icon': '03d'}]
                },
                {
                    'dt_txt': '2025-05-28 09:00:00',
                    'main': {'temp': 23.0},
                    'weather': [{'description': 'broken clouds', 'icon': '04d'}]
                }
            ]
        }
        mock_get.return_value = mock_response

        response = self.client.post(reverse('weather:weather'), {
            'city': 'Moscow',
            'period_days': 1,
            'csrfmiddlewaretoken': self.client.cookies.get('csrftoken', '')
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ясное небо')
        self.assertContains(response, 'Moscow')

    # Тест 3: Проверка, что история сохраняется для авторизованного пользователя
    @patch('requests.get')
    def test_history_save_authenticated_user(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'list': [
                {
                    'dt_txt': '2025-05-28 00:00:00',
                    'main': {'temp': 20.0},
                    'weather': [{'description': 'clear sky', 'icon': '01d'}]
                }
            ]
        }
        mock_get.return_value = mock_response

        self.client.post(reverse('weather:weather'), {
            'city': 'Moscow',
            'period_days': 1,
            'csrfmiddlewaretoken': self.client.cookies.get('csrftoken', '')
        })
        history = SearchHistory.objects.filter(user=self.user)
        self.assertEqual(history.count(), 1)
        self.assertEqual(history.first().city, 'Moscow')
        self.assertEqual(history.first().period, 1)

    # Тест 4: Проверка, что история сохраняется для неавторизованного пользователя
    @patch('requests.get')
    def test_history_save_unauthenticated_user(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'list': [
                {
                    'dt_txt': '2025-05-28 00:00:00',
                    'main': {'temp': 20.0},
                    'weather': [{'description': 'clear sky', 'icon': '01d'}]
                }
            ]
        }
        mock_get.return_value = mock_response

        self.client.logout()
        response = self.client.post(reverse('weather:weather'), {
            'city': 'London',
            'period_days': 2,
            'csrfmiddlewaretoken': self.client.cookies.get('csrftoken', '')
        })
        self.assertEqual(response.status_code, 200)

        # Проверяем сессию через GET-запрос
        response = self.client.get(reverse('weather:weather'))
        history = response.context['history']
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]['city'], 'London')
        self.assertEqual(history[0]['period'], 2)

    # Тест 5: Проверка, что история ограничивается 10 записями (авторизованный пользователь)
    @patch('requests.get')
    def test_history_limit_authenticated_user(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'list': [
                {
                    'dt_txt': '2025-05-28 00:00:00',
                    'main': {'temp': 20.0},
                    'weather': [{'description': 'clear sky', 'icon': '01d'}]
                }
            ]
        }
        mock_get.return_value = mock_response

        for i in range(12):
            self.client.post(reverse('weather:weather'), {
                'city': f'City{i}',
                'period_days': 1,
                'csrfmiddlewaretoken': self.client.cookies.get('csrftoken', '')
            })
        history = SearchHistory.objects.filter(user=self.user)
        self.assertEqual(history.count(), 10)

    # Тест 6: Проверка, что история ограничивается 10 записями (неавторизованный пользователь)
    @patch('requests.get')
    def test_history_limit_unauthenticated_user(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'list': [
                {
                    'dt_txt': '2025-05-28 00:00:00',
                    'main': {'temp': 20.0},
                    'weather': [{'description': 'clear sky', 'icon': '01d'}]
                }
            ]
        }
        mock_get.return_value = mock_response

        self.client.logout()
        for i in range(12):
            response = self.client.post(reverse('weather:weather'), {
                'city': f'City{i}',
                'period_days': 1,
                'csrfmiddlewaretoken': self.client.cookies.get('csrftoken', '')
            })
            self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('weather:weather'))
        history = response.context['history']
        self.assertEqual(len(history), 10)

    # Тест 7: Проверка перевода описания погоды
    @patch('requests.get')
    def test_weather_description_translation(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'list': [
                {
                    'dt_txt': '2025-05-28 00:00:00',
                    'main': {'temp': 20.0},
                    'weather': [{'description': 'clear sky', 'icon': '01d'}]
                }
            ]
        }
        mock_get.return_value = mock_response

        response = self.client.post(reverse('weather:weather'), {
            'city': 'Moscow',
            'period_days': 1,
            'csrfmiddlewaretoken': self.client.cookies.get('csrftoken', '')
        })
        self.assertContains(response, 'ясное небо')

    # Тест 8: Проверка формата даты (месяц-день)
    @patch('requests.get')
    def test_date_format(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'list': [
                {
                    'dt_txt': '2025-05-28 00:00:00',
                    'main': {'temp': 20.0},
                    'weather': [{'description': 'clear sky', 'icon': '01d'}]
                }
            ]
        }
        mock_get.return_value = mock_response

        response = self.client.post(reverse('weather:weather'), {
            'city': 'Moscow',
            'period_days': 1,
            'csrfmiddlewaretoken': self.client.cookies.get('csrftoken', '')
        })
        self.assertContains(response, '05-28')

    # Тест 9: Проверка ошибки API
    @patch('requests.get')
    def test_api_error_handling(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "City not found"
        mock_get.return_value = mock_response

        response = self.client.post(reverse('weather:weather'), {
            'city': 'InvalidCity',
            'period_days': 1,
            'csrfmiddlewaretoken': self.client.cookies.get('csrftoken', '')
        })
        self.assertEqual(response.status_code, 200)
        print(response.content.decode('utf-8'))  # Отладка: выводим содержимое ответа
        self.assertContains(response, 'Прогноз недоступен. Попробуйте другой город.')

    # Тест 10: Проверка отображения последней записи в "last_city"
    @patch('requests.get')
    def test_last_city_display(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'list': [
                {
                    'dt_txt': '2025-05-28 00:00:00',
                    'main': {'temp': 20.0},
                    'weather': [{'description': 'clear sky', 'icon': '01d'}]
                }
            ]
        }
        mock_get.return_value = mock_response

        self.client.post(reverse('weather:weather'), {
            'city': 'Paris',
            'period_days': 2,
            'csrfmiddlewaretoken': self.client.cookies.get('csrftoken', '')
        })
        response = self.client.get(reverse('weather:weather'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Посмотреть погоду в Paris?')