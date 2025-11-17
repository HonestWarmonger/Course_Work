import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st
import time

from dal.repository import FileRepository, DataAccessError
from bll.services import TestManagementService, TestingService, StatisticsService
from bll.exceptions import *

TESTS_FILE = os.path.join(PROJECT_ROOT, "data", "data_tests.json")
STATS_FILE = os.path.join(PROJECT_ROOT, "data", "data_stats.json")

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


management_service, stats_service, repository = get_services()

if not management_service:
    st.stop()

def page_admin():
    st.title("Керування тестами (Режим Адміністратора)")

    def safe_save_changes():
        try:
            management_service.save_changes()
            return True
        except QuestionValidationError as e:

            st.error(f"Помилка валідації: {e}")
            return False
    with st.expander("Створити новий тест"):
        with st.form("new_test_form", clear_on_submit=True):
            new_title = st.text_input("Назва тесту")
            new_time = st.number_input("Час на питання (секунди)", min_value=10, value=60)
            
            if st.form_submit_button("Створити"):
                if new_title:
                    management_service.create_test(new_title, new_time)
                    if safe_save_changes():
                        st.success(f"Тест '{new_title}' створено!")
                        st.rerun()
                else:
                    st.warning("Назва тесту не може бути порожньою.")

    st.divider()

    all_tests = management_service.get_all_tests()
    if not all_tests:
        st.info("Ще не створено жодного тесту. Почніть зі створення нового.")
        return

    test_titles = [t.title for t in all_tests]
    selected_title = st.selectbox("Оберіть тест для редагування:", test_titles)
    
    selected_test = next(t for t in all_tests if t.title == selected_title)

    with st.container(border=True):
        st.subheader(f"Налаштування тесту: {selected_test.title}")
        with st.form(f"edit_test_{selected_test.id}"):
            edit_title = st.text_input("Назва", value=selected_test.title)
            edit_time = st.number_input("Час на питання", min_value=10, value=selected_test.time_per_question)
            
            if st.form_submit_button("Зберегти налаштування"):
                management_service.edit_test_settings(selected_test.id, edit_title, edit_time)
                if safe_save_changes():
                    st.success("Налаштування оновлено.")
                    st.rerun()

    st.subheader("Питання тесту")
    for i, q in enumerate(selected_test.questions):
        with st.expander(f"Питання {i+1}: {q.text[:50]}..."):
            with st.form(f"edit_q_form_{q.id}"):

                new_q_text = st.text_area("Текст питання:", value=q.text)
                
                st.write("**Відповіді:**")
                correct_answer_id = next((ans.id for ans in q.answers if ans.is_correct), None)
                

                answer_options = [ans.id for ans in q.answers]
                answer_texts = [f"{ans.text} {'(✅)' if ans.is_correct else ''}" for ans in q.answers]
                
                if answer_options:

                    try:
                        correct_index = answer_options.index(correct_answer_id) if correct_answer_id else 0
                    except ValueError:
                        correct_index = 0



                    st.radio("Відповіді (оберіть правильну для редагування нижче):", 
                             answer_texts, 
                             index=correct_index, 
                             disabled=True)
                else:
                    st.info("До цього питання ще немає відповідей.")

                col1, col2 = st.columns(2)
                if col1.form_submit_button("Зберегти зміни питання"):
                    management_service.edit_question(selected_test.id, q.id, new_q_text)
                    if safe_save_changes():
                        st.success("Питання оновлено.")
                        st.rerun()
                
                if col2.form_submit_button("Видалити питання", type="primary"):
                    management_service.remove_question(selected_test.id, q.id)
                    if safe_save_changes():
                        st.warning("Питання видалено.")
                        st.rerun()
            
            st.markdown("---")
            st.write("Редагувати/Додати відповіді:")
            
            for ans in q.answers:
                with st.form(f"edit_ans_form_{ans.id}"):
                    cols = st.columns([0.6, 0.2, 0.2])
                    new_ans_text = cols[0].text_input("Текст", value=ans.text, label_visibility="collapsed")
                    new_is_correct = cols[1].checkbox("Правильна?", value=ans.is_correct)
                    
                    if cols[2].form_submit_button("Зберегти"):
                        management_service.edit_answer(selected_test.id, q.id, ans.id, new_ans_text, new_is_correct)
                        if safe_save_changes():
                            st.rerun()
                    if cols[2].form_submit_button("❌"): # 2.2. Видалити відповідь
                        management_service.remove_answer(selected_test.id, q.id, ans.id)
                        if safe_save_changes():
                            st.rerun()

            with st.form(f"add_ans_form_{q.id}", clear_on_submit=True):
                cols = st.columns([0.6, 0.2, 0.2])
                add_ans_text = cols[0].text_input("Нова відповідь")
                add_is_correct = cols[1].checkbox("Правильна?")
                
                if cols[2].form_submit_button("Додати"):
                    if add_ans_text:
                        management_service.add_answer(selected_test.id, q.id, add_ans_text, add_is_correct)
                        if safe_save_changes():
                            st.rerun()
                    else:
                        st.warning("Текст відповіді не може бути порожнім.")

    with st.form(f"add_q_form_{selected_test.id}", clear_on_submit=True):
        new_q_text = st.text_input("Текст нового питання:")
        if st.form_submit_button("➕ Додати питання до тесту"):
            if new_q_text:
                management_service.add_question(selected_test.id, new_q_text)
                if safe_save_changes():
                    st.success("Питання додано.")
                    st.rerun()
            else:
                st.warning("Текст питання не може бути порожнім.")

