$(document).ready(function() {
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    $("#city").autocomplete({
        source: debounce(function(request, response) {
            $.ajax({
                url: "https://nominatim.openstreetmap.org/search",
                dataType: "json",
                data: {
                    q: request.term,
                    format: "json",
                    featureType: "city",
                    limit: 10
                },
                headers: {
                    'User-Agent': 'WeatherApp/1.0 (your-email@example.com)'
                },
                success: function(data) {
                    response($.map(data, function(item) {
                        const cityName = item.display_name.split(',')[0].trim();
                        return {
                            label: cityName,
                            value: cityName
                        };
                    }));
                },
                error: function(xhr, status, error) {
                    console.error("Ошибка автодополнения:", status, error);
                    response([]);
                }
            });
        }, 300), //задержка 300 мс
        minLength: 2 //минимальная длина ввода
    });
});