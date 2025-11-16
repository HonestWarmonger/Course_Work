import streamlit as st
import time

# --- Імпорт наших шарів ---
# Ми імпортуємо класи з BLL, DAL та наші виключення
from dal.repository import FileRepository, DataAccessError
from bll.services import TestManagementService, TestingService, StatisticsService
from bll.exceptions import *

# --- 1. Налаштування та Ініціалізація (Dependency Injection) ---

# Вказуємо шляхи до наших файлів даних
TESTS_FILE = "data_tests.json"
STATS_FILE = "data_stats.json"

# @st.cache_resource - це магія Streamlit. 
# Ця команда гарантує, що наш DAL та BLL створяться ЛИШЕ ОДИН РАЗ
# і будуть "жити" протягом усього сеансу. 
# Це і є наш "Inversion of Control" на рівні PL.
@st.cache_resource
def get_services():
    """Ініціалізує та повертає всі необхідні сервіси."""
    try:
        repository = FileRepository(TESTS_FILE, STATS_FILE)
        management_service = TestManagementService(repository)
        stats_service = StatisticsService(repository)
        return management_service, stats_service, repository
    except DataAccessError as e:
        st.error(f"Критична помилка доступу до даних: {e}")
        return None, None, None

# Отримуємо наші сервіси. 
# BLL (сервіси) -> DAL (репозиторій)
management_service, stats_service, repository = get_services()

if not management_service:
    st.stop() # Зупиняємо додаток, якщо сервіси не завантажились

# --- 2. Сторінка "Керування тестами" (Адміністратор) ---
# Реалізує вимоги: 1 (Питання), 2 (Відповіді), 3.1, 3.2 (Тести), 4.1 (Пошук)