def page_student():
    st.title("Проходження тесту (Режим Студента)")

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
                testing_session = TestingService(selected_test)
                
                st.session_state['testing_session'] = testing_session
                st.session_state['student_name'] = student_name
                st.session_state['current_question'] = testing_session.get_next_question()
                st.rerun()

            except InvalidTestError as e:
                st.error(f"Не вдалося почати тест: {e}")
    
    else:

        testing_session: TestingService = st.session_state['testing_session']
        q = st.session_state.get('current_question')
        
        if q:
            st.subheader(f"Тест: {testing_session.test.title}")
            st.markdown(f"**Питання:**\n> {q.text}")
            
            answer_texts = [ans.text for ans in q.answers]
            answer_ids = [ans.id for ans in q.answers]
            
            selected_answer_text = st.radio("Оберіть відповідь:", 
                                            answer_texts, 
                                            key=f"q_radio_{q.id}",
                                            index=None)
            

            col1, col2 = st.columns(2)
            if col1.button("Наступне питання"):
                if selected_answer_text: 
                    selected_id = answer_ids[answer_texts.index(selected_answer_text)]
                    testing_session.submit_answer(q.id, selected_id)
                    
                    st.session_state['current_question'] = testing_session.get_next_question()
                    st.rerun()
                else:
                    st.warning("Будь ласка, оберіть варіант відповіді.")

            if col2.button("Завершити тест (Вийти)", type="primary"):
                st.session_state['current_question'] = None
                st.rerun()
        
        else:
            st.subheader("Тест завершено!")
            
            results = testing_session.calculate_results()
            
            st.metric(label="Ваш результат", 
                      value=f"{results['percent']}%",
                      delta=f"{results['correct']} з {results['total']} правильних")
            
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

                del st.session_state['testing_session']
                if 'current_question' in st.session_state:
                    del st.session_state['current_question']
                st.rerun()

def page_statistics():
    st.title("Загальна статистика тестів")
    
    stats = stats_service.get_test_statistics()
    
    if not stats:
        st.info("Поки що немає жодних результатів для відображення.")
        return

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

        st.warning("Для кращого відображення таблиці рекомендується встановити 'pandas'.")
        for item in stats:
            st.metric(label=item['title'], 
                      value=f"{item['average_score']}%", 
                      delta=f"{item['attempts']} спроб")

st.sidebar.title("Навігація")
mode = st.sidebar.radio(
    "Оберіть ваш режим:",
    ("Проходження тесту (Студент)", "Керування тестами (Адміністратор)", "Статистика")
)

st.sidebar.info("Система тестування")

if mode == "Проходження тесту (Студент)":
    page_student()
elif mode == "Керування тестами (Адміністратор)":
    page_admin()
elif mode == "Статистика":
    page_statistics()
