import requests
from django.shortcuts import render
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Count
from .models import SearchHistory
from .serializers import CityStatsSerializer
from datetime import datetime

def get_weather(city, period_days):
    api_key = settings.OPENWEATHERMAP_API_KEY
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}&units=metric"
    response = requests.get(url)
    
    weather_translations = {
        'clear sky': 'ясное небо',
        'few clouds': 'малооблачно',
        'scattered clouds': 'рассеянные облака',
        'broken clouds': 'облачно',
        'overcast clouds': 'пасмурно',
        'light rain': 'небольшой дождь',
        'moderate rain': 'умеренный дождь',
        'heavy intensity rain': 'сильный дождь',
        'shower rain': 'ливень',
        'thunderstorm': 'гроза',
        'snow': 'снег',
        'light snow': 'небольшой снег',
        'heavy snow': 'сильный снег',
        'mist': 'туман',
        'fog': 'густой туман',
    }

    if response.status_code == 200:
        data = response.json()
        forecast_list = data['list']
        
        forecast_by_day = {}
        for item in forecast_list:
            date_str = item['dt_txt'].split(' ')[0]
            time = item['dt_txt'].split(' ')[1]
            date = datetime.strptime(date_str, '%Y-%m-%d')
            if date not in forecast_by_day:
                forecast_by_day[date] = []
            description = item['weather'][0]['description']
            translated_description = weather_translations.get(description.lower(), description)
            forecast_by_day[date].append({
                'time': time,
                'temp': item['main']['temp'],
                'description': translated_description,
                'icon': item['weather'][0]['icon']
            })
        forecast_by_day = dict(list(forecast_by_day.items())[:period_days])

        #для каждого дня выбираем 4 времени - утро, день, вечер и ночь
        result = {}
        for date, entries in forecast_by_day.items():
            periods = []
            entries.sort(key=lambda x: x['time'])
            total_entries = len(entries)
            if total_entries < 4:
                while len(entries) < 4:
                    entries.append(entries[0])
            indices = [0, total_entries//4, total_entries//2, total_entries-1]
            labels = ['Ночь', 'Утро', 'День', 'Вечер']
            for i, label in zip(indices, labels):
                entry = entries[i]
                periods.append({
                    'time': label,
                    'temp': entry['temp'],
                    'description': entry['description'],
                    'icon': entry['icon']
                })
            result[date] = periods

        return result
    print(f"Ошибка API: {response.status_code} - {response.text}")
    return {}

def weather_view(request):
    last_city = None
    history = []
    forecast = {}

    if request.user.is_authenticated:
        last_search = SearchHistory.objects.filter(user=request.user).first()
        if last_search:
            last_city = last_search.city
    else:
        last_city = request.session.get('last_city')

    if request.method == 'POST':
        city = request.POST.get('city')
        period_days = int(request.POST.get('period_days', 1))
        
        forecast = get_weather(city, period_days)

        if forecast:
            if request.user.is_authenticated:
                existing = SearchHistory.objects.filter(user=request.user, city=city, period=period_days).first()
                if not existing:
                    SearchHistory.objects.create(user=request.user, city=city, period=period_days)
                all_entries = SearchHistory.objects.filter(user=request.user).order_by('-timestamp')
                if all_entries.count() > 10:
                    ids_to_keep = list(all_entries[:10].values_list('id', flat=True))
                    SearchHistory.objects.filter(user=request.user).exclude(id__in=ids_to_keep).delete()
            else:
                request.session['last_city'] = city
                if 'history' not in request.session:
                    request.session['history'] = []
                current_history = request.session.get('history', [])
                new_entry = {'city': city, 'period': period_days}
                if new_entry not in current_history:
                    request.session['history'] = [new_entry] + current_history
                request.session['history'] = request.session['history'][:10]
                request.session.modified = True

    if request.user.is_authenticated:
        history = SearchHistory.objects.filter(user=request.user).order_by('-timestamp')[:10]
    else:
        history = request.session.get('history', [])[:10]

    return render(request, 'weather/weather.html', {
        'forecast': forecast,
        'last_city': last_city,
        'history': history,
    })

class CityStatsView(APIView):
    def get(self, request):
        stats = SearchHistory.objects.values('city').annotate(count=Count('city')).order_by('-count')
        serializer = CityStatsSerializer(stats, many=True)
        return Response(serializer.data)