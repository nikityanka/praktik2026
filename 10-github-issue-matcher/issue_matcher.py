#!/usr/bin/env python3
"""
GitHub Issue Matcher

Анализирует GitHub-профиль разработчика и подбирает релевантные issues
с лейблом good-first-issue на основе его стека технологий.
"""

import os
import sys
import argparse
import json
import hashlib
import time
from pathlib import Path
from typing import List, Dict, Optional
from collections import Counter
import requests
import google.generativeai as genai
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Конфигурация
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
CACHE_DIR = Path('.cache')
CACHE_EXPIRY = 3600  # 1 час

class Cache:
    """Простое кэширование для экономии API запросов"""
    
    def __init__(self, cache_dir: Path = CACHE_DIR):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(exist_ok=True)
    
    def _get_cache_key(self, key: str) -> str:
        """Генерирует хэш для ключа кэша"""
        return hashlib.md5(key.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Dict]:
        """Получает данные из кэша"""
        cache_file = self.cache_dir / f"{self._get_cache_key(key)}.json"
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Проверяем срок действия
            if time.time() - data['timestamp'] > CACHE_EXPIRY:
                cache_file.unlink()
                return None
            
            return data['value']
        except Exception:
            return None
    
    def set(self, key: str, value: Dict):
        """Сохраняет данные в кэш"""
        cache_file = self.cache_dir / f"{self._get_cache_key(key)}.json"
        
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'timestamp': time.time(),
                    'value': value
                }, f, ensure_ascii=False)
        except Exception:
            pass

class GitHubAnalyzer:
    """Анализатор GitHub профиля"""
    
    def __init__(self, username: str, token: Optional[str] = None):
        self.username = username
        self.token = token
        self.headers = {}
        self.cache = Cache()
        
        if token:
            self.headers['Authorization'] = f'token {token}'
    
    def get_user_repos(self) -> List[Dict]:
        """Получает репозитории пользователя"""
        cache_key = f"repos:{self.username}"
        cached = self.cache.get(cache_key)
        
        if cached is not None:
            return cached
        
        url = f'https://api.github.com/users/{self.username}/repos'
        params = {'per_page': 100, 'sort': 'updated'}
        
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        
        repos = response.json()
        self.cache.set(cache_key, repos)
        
        return repos
    
    def analyze_tech_stack(self, repos: List[Dict]) -> Dict:
        """Анализирует технологический стек из репозиториев"""
        languages = Counter()
        topics = Counter()
        
        for repo in repos:
            # Собираем языки
            if repo.get('language'):
                languages[repo['language']] += 1
            
            # Собираем топики
            if repo.get('topics'):
                for topic in repo['topics']:
                    topics[topic] += 1
        
        return {
            'languages': dict(languages.most_common(10)),
            'topics': dict(topics.most_common(20)),
            'total_repos': len(repos)
        }
    
    def search_issues(self, languages: List[str], topics: List[str], 
                     limit: int = 100) -> List[Dict]:
        """Ищет issues с good-first-issue"""
        cache_key = f"issues:{','.join(languages[:5])}:{','.join(topics[:5])}"
        cached = self.cache.get(cache_key)
        
        if cached is not None:
            return cached
        
        # Формируем поисковый запрос
        lang_query = ' OR '.join([f'language:{lang}' for lang in languages[:5]])
        topic_query = ' OR '.join([f'topic:{topic}' for topic in topics[:5]])
        
        query = f'label:"good-first-issue" state:open ({lang_query})'
        
        url = 'https://api.github.com/search/issues'
        params = {
            'q': query,
            'sort': 'updated',
            'per_page': min(limit, 100)
        }
        
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        
        issues = response.json()['items']
        self.cache.set(cache_key, issues)
        
        return issues

