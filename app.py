import streamlit as st
import ollama
import pandas as pd
from datetime import datetime

# ==================== НАСТРОЙКА СТРАНИЦЫ ====================
st.set_page_config(
    page_title="Медицинский помощник",
    page_icon="🩺",
    layout="wide"
)

# ==================== ПЕРЕМЕННЫЕ ====================
OLLAMA_MODEL = "llama3"

# Инициализация состояния сессии
if "messages" not in st.session_state:
    st.session_state.messages = []
if "health_data" not in st.session_state:
    st.session_state.health_data = []
if "reminders" not in st.session_state:
    st.session_state.reminders = []


# ==================== ФУНКЦИИ ====================
def check_ollama():
    """Проверка доступности Ollama и модели"""
    try:
        # Проверяем список моделей
        models = ollama.list()
        model_names = [m['name'] for m in models.get('models', [])]

        # Проверяем, есть ли наша модель
        model_available = any(OLLAMA_MODEL in name for name in model_names)

        if model_available:
            return True, f"✅ Модель {OLLAMA_MODEL} готова"
        else:
            return False, f"❌ Модель {OLLAMA_MODEL} не найдена. Скачайте командой: ollama pull {OLLAMA_MODEL}"
    except Exception as e:
        return False, f"❌ Ollama не запущен. Запустите командой: ollama serve\nОшибка: {str(e)}"


def get_medical_response(prompt, history):
    """Получение ответа от Ollama"""
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
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=messages,
            stream=False,
            options={"temperature": 0.3}
        )
        return response['message']['content']
    except Exception as e:
        return f"❌ Ошибка: {str(e)}\n\nПроверьте: запущен ли Ollama и скачана ли модель"


# ==================== БОКОВАЯ ПАНЕЛЬ ====================
with st.sidebar:
    st.title("🩺 Медицинский помощник")
    st.caption("Ваш AI ассистент здоровья")

    st.divider()

    # Проверка статуса
    ollama_ok, ollama_msg = check_ollama()
    if ollama_ok:
        st.success(ollama_msg)
    else:
        st.error(ollama_msg)
        st.info(
            "💡 **Как исправить:**\n1. Установите Ollama с ollama.com\n2. Запустите: `ollama serve`\n3. Скачайте модель: `ollama pull llama3`")

    st.divider()

    # Меню
    menu = st.radio(
        "📋 Разделы",
        ["💬 Чат", "🔍 Анализ симптомов", "📊 Трекер здоровья", "💊 Напоминания", "📚 Советы"]
    )

# ==================== ОСНОВНОЙ КОНТЕНТ ====================
if menu == "💬 Чат":
    st.header("💬 Медицинская консультация")
    st.caption("Задайте любой вопрос о вашем здоровье")

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

elif menu == "🔍 Анализ симптомов":
    st.header("🔍 Анализ симптомов")
    st.caption("Опишите ваши симптомы для предварительного анализа")

    symptoms = st.text_area(
        "📝 Опишите, что вас беспокоит:",
        placeholder="Пример: У меня болит голова уже 2 дня, температура 37.5, чувствую слабость...",
        height=150
    )

    if st.button("🔍 Проанализировать", type="primary"):
        if symptoms:
            with st.spinner("Анализирую симптомы..."):
                prompt = f"""Проанализируй симптомы и дай рекомендации:

Симптомы: {symptoms}

Ответь в формате:
1. Возможные причины:
2. Срочность: (низкая/средняя/высокая/неотложка)
3. Рекомендации:
4. К какому врачу обратиться:

⚠️ Добавь дисклеймер о необходимости консультации врача."""

                response = get_medical_response(prompt, [])
                st.markdown("### 📊 Результат анализа")
                st.info(response)
        else:
            st.warning("Пожалуйста, опишите симптомы")

    st.divider()
    st.warning(
        "🚨 **При серьезных симптомах** (боль в груди, потеря сознания, сильное кровотечение) немедленно вызывайте скорую!")

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

    # Показываем историю
    if st.session_state.health_data:
        st.subheader("📈 История")
        df = pd.DataFrame(st.session_state.health_data)
        st.dataframe(df, use_container_width=True)

        if st.button("🗑️ Очистить историю"):
            st.session_state.health_data = []
            st.rerun()

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