def page_admin():
    st.title("👩‍🏫 Керування тестами (Режим Адміністратора)")
    
    # 4. Контроль коректності введених даних (вимога)
    # Ми будемо використовувати st.form для цього.

    # -- Створення нового тесту (Вимога 3.1) --
    with st.expander("➕ Створити новий тест"):
        with st.form("new_test_form", clear_on_submit=True):
            new_title = st.text_input("Назва тесту")
            new_time = st.number_input("Час на питання (секунди)", min_value=10, value=60)
            
            if st.form_submit_button("Створити"):
                if new_title: # 4. Контроль коректності: перевірка, чи поле не порожнє
                    management_service.create_test(new_title, new_time)
                    management_service.save_changes() # Зберігаємо зміни
                    st.success(f"Тест '{new_title}' створено!")
                    st.rerun() # Оновлюємо сторінку, щоб побачити новий тест
                else:
                    st.warning("Назва тесту не може бути порожньою.")

    st.divider()

    # -- Редагування існуючих тестів --
    all_tests = management_service.get_all_tests()
    if not all_tests:
        st.info("Ще не створено жодного тесту. Почніть зі створення нового.")
        return

    # 4.1. Пошук тестів (у вигляді випадаючого списку)
    test_titles = [t.title for t in all_tests]
    selected_title = st.selectbox("Оберіть тест для редагування:", test_titles)
    
    selected_test = next(t for t in all_tests if t.title == selected_title)

    # -- 3.2. Зміна налаштувань тесту --
    with st.container(border=True):
        st.subheader(f"Налаштування тесту: {selected_test.title}")
        with st.form(f"edit_test_{selected_test.id}"):
            edit_title = st.text_input("Назва", value=selected_test.title)
            edit_time = st.number_input("Час на питання", min_value=10, value=selected_test.time_per_question)
            
            if st.form_submit_button("Зберегти налаштування"):
                management_service.edit_test_settings(selected_test.id, edit_title, edit_time)
                management_service.save_changes()
                st.success("Налаштування оновлено.")
                st.rerun()

    # -- 1. Керування питаннями (1.1, 1.2, 1.3, 1.4) --
    st.subheader("Питання тесту")
    for i, q in enumerate(selected_test.questions):
        with st.expander(f"Питання {i+1}: {q.text[:50]}..."):
            with st.form(f"edit_q_form_{q.id}"):
                # 1.3. Змінити питання
                new_q_text = st.text_area("Текст питання:", value=q.text)
                
                # 2. Керування відповідями (2.1, 2.2, 2.3, 2.4)
                st.write("**Відповіді:**")
                correct_answer_id = next((ans.id for ans in q.answers if ans.is_correct), None)
                
                # 2.4.1. Помітити правильну відповідь
                # Ми збираємо ID відповідей, щоб st.radio міг їх використати
                answer_options = [ans.id for ans in q.answers]
                answer_texts = [f"{ans.text} {'(✅)' if ans.is_correct else ''}" for ans in q.answers]
                
                if answer_options:
                    # 'index' - це індекс правильної відповіді у списку
                    try:
                        correct_index = answer_options.index(correct_answer_id) if correct_answer_id else 0
                    except ValueError:
                        correct_index = 0 # Якщо правильну відповідь видалили,
                                        # ставимо за замовчуванням першу

                    # Ми не можемо редагувати відповіді прямо тут, це занадто складно для інтерфейсу
                    # Ми просто показуємо їх
                    st.radio("Відповіді (оберіть правильну для редагування нижче):", 
                             answer_texts, 
                             index=correct_index, 
                             disabled=True)
                else:
                    st.info("До цього питання ще немає відповідей.")

                # 1.2. Видалити питання
                col1, col2 = st.columns(2)
                if col1.form_submit_button("Зберегти зміни питання"):
                    management_service.edit_question(selected_test.id, q.id, new_q_text)
                    management_service.save_changes()
                    st.success("Питання оновлено.")
                    st.rerun()
                
                if col2.form_submit_button("Видалити питання", type="primary"):
                    management_service.remove_question(selected_test.id, q.id)
                    management_service.save_changes()
                    st.warning("Питання видалено.")
                    st.rerun()
            
            # -- 2.1, 2.3. Додавання/Редагування відповідей --
            st.markdown("---")
            st.write("Редагувати/Додати відповіді:")
            
            # Редагування
            for ans in q.answers:
                with st.form(f"edit_ans_form_{ans.id}"):
                    cols = st.columns([0.6, 0.2, 0.2])
                    new_ans_text = cols[0].text_input("Текст", value=ans.text, label_visibility="collapsed")
                    new_is_correct = cols[1].checkbox("Правильна?", value=ans.is_correct)
                    
                    if cols[2].form_submit_button("Зберегти"):
                        management_service.edit_answer(selected_test.id, q.id, ans.id, new_ans_text, new_is_correct)
                        management_service.save_changes()
                        st.rerun()
                    if cols[2].form_submit_button("❌"): # 2.2. Видалити відповідь
                        management_service.remove_answer(selected_test.id, q.id, ans.id)
                        management_service.save_changes()
                        st.rerun()

            # 2.1. Додати нову відповідь
            with st.form(f"add_ans_form_{q.id}", clear_on_submit=True):
                cols = st.columns([0.6, 0.2, 0.2])
                add_ans_text = cols[0].text_input("Нова відповідь")
                add_is_correct = cols[1].checkbox("Правильна?")
                
                if cols[2].form_submit_button("Додати"):
                    if add_ans_text: # 4. Контроль коректності
                        management_service.add_answer(selected_test.id, q.id, add_ans_text, add_is_correct)
                        management_service.save_changes()
                        st.rerun()
                    else:
                        st.warning("Текст відповіді не може бути порожнім.")

    # 1.1. Додати питання
    with st.form(f"add_q_form_{selected_test.id}", clear_on_submit=True):
        new_q_text = st.text_input("Текст нового питання:")
        if st.form_submit_button("➕ Додати питання до тесту"):
            if new_q_text: # 4. Контроль коректності
                management_service.add_question(selected_test.id, new_q_text)
                management_service.save_changes()
                st.success("Питання додано.")
                st.rerun()
            else:
                st.warning("Текст питання не може бути порожнім.")

# --- 3. Сторінка "Проходження тесту" (Студент) ---
# Реалізує вимоги: 2.5 (Генерація), 3.3 (Підрахунок), 3.4 (Вихід)

