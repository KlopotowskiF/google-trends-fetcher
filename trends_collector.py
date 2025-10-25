#!/usr/bin/env python3
import json
import logging
from datetime import datetime
from typing import Dict, List, Any
import time
import yaml

try:
    from serpapi import GoogleSearch
except ImportError:
    print("Błąd: Biblioteka google-search-results nie jest zainstalowana.")
    print("Zainstaluj ją używając: pip install google-search-results")
    exit(1)


class TrendsCollector:
    def __init__(self, config_file: str = "config.yaml"):
        self.config = self.load_config(config_file)
        self.api_key = self.config.get('serpapi_key')
        if not self.api_key:
            raise ValueError("Brak serpapi_key w pliku konfiguracyjnym!")
        self.setup_logging()
    
    def load_config(self, config_file: str) -> Dict[str, Any]:
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logging.error(f"Plik konfiguracyjny {config_file} nie został znaleziony")
            raise
        except yaml.YAMLError as e:
            logging.error(f"Błąd parsowania pliku YAML {config_file}: {e}")
            raise
    
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('trends_collector.log'),
                logging.StreamHandler()
            ]
        )
    
    def collect_trending_searches(self, region_code: str, region_name: str) -> Dict[str, Any]:
        """Zbiera trending searches z SerpAPI Google Trends"""
        try:
            logging.info(f"Zbieranie trending searches dla regionu: {region_name} ({region_code})")
            
            # Używamy regionalnych trending searches z parametrem geo
            params = {
                "api_key": self.api_key,
                "engine": "google_trends_trending_now",
                "geo": region_code
            }
            
            search = GoogleSearch(params)
            results = search.get_dict()
            
            trending_data = {
                'region_name': region_name,
                'region_code': region_code,
                'collection_time': datetime.now().isoformat(),
                'trending_searches': [],
                'source': 'SerpAPI Google Trends',
                'note': 'Global trending searches (region-specific may not be available)'
            }
            
            if 'trending_searches' in results:
                count = self.config.get('trending_searches', {}).get('count', 20)
                trending_list = results['trending_searches'][:count]
                
                for trend in trending_list:
                    trend_data = {
                        'query': trend.get('query', ''),
                        'search_volume': trend.get('search_volume', 0),
                        'increase_percentage': trend.get('increase_percentage', 0),
                        'active': trend.get('active', True),
                        'categories': trend.get('categories', []),
                        'related_queries': trend.get('trend_breakdown', []),
                        'start_timestamp': trend.get('start_timestamp', 0)
                    }
                    trending_data['trending_searches'].append(trend_data)
                
                logging.info(f"Pomyślnie zebrano {len(trending_data['trending_searches'])} trending searches dla regionu: {region_name}")
            else:
                logging.warning(f"Brak danych trending searches dla regionu: {region_name}")
                trending_data['error'] = 'Brak danych w odpowiedzi SerpAPI'
                if 'error' in results:
                    trending_data['api_error'] = results['error']
            
            return trending_data
            
        except Exception as e:
            logging.error(f"Błąd podczas zbierania trending searches dla regionu {region_name}: {str(e)}")
            return {
                'region_name': region_name,
                'region_code': region_code,
                'error': str(e),
                'collection_time': datetime.now().isoformat(),
                'source': 'SerpAPI Google Trends'
            }
    
    def collect_interest_over_time(self, keywords: List[str], region_code: str, region_name: str) -> Dict[str, Any]:
        """Zbiera interest over time z SerpAPI Google Trends"""
        try:
            logging.info(f"Zbieranie interest over time dla regionu: {region_name} ({region_code})")
            
            geo_mapping = {
                'PL': 'PL',
                'US': 'US', 
                'DE': 'DE',
                'GB': 'GB',
                'FR': 'FR'
            }
            
            geo_code = geo_mapping.get(region_code, region_code)
            
            params = {
                "api_key": self.api_key,
                "engine": "google_trends",
                "q": ",".join(keywords),
                "geo": geo_code,
                "date": self.config.get('timeframe', 'today 3-m')
            }
            
            search = GoogleSearch(params)
            results = search.get_dict()
            
            interest_data = {
                'region_name': region_name,
                'region_code': region_code,
                'collection_time': datetime.now().isoformat(),
                'keywords': keywords,
                'timeframe': self.config.get('timeframe', 'today 3-m'),
                'interest_over_time': {},
                'related_topics': {},
                'related_queries': {},
                'source': 'SerpAPI Google Trends'
            }
            
            # Interest over time
            if 'interest_over_time' in results:
                timeline = results['interest_over_time'].get('timeline_data', [])
                for data_point in timeline:
                    date_str = data_point.get('date', '')
                    values = data_point.get('values', [])
                    
                    if date_str and values:
                        interest_data['interest_over_time'][date_str] = {}
                        for i, keyword in enumerate(keywords):
                            if i < len(values):
                                interest_data['interest_over_time'][date_str][keyword] = values[i].get('value', 0)
            
            # Related topics
            if 'related_topics' in results:
                for keyword in keywords:
                    if keyword in results['related_topics']:
                        interest_data['related_topics'][keyword] = results['related_topics'][keyword]
            
            # Related queries  
            if 'related_queries' in results:
                for keyword in keywords:
                    if keyword in results['related_queries']:
                        interest_data['related_queries'][keyword] = results['related_queries'][keyword]
            
            logging.info(f"Pomyślnie zebrano interest over time dla regionu: {region_name}")
            return interest_data
            
        except Exception as e:
            logging.error(f"Błąd podczas zbierania interest over time dla regionu {region_name}: {str(e)}")
            return {
                'region_name': region_name,
                'region_code': region_code,
                'error': str(e),
                'collection_time': datetime.now().isoformat(),
                'source': 'SerpAPI Google Trends'
            }
    
    def collect_all_trends(self) -> Dict[str, Any]:
        keywords = self.config['keywords']
        regions = self.config['regions']
        trending_enabled = self.config.get('trending_searches', {}).get('enabled', False)
        
        all_data = {
            'metadata': {
                'collection_time': datetime.now().isoformat(),
                'keywords': keywords,
                'total_regions': len(regions),
                'timeframe': self.config.get('timeframe', 'today 3-m'),
                'trending_searches_enabled': trending_enabled,
                'source': 'SerpAPI Google Trends',
                'api_usage_note': 'Each request uses your SerpAPI quota'
            },
            'trending_searches_data': []
        }
        
        for i, region in enumerate(regions):
            region_name = region['name']
            region_code = region['code']
            
            logging.info(f"Przetwarzanie regionu {i+1}/{len(regions)}: {region_name}")
            
            # Interest over time wyłączone - zbieramy tylko trending searches
            
            # Zbieranie trending searches jeśli włączone
            if trending_enabled:
                trending_data = self.collect_trending_searches(region_code, region_name)
                all_data['trending_searches_data'].append(trending_data)
                time.sleep(2)  # Opóźnienie między zapytaniami
            
            if i < len(regions) - 1:
                time.sleep(3)  # Dłuższe opóźnienie między regionami
        
        return all_data
    
    def save_to_json(self, data: Dict[str, Any], filename: str = None):
        if filename is None:
            filename = self.config.get('output_file', 'trends_data.json')
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            logging.info(f"Dane zostały zapisane do pliku: {filename}")
            
            # Zapisz uproszczoną wersję dla agenta AI
            simple_data = self.create_simple_format(data)
            simple_filename = filename.replace('.json', '_simple.json')
            with open(simple_filename, 'w', encoding='utf-8') as f:
                json.dump(simple_data, f, ensure_ascii=False, indent=2)
            logging.info(f"Uproszczone dane dla agenta AI zapisane do: {simple_filename}")
            
        except Exception as e:
            logging.error(f"Błąd podczas zapisywania do pliku {filename}: {str(e)}")
            raise

    def create_simple_format(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Tworzy uproszczony format JSON tylko z trendującymi hasłami dla agenta AI"""
        simple_data = {
            'collection_time': data.get('metadata', {}).get('collection_time'),
            'regions': []
        }
        
        for region_data in data.get('trending_searches_data', []):
            region_trends = {
                'region_name': region_data.get('region_name'),
                'region_code': region_data.get('region_code'),
                'trending_queries': []
            }
            
            for trend in region_data.get('trending_searches', []):
                region_trends['trending_queries'].append({
                    'query': trend.get('query'),
                    'search_volume': trend.get('search_volume'),
                    'increase_percentage': trend.get('increase_percentage'),
                    'category': trend.get('categories', [{}])[0].get('name', 'Unknown') if trend.get('categories') else 'Unknown'
                })
            
            simple_data['regions'].append(region_trends)
        
        return simple_data
    
    def run(self):
        try:
            logging.info("Rozpoczynanie zbierania danych Google Trends")
            data = self.collect_all_trends()
            self.save_to_json(data)
            logging.info("Zbieranie danych zakończone pomyślnie")
            
            # Podsumowanie użycia API - tylko trending searches
            total_requests = len(self.config.get('regions', []))
            logging.info(f"Wykorzystano około {total_requests} zapytań SerpAPI")
            
            return data
        except Exception as e:
            logging.error(f"Błąd podczas wykonywania programu: {str(e)}")
            raise


def main():
    try:
        collector = TrendsCollector()
        collector.run()
        print("Program zakończył się pomyślnie. Sprawdź plik z danymi i logi.")
    except Exception as e:
        print(f"Błąd: {str(e)}")
        exit(1)


if __name__ == "__main__":
    main()