def rank_issues(issues: List[Dict], tech_stack: Dict) -> List[Dict]:
    """Ранжирует issues по релевантности с помощью LLM"""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY не установлен в переменных окружения")
    
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    # Формируем описание стека
    stack_description = f"""
Языки программирования: {', '.join(tech_stack['languages'].keys())}
Технологии и фреймворки: {', '.join(tech_stack['topics'].keys())}
"""
    
    # Формируем список issues для анализа
    issues_text = ""
    for i, issue in enumerate(issues[:20], 1):  # Анализируем топ-20
        repo_name = issue['repository_url'].split('/')[-2:]
        issues_text += f"\n{i}. [{'/'.join(repo_name)}] {issue['title']}\n"
        issues_text += f"   URL: {issue['html_url']}\n"
        if issue.get('labels'):
            labels = [l['name'] for l in issue['labels']]
            issues_text += f"   Labels: {', '.join(labels)}\n"
    
    prompt = f"""Проанализируй следующие GitHub issues и отранжируй их по релевантности для разработчика со следующим стеком:

{stack_description}

Issues:
{issues_text}

Для каждого issue оцени релевантность от 1 до 10 и дай краткое обоснование.

Верни результат в JSON формате:
{{
  "rankings": [
    {{
      "issue_number": 1,
      "score": 9,
      "reason": "Краткое обоснование релевантности"
    }}
  ]
}}

Сортируй по убыванию score. Верни ТОЛЬКО JSON без дополнительного текста.

JSON:"""

    response = model.generate_content(prompt)
    json_text = response.text.strip()
    
    # Убираем markdown блоки если есть
    if json_text.startswith('```json'):
        json_text = json_text.split('```json', 1)[1]
        json_text = json_text.rsplit('```', 1)[0]
    elif json_text.startswith('```'):
        json_text = json_text.split('```', 1)[1]
        json_text = json_text.rsplit('```', 1)[0]
    
    try:
        rankings = json.loads(json_text.strip())
        
        # Применяем ранжирование
        ranked_issues = []
        for rank in rankings['rankings']:
            issue_idx = rank['issue_number'] - 1
            if issue_idx < len(issues):
                issue = issues[issue_idx].copy()
                issue['relevance_score'] = rank['score']
                issue['relevance_reason'] = rank['reason']
                ranked_issues.append(issue)
        
        return ranked_issues
    
    except json.JSONDecodeError as e:
        print(f"Ошибка парсинга JSON: {e}", file=sys.stderr)
        # Возвращаем issues без ранжирования
        return issues[:10]

def format_output(issues: List[Dict], format_type: str = 'text') -> str:
    """Форматирует результаты"""
    if format_type == 'json':
        output_data = []
        for issue in issues:
            repo_url = issue['repository_url'].replace('https://api.github.com/repos/', 'https://github.com/')
            output_data.append({
                'title': issue['title'],
                'url': issue['html_url'],
                'repository': repo_url,
                'labels': [l['name'] for l in issue.get('labels', [])],
                'relevance_score': issue.get('relevance_score', 0),
                'relevance_reason': issue.get('relevance_reason', '')
            })
        return json.dumps(output_data, ensure_ascii=False, indent=2)
    
    elif format_type == 'markdown':
        output = "# Рекомендованные GitHub Issues\n\n"
        
        for i, issue in enumerate(issues, 1):
            repo_url = issue['repository_url'].replace('https://api.github.com/repos/', 'https://github.com/')
            
            output += f"## {i}. {issue['title']}\n\n"
            output += f"**Репозиторий:** [{repo_url}]({repo_url})\n\n"
            output += f"**Issue:** {issue['html_url']}\n\n"
            
            if issue.get('labels'):
                labels = ', '.join([f"`{l['name']}`" for l in issue['labels']])
                output += f"**Labels:** {labels}\n\n"
            
            if issue.get('relevance_score'):
                output += f"**Релевантность:** {issue['relevance_score']}/10\n\n"
                output += f"**Обоснование:** {issue['relevance_reason']}\n\n"
            
            output += "---\n\n"
        
        return output
    
    else:  # text
        output = "=" * 70 + "\n"
        output += "РЕКОМЕНДОВАННЫЕ GITHUB ISSUES\n"
        output += "=" * 70 + "\n\n"
        
        for i, issue in enumerate(issues, 1):
            repo_url = issue['repository_url'].replace('https://api.github.com/repos/', 'https://github.com/')
            
            output += f"{i}. {issue['title']}\n"
            output += f"   Репозиторий: {repo_url}\n"
            output += f"   Issue: {issue['html_url']}\n"
            
            if issue.get('labels'):
                labels = ', '.join([l['name'] for l in issue['labels']])
                output += f"   Labels: {labels}\n"
            
            if issue.get('relevance_score'):
                output += f"   Релевантность: {issue['relevance_score']}/10\n"
                output += f"   Обоснование: {issue['relevance_reason']}\n"
            
            output += "\n"
        
        output += "=" * 70
        return output

