import streamlit as st
import pandas as pd
from datetime import datetime
import os
import subprocess

# ========== НАСТРОЙКА OLLAMA ==========
# ========== НАСТРОЙКА OLLAMA ==========
os.environ['OLLAMA_MODELS'] = 'D:\\OllamaDir'

# Пытаемся импортировать ollama с обработкой ошибок
try:
    from ollama import Client
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    st.error("Библиотека ollama не установлена. Выполните: pip install ollama")

OLLAMA_MODEL = "llama3:latest"  # <-- ИСПРАВЛЕНО! Добавлен :latest

# ========== НАСТРОЙКА СТРАНИЦЫ ==========
st.set_page_config(
    page_title="Медицинский помощник",
    page_icon="🩺",
    layout="wide"
)

# ========== ИНИЦИАЛИЗАЦИЯ ==========
if "messages" not in st.session_state:
    st.session_state.messages = []
if "health_data" not in st.session_state:
    st.session_state.health_data = []
if "reminders" not in st.session_state:
    st.session_state.reminders = []

# ========== ФУНКЦИИ ==========
def check_ollama():
    """Проверка доступности Ollama и модели"""
    if not OLLAMA_AVAILABLE:
        return False, "❌ Библиотека ollama не установлена"
    
    try:
        # Проверяем, запущен ли сервер
        client = Client(host='http://127.0.0.1:11434')
        models = client.list()
        
        # Получаем список моделей
        model_names = []
        if hasattr(models, 'models'):
            for m in models.models:
                if hasattr(m, 'model'):
                    model_names.append(m.model)
                elif hasattr(m, 'name'):
                    model_names.append(m.name)
        
        if OLLAMA_MODEL in model_names:
            return True, f"✅ Модель {OLLAMA_MODEL} готова"
        else:
            return False, f"❌ Модель {OLLAMA_MODEL} не найдена. Доступные: {model_names if model_names else 'нет'}"
            
    except Exception as e:
        error_msg = str(e)
        if "connection" in error_msg.lower() or "refused" in error_msg.lower():
            return False, "❌ Ollama не запущен. Запустите в отдельном окне: `ollama serve`"
        else:
            return False, f"❌ Ошибка: {error_msg}"

def get_medical_response(prompt, history):
    """Получение ответа от Ollama"""
    if not OLLAMA_AVAILABLE:
        return "Библиотека ollama не установлена. Выполните: pip install ollama"
    
    system_prompt = """Ты — медицинский помощник. Отвечай на вопросы о здоровье.
    Всегда добавляй: ⚠️ ВАЖНО: Это не заменяет консультацию врача.
    При серьезных симптомах рекомендую вызвать скорую.
    Отвечай на русском языке."""

    messages = [
        {"role": "system", "content": system_prompt},
        *history,
        {"role": "user", "content": prompt}
    ]

    try:
        client = Client(host='http://127.0.0.1:11434')
        response = client.chat(
            model=OLLAMA_MODEL,
            messages=messages,
            stream=False,
            options={"temperature": 0.3}
        )
        return response['message']['content']
    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg:
            return f"❌ Модель {OLLAMA_MODEL} не найдена. Скачайте: ollama pull {OLLAMA_MODEL}"
        elif "connection" in error_msg.lower():
            return "❌ Ollama не запущен. Запустите в отдельном окне: `ollama serve`\n\nЗатем нажмите F5 для обновления страницы"
        else:
            return f"❌ Ошибка: {error_msg}"

def analyze_symptoms(symptoms_text):
    """Анализ симптомов"""
    prompt = f"""Проанализируй симптомы и дай рекомендации:

Симптомы: {symptoms_text}

Ответь в формате:
1. Возможные причины:
2. Срочность: (низкая/средняя/высокая/неотложка)
3. Рекомендации:
4. К какому врачу обратиться:"""
    
    return get_medical_response(prompt, [])