elif menu == "📚 Советы":
    st.header("📚 Полезные советы по здоровью")

    tab1, tab2, tab3, tab4 = st.tabs(["🥗 Питание", "🧘 Ментальное здоровье", "💪 Фитнес", "😴 Сон"])

    with tab1:
        st.markdown("""
        ### 🥗 10 правил здорового питания

        1. **Завтракайте** в течение часа после пробуждения
        2. **Ешьте разноцветные овощи** каждый день
        3. **Пейте воду** до еды, а не во время
        4. **Белок** должен быть в каждом приеме пищи
        5. **Ограничьте сахар** (не более 25 г в день)
        6. **Полезные жиры** - авокадо, орехи, оливковое масло
        7. **Сложные углеводы** - крупы, цельнозерновой хлеб
        8. **Ужинайте за 3 часа до сна**
        9. **Жуйте медленно** - не менее 20 минут на прием пищи
        10. **Планируйте питание** заранее

        🍎 **Пример здорового дня:**
        - Завтрак: Овсянка с ягодами
        - Обед: Курица с гречкой и салатом
        - Ужин: Рыба с овощами
        - Перекусы: Яблоко, йогурт
        """)

    with tab2:
        st.markdown("""
        ### 🧘 Упражнения для ментального здоровья

        **Ежедневная практика:**

        **1. Медитация (10 минут)**
        - Сядьте удобно, закройте глаза
        - Сосредоточьтесь на дыхании
        - Используйте приложения: Calm, Headspace

        **2. Дыхательная гимнастика "4-7-8"**
        - Вдох на 4 счета
        - Задержка на 7 счетов
        - Выдох на 8 счетов
        - Повторить 5 раз

        **3. Ведение дневника благодарности**
        - Записывайте 3 вещи, за которые вы благодарны

        **4. Цифровой детокс**
        - 1 час без телефона перед сном

        **Когда нужен психолог:**
        - Тревога более 2 недель
        - Потеря интереса к жизни
        - Проблемы со сном
        """)

    with tab3:
        st.markdown("""
        ### 💪 Рекомендации по фитнесу

        **Для начинающих:**

        | День | Активность | Время |
        |------|------------|-------|
        | ПН | Ходьба | 30 мин |
        | ВТ | Растяжка | 15 мин |
        | СР | Ходьба быстрым шагом | 40 мин |
        | ЧТ | Отдых | - |
        | ПТ | Легкая зарядка | 20 мин |
        | СБ | Ходьба | 60 мин |
        | ВС | Отдых | - |

        **Для продвинутых:**
        - **Кардио**: 150 мин в неделю
        - **Силовые**: 2-3 раза в неделю
        - **Растяжка**: каждый день
        - **HIIT**: 1 раз в неделю

        ⚠️ Перед началом тренировок проконсультируйтесь с врачом!
        """)

    with tab4:
        st.markdown("""
        ### 😴 Правила здорового сна

        **Создайте ритуал:**

        1. **За час до сна** - без экранов
        2. **Проветрите комнату** (18-20°C)
        3. **Темнота** - плотные шторы
        4. **Тишина** - беруши или белый шум
        5. **Расслабление** - теплая ванна, чтение

        **Что помогает заснуть:**
        - 🍵 Ромашковый чай
        - 📖 Чтение книги
        - 🎵 Спокойная музыка
        - 🧘 Медитация

        **Чего избегать:**
        - ❌ Кофеин после 15:00
        - ❌ Алкоголь перед сном
        - ❌ Тяжелая еда за 3 часа до сна
        - ❌ Яркий свет

        **Норма сна:**
        - 18-64 года: 7-9 часов
        - 65+ лет: 7-8 часов
        """)

# ==================== FOOTER ====================
st.divider()
st.caption(
    "⚠️ Данный помощник не заменяет профессиональную медицинскую помощь. При серьезных симптомах обращайтесь к врачу.")