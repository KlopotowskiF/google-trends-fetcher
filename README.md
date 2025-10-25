# Google Trends Data Collector

Program do zbierania danych z Google Trends przez SerpAPI z konfiguracją regionów i zapisem do pliku JSON.

## Instalacja

1. Zainstaluj wymagane biblioteki:
```bash
pip install -r requirements.txt
```

2. Ustaw swój SerpAPI key w `config.json`

## Użycie

```bash
python trends_collector.py
```

## Konfiguracja (config.yaml)

Program automatycznie używa `config.yaml` (z komentarzami) lub `config.json`.

```yaml
# API Configuration
serpapi_key: "your_api_key_here"  # Twój klucz SerpAPI (wymagany)

# Keywords (obecnie wyłączone)
keywords: []  # Lista słów kluczowych (pusta = oszczędza zapytania API)

# Regions Configuration  
regions:
  - name: "Poland"        # Nazwa regionu
    code: "PL"           # Kod kraju ISO (PL, US, DE, GB, FR, etc.)
  - name: "United States"
    code: "US"

# Output Configuration
output_file: "trends_data.json"  # Nazwa pliku (+ _simple.json dla agenta AI)

# Trending Searches Configuration
trending_searches:
  enabled: true     # Czy zbierać trending searches
  count: 20        # Ile haseł pobrać (max 25)
```

## Funkcje

✅ **Trending searches** - aktualne popularne wyszukiwania  
✅ **Multiple regions** - prawdziwe regionalne trendy (PL, US, etc.)  
✅ **Real Google data** - świeże dane z Google Trends  
✅ **Simple format** - uproszczony JSON dla agenta AI  

## Dane wyjściowe

Program zapisuje 2 pliki:
- `trends_data.json`: pełne dane z SerpAPI
- `trends_data_simple.json`: uproszczony format dla agenta AI

Format dla agenta AI zawiera tylko:
- `query`: trendujące hasło
- `search_volume`: liczba wyszukiwań  
- `increase_percentage`: procentowy wzrost
- `category`: kategoria (Sports, Entertainment, etc.)

## Koszty

Używa SerpAPI - 250 zapytań darmowo/miesiąc