def main():
    parser = argparse.ArgumentParser(
        description='GitHub Issue Matcher - подбор issues под стек разработчика',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  %(prog)s username
  %(prog)s username --top 5
  %(prog)s username --format markdown --output issues.md
  %(prog)s username --format json

Переменные окружения:
  GITHUB_TOKEN     - GitHub Personal Access Token (опционально, для увеличения rate limit)
  GEMINI_API_KEY   - Google Gemini API Key (обязательно)
        """
    )
    
    parser.add_argument(
        'username',
        help='GitHub username'
    )
    
    parser.add_argument(
        '--top', '-t',
        type=int,
        default=10,
        help='Количество issues в результате (по умолчанию: 10)'
    )
    
    parser.add_argument(
        '--format', '-f',
        choices=['text', 'markdown', 'json'],
        default='text',
        help='Формат вывода (по умолчанию: text)'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        help='Сохранить результат в файл'
    )
    
    args = parser.parse_args()
    
    # Проверяем API ключ
    if not GEMINI_API_KEY:
        print("Ошибка: GEMINI_API_KEY не установлен", file=sys.stderr)
        sys.exit(1)
    
    print(f"Анализирую профиль @{args.username}...", file=sys.stderr)
    
    try:
        # Создаем анализатор
        analyzer = GitHubAnalyzer(args.username, GITHUB_TOKEN)
        
        # Получаем репозитории
        repos = analyzer.get_user_repos()
        print(f"✓ Найдено {len(repos)} репозиториев", file=sys.stderr)
        
        # Анализируем стек
        tech_stack = analyzer.analyze_tech_stack(repos)
        print(f"✓ Определен стек:", file=sys.stderr)
        print(f"  Языки: {', '.join(list(tech_stack['languages'].keys())[:5])}", file=sys.stderr)
        print(f"  Технологии: {', '.join(list(tech_stack['topics'].keys())[:5])}", file=sys.stderr)
        
        # Ищем issues
        print("\nИщу подходящие issues...", file=sys.stderr)
        issues = analyzer.search_issues(
            list(tech_stack['languages'].keys()),
            list(tech_stack['topics'].keys()),
            limit=100
        )
        print(f"✓ Найдено {len(issues)} issues с good-first-issue", file=sys.stderr)
        
        if not issues:
            print("\nНе найдено подходящих issues", file=sys.stderr)
            sys.exit(0)
        
        # Ранжируем issues
        print("\nРанжирую issues по релевантности...", file=sys.stderr)
        ranked_issues = rank_issues(issues, tech_stack)
        print("✓ Ранжирование завершено\n", file=sys.stderr)
        
        # Берем топ-N
        top_issues = ranked_issues[:args.top]
        
        # Форматируем результат
        formatted_output = format_output(top_issues, args.format)
        
        # Выводим или сохраняем
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(formatted_output)
            print(f"✓ Результат сохранен в '{args.output}'", file=sys.stderr)
        else:
            print(formatted_output)
    
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"Ошибка: пользователь '{args.username}' не найден", file=sys.stderr)
        elif e.response.status_code == 403:
            print("Ошибка: превышен rate limit GitHub API. Используйте GITHUB_TOKEN", file=sys.stderr)
        else:
            print(f"Ошибка GitHub API: {e}", file=sys.stderr)
        sys.exit(1)
    
    except Exception as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()