def page_student():
    st.title("👨‍🎓 Проходження тесту (Режим Студента)")

    # st.session_state - це "пам'ять" Streamlit для одного користувача.
    # Ми зберігаємо тут сервіс тестування, щоб він "жив" між натисканнями кнопок.
    
    # Сценарій 1: Тест ще не почато
    if 'testing_session' not in st.session_state:
        st.info("Ласкаво просимо! Оберіть тест, щоб почати.")
        
        all_tests = management_service.get_all_tests()
        if not all_tests:
            st.warning("На жаль, ще немає доступних тестів.")
            return

        test_titles = [t.title for t in all_tests]
        selected_title = st.selectbox("Оберіть тест:", test_titles)
        student_name = st.text_input("Ваше ім'я (для статистики):", "Анонім")

        if st.button("Почати тестування"):
            selected_test = next(t for t in all_tests if t.title == selected_title)
            
            try:
                # 5. Обробка виняткових ситуацій (напр. тест без питань)
                testing_session = TestingService(selected_test)
                
                st.session_state['testing_session'] = testing_session
                st.session_state['student_name'] = student_name
                st.session_state['current_question'] = testing_session.get_next_question()
                st.rerun() # Перезапускаємо скрипт, щоб увійти в режим тестування

            except InvalidTestError as e:
                st.error(f"Не вдалося почати тест: {e}")
    
    # Сценарій 2: Тест триває
    else:
        # Дістаємо наш сервіс та поточне питання з "пам'яті"
        testing_session: TestingService = st.session_state['testing_session']
        q = st.session_state.get('current_question')
        
        if q:
            st.subheader(f"Тест: {testing_session.test.title}")
            st.markdown(f"**Питання:**\n> {q.text}")
            
            # 2.5. Варіанти відповідей генеруються (перемішані)
            # Ми їх отримали з BLL вже перемішаними
            
            # Використовуємо st.radio для вибору ОДНІЄЇ відповіді
            answer_texts = [ans.text for ans in q.answers]
            answer_ids = [ans.id for ans in q.answers]
            
            # Зберігаємо вибір у 'session_state', щоб він не зник
            selected_answer_text = st.radio("Оберіть відповідь:", 
                                            answer_texts, 
                                            key=f"q_radio_{q.id}",
                                            index=None) # 'None' - нічого не обрано
            
            # --- 3.4. Можливість передчасно вийти ---
            col1, col2 = st.columns(2)
            if col1.button("Наступне питання"):
                if selected_answer_text: # 4. Контроль коректності
                    # Знаходимо ID обраної відповіді
                    selected_id = answer_ids[answer_texts.index(selected_answer_text)]
                    testing_session.submit_answer(q.id, selected_id)
                    
                    # Завантажуємо наступне питання
                    st.session_state['current_question'] = testing_session.get_next_question()
                    st.rerun()
                else:
                    st.warning("Будь ласка, оберіть варіант відповіді.")

            if col2.button("Завершити тест (Вийти)", type="primary"):
                st.session_state['current_question'] = None # Сигнал, що тест завершено
                st.rerun()
        
        # Сценарій 3: Тест завершено
        else:
            st.subheader("🏁 Тест завершено!")
            
            # 3.3. Порахувати процент правильних відповідей
            results = testing_session.calculate_results()
            
            st.metric(label="Ваш результат", 
                      value=f"{results['percent']}%",
                      delta=f"{results['correct']} з {results['total']} правильних")
            
            # Зберігаємо результат у статистику
            try:
                stats_service.record_result(
                    test_id=testing_session.test.id,
                    test_title=testing_session.test.title,
                    score=results['percent'],
                    student=st.session_state['student_name']
                )
                st.success("Ваш результат збережено у статистиці.")
            except DataAccessError as e:
                st.error(f"Не вдалося зберегти результат: {e}")

            if st.button("Спробувати інший тест"):
                # Очищуємо "пам'ять"
                del st.session_state['testing_session']
                if 'current_question' in st.session_state:
                    del st.session_state['current_question']
                st.rerun()

# --- 4. Сторінка "Статистика" ---
# Реалізує вимогу: 4.2. Перегляд статистики

def page_statistics():
    st.title("📊 Загальна статистика тестів")
    
    stats = stats_service.get_test_statistics()
    
    if not stats:
        st.info("Поки що немає жодних результатів для відображення.")
        return

    # st.dataframe - це чудовий спосіб показати таблицю
    # Ми перетворюємо список dict'ів у DataFrame (це вимагає 'pandas')
    # Якщо 'pandas' не встановлено, можна просто вивести дані
    try:
        import pandas as pd
        df = pd.DataFrame(stats)
        df.rename(columns={
            'title': 'Назва тесту',
            'attempts': 'Кількість спроб',
            'average_score': 'Середній бал (%)'
        }, inplace=True)
        st.dataframe(df, use_container_width=True, hide_index=True)

    except ImportError:
        # Якщо pandas не встановлено, просто виводимо список
        st.warning("Для кращого відображення таблиці рекомендується встановити 'pandas'.")
        for item in stats:
            st.metric(label=item['title'], 
                      value=f"{item['average_score']}%", 
                      delta=f"{item['attempts']} спроб")

# --- Головний "Маршрутизатор" додатку ---

st.sidebar.title("Навігація")
# 2. Вимога: Два режими - Адмін та Студент
mode = st.sidebar.radio(
    "Оберіть ваш режим:",
    ("Проходження тесту (Студент)", "Керування тестами (Адміністратор)", "Статистика")
)

st.sidebar.info("Курсова робота з ООП. Варіант 11: Система тестування.")

if mode == "Проходження тесту (Студент)":
    page_student()
elif mode == "Керування тестами (Адміністратор)":
    page_admin()
elif mode == "Статистика":
    page_statistics()
