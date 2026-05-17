#!/usr/bin/env python3
"""
AI-powered Unit Test Generator

Генерирует unit-тесты для Python и JavaScript функций с использованием LLM.
Покрывает happy path, edge cases и обработку ошибок.
"""

import os
import sys
import ast
import argparse
import re
from pathlib import Path
from typing import List, Dict, Optional
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

class FunctionInfo:
    """Информация о функции"""
    def __init__(self, name: str, signature: str, body: str, docstring: Optional[str] = None):
        self.name = name
        self.signature = signature
        self.body = body
        self.docstring = docstring

def extract_python_functions(file_path: Path) -> List[FunctionInfo]:
    """Извлекает функции из Python файла с помощью AST"""
    with open(file_path, 'r', encoding='utf-8') as f:
        source = f.read()
    
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        print(f"Ошибка синтаксиса в файле: {e}", file=sys.stderr)
        return []
    
    functions = []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Пропускаем приватные функции и методы классов
            if node.name.startswith('_') and not node.name.startswith('__'):
                continue
            
            # Получаем сигнатуру
            args = []
            for arg in node.args.args:
                arg_str = arg.arg
                if arg.annotation:
                    arg_str += f": {ast.unparse(arg.annotation)}"
                args.append(arg_str)
            
            returns = ""
            if node.returns:
                returns = f" -> {ast.unparse(node.returns)}"
            
            signature = f"def {node.name}({', '.join(args)}){returns}"
            
            # Получаем тело функции
            body = ast.unparse(node)
            
            # Получаем docstring
            docstring = ast.get_docstring(node)
            
            functions.append(FunctionInfo(node.name, signature, body, docstring))
    
    return functions

def extract_javascript_functions(file_path: Path) -> List[FunctionInfo]:
    """Извлекает функции из JavaScript файла с помощью регулярных выражений"""
    with open(file_path, 'r', encoding='utf-8') as f:
        source = f.read()
    
    functions = []
    
    # Паттерны для различных типов функций
    patterns = [
        # function name(args) { ... }
        r'function\s+(\w+)\s*\((.*?)\)\s*\{',
        # const name = function(args) { ... }
        r'const\s+(\w+)\s*=\s*function\s*\((.*?)\)\s*\{',
        # const name = (args) => { ... }
        r'const\s+(\w+)\s*=\s*\((.*?)\)\s*=>\s*\{',
        # export function name(args) { ... }
        r'export\s+function\s+(\w+)\s*\((.*?)\)\s*\{',
    ]
    
    for pattern in patterns:
        for match in re.finditer(pattern, source):
            name = match.group(1)
            args = match.group(2)
            
            # Пропускаем приватные функции
            if name.startswith('_'):
                continue
            
            # Находим тело функции (упрощенный подход)
            start = match.end()
            brace_count = 1
            end = start
            
            while end < len(source) and brace_count > 0:
                if source[end] == '{':
                    brace_count += 1
                elif source[end] == '}':
                    brace_count -= 1
                end += 1
            
            body = source[match.start():end]
            signature = f"function {name}({args})"
            
            functions.append(FunctionInfo(name, signature, body, None))
    
    return functions

def generate_python_tests(function: FunctionInfo, file_path: Path) -> str:
    """Генерирует pytest тесты для Python функции"""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY не установлен в переменных окружения")
    
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = f"""Сгенерируй unit-тесты для следующей Python функции используя pytest.

Функция:
```python
{function.body}
```

{f"Docstring: {function.docstring}" if function.docstring else ""}

Требования к тестам:
1. Используй pytest framework
2. Покрой happy path (нормальные случаи использования)
3. Покрой edge cases (граничные случаи, пустые значения, None и т.д.)
4. Покрой обработку ошибок (если функция может выбрасывать исключения)
5. Используй pytest.raises для проверки исключений
6. Используй pytest.mark.parametrize для параметризованных тестов где уместно
7. Добавь docstrings к тестовым функциям
8. Имена тестов должны быть описательными (test_function_name_scenario)

Верни ТОЛЬКО код тестов без дополнительных объяснений.
Начни с необходимых импортов."""

    response = model.generate_content(prompt)
    tests = response.text.strip()
    
    # Убираем markdown блоки если есть
    if tests.startswith('```python'):
        tests = tests.split('```python', 1)[1]
        tests = tests.rsplit('```', 1)[0]
    elif tests.startswith('```'):
        tests = tests.split('```', 1)[1]
        tests = tests.rsplit('```', 1)[0]
    
    return tests.strip()

def generate_javascript_tests(function: FunctionInfo, file_path: Path) -> str:
    """Генерирует jest тесты для JavaScript функции"""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY не установлен в переменных окружения")
    
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = f"""Сгенерируй unit-тесты для следующей JavaScript функции используя Jest.

Функция:
```javascript
{function.body}
```

Требования к тестам:
1. Используй Jest framework
2. Покрой happy path (нормальные случаи использования)
3. Покрой edge cases (граничные случаи, null, undefined, пустые значения и т.д.)
4. Покрой обработку ошибок (если функция может выбрасывать исключения)
5. Используй expect().toThrow() для проверки исключений
6. Используй describe и test/it для структурирования тестов
7. Добавь комментарии к тестам
8. Имена тестов должны быть описательными

Верни ТОЛЬКО код тестов без дополнительных объяснений.
Начни с необходимых импортов."""

    response = model.generate_content(prompt)
    tests = response.text.strip()
    
    # Убираем markdown блоки если есть
    if tests.startswith('```javascript') or tests.startswith('```js'):
        tests = re.sub(r'^```(?:javascript|js)\n', '', tests)
        tests = tests.rsplit('```', 1)[0]
    elif tests.startswith('```'):
        tests = tests.split('```', 1)[1]
        tests = tests.rsplit('```', 1)[0]
    
    return tests.strip()