# ========== БОКОВАЯ ПАНЕЛЬ ==========
with st.sidebar:
    st.title("🩺 Медицинский помощник")
    st.caption("Ваш AI ассистент здоровья")
    st.divider()
    
    # Проверка статуса с кнопкой обновления
    col1, col2 = st.columns([3, 1])
    with col1:
        ollama_ok, ollama_msg = check_ollama()
        if ollama_ok:
            st.success(ollama_msg)
        else:
            st.error(ollama_msg)
    with col2:
        if st.button("🔄", help="Обновить статус"):
            st.rerun()
    
    if not ollama_ok:
        st.info("💡 **Как запустить Ollama:**\n\n"
                "1. Откройте **новую** командную строку\n"
                "2. Выполните: `ollama serve`\n"
                "3. Оставьте окно открытым\n"
                "4. Вернитесь сюда и нажмите 🔄")
        
        if st.button("📥 Скачать модель llama3"):
            st.info("Выполните в командной строке:\n`ollama pull llama3`")
    
    st.divider()
    
    menu = st.radio(
        "📋 Разделы",
        ["💬 Чат", "🔍 Анализ симптомов", "📊 Трекер здоровья", "💊 Напоминания", "📚 Советы"]
    )

# ========== ЧАТ ==========
if menu == "💬 Чат":
    st.header("💬 Медицинская консультация")
    st.caption("Задайте вопрос о здоровье")
    
    # Отображение чата
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.chat_message("user").write(msg["content"])
        else:
            st.chat_message("assistant").write(msg["content"])
    
    # Ввод сообщения
    if prompt := st.chat_input("Опишите ваши симптомы или задайте вопрос..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)
        
        with st.spinner("🩺 Думаю..."):
            response = get_medical_response(prompt, st.session_state.messages[:-1])
            st.chat_message("assistant").write(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
    
    # Кнопка очистки
    if st.button("🗑️ Очистить чат"):
        st.session_state.messages = []
        st.rerun()

# ========== АНАЛИЗ СИМПТОМОВ ==========
elif menu == "🔍 Анализ симптомов":
    st.header("🔍 Анализ симптомов")
    
    symptoms = st.text_area(
        "📝 Опишите, что вас беспокоит:",
        placeholder="Пример: У меня болит голова уже 2 дня, температура 37.5, чувствую слабость...",
        height=150
    )
    
    if st.button("🔍 Проанализировать", type="primary"):
        if symptoms:
            with st.spinner("🩺 Анализирую симптомы..."):
                response = analyze_symptoms(symptoms)
                st.markdown("### 📊 Результат анализа")
                st.info(response)
        else:
            st.warning("Пожалуйста, опишите симптомы")
    
    st.divider()
    st.warning("🚨 **При серьезных симптомах** (боль в груди, потеря сознания, сильное кровотечение) немедленно вызывайте скорую!")

# ========== ТРЕКЕР ЗДОРОВЬЯ ==========
elif menu == "📊 Трекер здоровья":
    st.header("📊 Трекер здоровья")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        steps = st.number_input("🚶 Шаги сегодня", min_value=0, max_value=50000, value=0, step=500)
        if steps > 0:
            st.progress(min(steps / 10000, 1.0))
            st.caption(f"Цель: 10,000 шагов ({steps / 10000 * 100:.0f}%)")
    
    with col2:
        water = st.number_input("💧 Стаканы воды", min_value=0, max_value=15, value=0, step=1)
        st.caption("Рекомендация: 8 стаканов в день")
    
    with col3:
        sleep = st.number_input("😴 Часы сна", min_value=0.0, max_value=24.0, value=0.0, step=0.5)
        if sleep > 0:
            if sleep >= 7:
                st.success(f"✅ Хорошо! {sleep} ч")
            else:
                st.warning(f"⚠️ Рекомендуется 7-8 ч")
    
    if st.button("💾 Сохранить данные", type="primary"):
        if steps > 0 or water > 0 or sleep > 0:
            st.session_state.health_data.append({
                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "steps": steps,
                "water": water,
                "sleep": sleep
            })
            st.success("✅ Данные сохранены!")
            st.balloons()
        else:
            st.warning("Введите хотя бы один показатель")
    
    if st.session_state.health_data:
        st.subheader("📈 История")
        df = pd.DataFrame(st.session_state.health_data)
        st.dataframe(df, use_container_width=True)
        
        if st.button("🗑️ Очистить историю"):
            st.session_state.health_data = []
            st.rerun()

# ========== НАПОМИНАНИЯ ==========
elif menu == "💊 Напоминания":
    st.header("💊 Напоминания")
    
    col1, col2 = st.columns(2)
    
    with col1:
        with st.container(border=True):
            st.subheader("➕ Добавить")
            rem_title = st.text_input("Что нужно сделать?")
            rem_type = st.selectbox("Тип", ["Прием лекарств", "Визит к врачу", "Измерение давления", "Другое"])
            rem_time = st.time_input("Время")
            
            if st.button("🔔 Добавить напоминание", type="primary"):
                if rem_title:
                    st.session_state.reminders.append({
                        "title": rem_title,
                        "type": rem_type,
                        "time": rem_time.strftime("%H:%M"),
                        "completed": False
                    })
                    st.success("✅ Добавлено!")
                    st.rerun()
                else:
                    st.warning("Введите название")
    
    with col2:
        st.subheader("📋 Мои напоминания")
        if st.session_state.reminders:
            for i, rem in enumerate(st.session_state.reminders):
                if not rem["completed"]:
                    with st.container(border=True):
                        col_a, col_b = st.columns([3, 1])
                        with col_a:
                            st.write(f"**{rem['title']}**")
                            st.caption(f"📌 {rem['type']} | ⏰ {rem['time']}")
                        with col_b:
                            if st.button("✅ Выполнено", key=f"done_{i}"):
                                st.session_state.reminders[i]["completed"] = True
                                st.rerun()
        else:
            st.info("Нет активных напоминаний")

# ========== СОВЕТЫ ==========
elif menu == "📚 Советы":
    st.header("📚 Полезные советы по здоровью")
    
    tab1, tab2, tab3, tab4 = st.tabs(["🥗 Питание", "🧘 Ментальное здоровье", "💪 Фитнес", "😴 Сон"])
    
    with tab1:
        st.markdown("""
        ### 🥗 10 правил здорового питания
        
        1. **Завтракайте** в течение часа после пробуждения
        2. **Ешьте разноцветные овощи** каждый день
        3. **Пейте воду** до еды
        4. **Белок** в каждом приеме пищи
        5. **Ограничьте сахар** (не более 25 г в день)
        6. **Полезные жиры** - авокадо, орехи
        7. **Сложные углеводы** - крупы
        8. **Ужинайте за 3 часа до сна**
        9. **Жуйте медленно**
        10. **Планируйте питание** заранее
        """)
    
    with tab2:
        st.markdown("""
        ### 🧘 Упражнения для ментального здоровья
        
        **Ежедневная практика:**
        - **Медитация** 10 минут в день
        - **Дыхательная гимнастика** 4-7-8
        - **Дневник благодарности** (3 вещи в день)
        - **Цифровой детокс** за час до сна
        """)
    
    with tab3:
        st.markdown("""
        ### 💪 Рекомендации по фитнесу
        
        - **Кардио**: 150 минут в неделю
        - **Силовые**: 2-3 раза в неделю
        - **Растяжка**: каждый день
        - **HIIT**: 1 раз в неделю (20 минут)
        
        ⚠️ Перед началом тренировок проконсультируйтесь с врачом!
        """)
    
    with tab4:
        st.markdown("""
        ### 😴 Правила здорового сна
        
        1. **За час до сна** - без экранов
        2. **Проветрите комнату** (18-20°C)
        3. **Темнота** - плотные шторы
        4. **Тишина** - беруши или белый шум
        5. **Норма сна**: 7-9 часов
        """)

# ========== ПОДВАЛ ==========
st.divider()
st.caption("⚠️ Данный помощник не заменяет профессиональную медицинскую помощь. При серьезных симптомах обращайтесь к врачу.")