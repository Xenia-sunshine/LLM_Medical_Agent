# test_ollama_connection.py
import ollama
import os

# Указываем путь
os.environ['OLLAMA_MODELS'] = 'D:\\OllamaDir'

print("=== Диагностика Ollama ===\n")

# 1. Проверяем переменные окружения
print(f"1. OLLAMA_MODELS = {os.environ.get('OLLAMA_MODELS', 'не задан')}")

# 2. Проверяем подключение
print("\n2. Проверка подключения к Ollama серверу...")
try:
    # Пробуем получить список моделей
    models = ollama.list()
    print("   ✅ Сервер отвечает")
    print(f"   📋 Тип ответа: {type(models)}")
    print(f"   📋 Содержимое: {models}")
except Exception as e:
    print(f"   ❌ Ошибка: {e}")
    print("   Запустите сервер: ollama serve")
    exit()

# 3. Список моделей (исправленная версия)
print("\n3. Доступные модели:")
model_names = []

# Проверяем разные варианты структуры ответа
if hasattr(models, 'get') and models.get('models'):
    # Вариант 1: словарь с ключом 'models'
    for m in models['models']:
        if isinstance(m, dict):
            name = m.get('model', m.get('name', 'unknown'))
            model_names.append(name)
            print(f"   - {name}")
elif isinstance(models, dict):
    # Вариант 2: прямой словарь
    for key in models.keys():
        model_names.append(key)
        print(f"   - {key}")
elif isinstance(models, list):
    # Вариант 3: список моделей
    for m in models:
        if isinstance(m, dict):
            name = m.get('model', m.get('name', str(m)))
            model_names.append(name)
            print(f"   - {name}")
        else:
            model_names.append(str(m))
            print(f"   - {m}")
else:
    print(f"   ❌ Неизвестный формат ответа: {models}")

if not model_names:
    print("   ❌ Нет доступных моделей")
    print("   Скачайте модель: ollama pull llama3")
    exit()

# 4. Проверка llama3
print("\n4. Проверка модели llama3:")
found = False
for name in model_names:
    if 'llama3' in name.lower():
        found = True
        break

if found:
    print("   ✅ Модель найдена!")
    try:
        # Пробуем разные способы вызова
        print("   🔄 Пробуем generate...")
        response = ollama.generate(model='llama3', prompt='Скажи "привет"')
        if isinstance(response, dict):
            result = response.get('response', response)
            print(f"   ✅ Модель отвечает: {str(result)[:100]}...")
        else:
            print(f"   ✅ Модель отвечает: {str(response)[:100]}...")
    except Exception as e:
        print(f"   ❌ Ошибка при generate: {e}")
        try:
            print("   🔄 Пробуем chat...")
            response = ollama.chat(model='llama3', messages=[{'role': 'user', 'content': 'Скажи "привет"'}])
            result = response.get('message', {}).get('content', response)
            print(f"   ✅ Модель отвечает через chat: {str(result)[:100]}...")
        except Exception as e2:
            print(f"   ❌ Ошибка при chat: {e2}")
else:
    print("   ❌ Модель 'llama3' не найдена")
    print(f"   Найденные модели: {model_names}")
    print("   Скачайте: ollama pull llama3")

print("\n=== Диагностика завершена ===")