def validate_python_tests(test_code: str) -> bool:
    """Проверяет, что сгенерированные Python тесты синтаксически корректны"""
    try:
        ast.parse(test_code)
        return True
    except SyntaxError:
        return False

def main():
    parser = argparse.ArgumentParser(
        description='AI-powered Unit Test Generator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  %(prog)s mymodule.py                    # Генерация тестов для Python
  %(prog)s utils.js                       # Генерация тестов для JavaScript
  %(prog)s mymodule.py -o tests/          # Указать директорию для тестов
  %(prog)s mymodule.py --function add     # Генерация тестов только для функции add
  %(prog)s mymodule.py --validate         # Проверить синтаксис тестов
        """
    )
    
    parser.add_argument(
        'file',
        type=Path,
        help='Путь к файлу с кодом (Python или JavaScript)'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=Path,
        help='Директория для сохранения тестов (по умолчанию: рядом с исходным файлом)'
    )
    
    parser.add_argument(
        '--function', '-f',
        help='Генерировать тесты только для указанной функции'
    )
    
    parser.add_argument(
        '--validate', '-v',
        action='store_true',
        help='Проверить синтаксис сгенерированных тестов'
    )
    
    parser.add_argument(
        '--dry-run', '-d',
        action='store_true',
        help='Показать тесты без сохранения в файл'
    )
    
    args = parser.parse_args()
    
    # Проверяем существование файла
    if not args.file.exists():
        print(f"Ошибка: файл '{args.file}' не существует", file=sys.stderr)
        sys.exit(1)
    
    # Определяем язык по расширению
    ext = args.file.suffix.lower()
    if ext == '.py':
        language = 'python'
        test_suffix = 'test_'
        test_ext = '.py'
    elif ext in ('.js', '.mjs', '.cjs'):
        language = 'javascript'
        test_suffix = ''
        test_ext = '.test.js'
    else:
        print(f"Ошибка: неподдерживаемый тип файла '{ext}'", file=sys.stderr)
        print("Поддерживаются: .py, .js, .mjs, .cjs", file=sys.stderr)
        sys.exit(1)
    
    # Извлекаем функции
    print(f"Анализирую файл '{args.file}'...", file=sys.stderr)
    
    if language == 'python':
        functions = extract_python_functions(args.file)
    else:
        functions = extract_javascript_functions(args.file)
    
    if not functions:
        print("Не найдено функций для тестирования", file=sys.stderr)
        sys.exit(1)
    
    print(f"Найдено {len(functions)} функций", file=sys.stderr)
    
    # Фильтруем по имени функции если указано
    if args.function:
        functions = [f for f in functions if f.name == args.function]
        if not functions:
            print(f"Функция '{args.function}' не найдена", file=sys.stderr)
            sys.exit(1)
    
    # Генерируем тесты
    all_tests = []
    
    for i, func in enumerate(functions, 1):
        print(f"\n[{i}/{len(functions)}] Генерирую тесты для функции '{func.name}'...", file=sys.stderr)
        
        try:
            if language == 'python':
                tests = generate_python_tests(func, args.file)
            else:
                tests = generate_javascript_tests(func, args.file)
            
            # Валидация если требуется
            if args.validate and language == 'python':
                if validate_python_tests(tests):
                    print("  ✓ Тесты синтаксически корректны", file=sys.stderr)
                else:
                    print("  ✗ Предупреждение: тесты содержат синтаксические ошибки", file=sys.stderr)
            
            all_tests.append(f"# Tests for {func.name}\n{tests}\n")
            
        except Exception as e:
            print(f"  Ошибка: {e}", file=sys.stderr)
            continue
    
    if not all_tests:
        print("\nНе удалось сгенерировать тесты", file=sys.stderr)
        sys.exit(1)
    
    # Объединяем все тесты
    final_tests = "\n\n".join(all_tests)
    
    # Добавляем заголовок
    if language == 'python':
        header = f'"""\nUnit tests for {args.file.name}\nGenerated by AI Test Generator\n"""\n\n'
    else:
        header = f'/**\n * Unit tests for {args.file.name}\n * Generated by AI Test Generator\n */\n\n'
    
    final_tests = header + final_tests
    
    # Выводим или сохраняем
    if args.dry_run:
        print("\n" + "="*70)
        print("Сгенерированные тесты:")
        print("="*70)
        print(final_tests)
        print("="*70)
    else:
        # Определяем путь для сохранения
        if args.output:
            output_dir = args.output
            output_dir.mkdir(parents=True, exist_ok=True)
        else:
            output_dir = args.file.parent
        
        output_file = output_dir / f"{test_suffix}{args.file.stem}{test_ext}"
        
        # Сохраняем
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(final_tests)
        
        print(f"\n✓ Тесты сохранены в '{output_file}'", file=sys.stderr)
        print(f"\nДля запуска тестов:", file=sys.stderr)
        if language == 'python':
            print(f"  pytest {output_file}", file=sys.stderr)
        else:
            print(f"  npm test {output_file}", file=sys.stderr)

if __name__ == '__main__':
    main()


