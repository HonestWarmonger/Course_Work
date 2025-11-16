import unittest
from unittest.mock import Mock, patch
import sys
import os

# --- Налаштування шляху для імпортів ---
# Це потрібно, щоб Python міг знайти папки 'bll' та 'dal' з тесту
# (Можливо, доведеться трішки змінити, залежно від вашої IDE)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)
# --- Кінець налаштування шляху ---

from bll.services import TestManagementService, StatisticsService, TestingService
from bll.exceptions import TestNotFoundError, InvalidTestError
from bll.models import Test, Question, Answer
from dal.repository import FileRepository

class TestTestManagementService(unittest.TestCase):

    def setUp(self):
        """Цей метод викликається перед кожним тестом."""
        
        # Arrange (Загальна підготовка)
        # 1. Створюємо Mock для FileRepository
        self.mock_repo = Mock(spec=FileRepository)
        
        # 2. Налаштовуємо Mock: коли BLL попросить 'load_all_tests', 
        #    mock поверне порожній список.
        self.mock_repo.load_all_tests.return_value = []
        
        # 3. Створюємо сервіс (BLL) з mock-репозиторієм (Inversion of Control)
        self.service = TestManagementService(self.mock_repo)

    def test_create_test_success(self):
        # --- Arrange (Підготовка) ---
        title = "Новий Тест"
        time = 30

        # --- Act (Дія) ---
        new_test = self.service.create_test(title, time)

        # --- Assert (Перевірка) ---
        self.assertIsNotNone(new_test)
        self.assertEqual(new_test.title, title)
        self.assertEqual(new_test.time_per_question, time)
        # Переконуємося, що тест додано до внутрішнього списку сервісу
        self.assertIn(new_test, self.service.get_all_tests())

    def test_save_changes_calls_repository_save(self):
        # --- Arrange (Підготовка) ---
        # Створимо тест, щоб було що зберігати
        test = self.service.create_test("Тест для збереження", 60)
        
        # --- Act (Дія) ---
        self.service.save_changes()

        # --- Assert (Перевірка) ---
        # Ми перевіряємо, що BLL викликав метод 'save_all_tests' 
        # нашого mock-репозиторію РІВНО ОДИН РАЗ.
        self.mock_repo.save_all_tests.assert_called_once()
        
        # ...і що він передав туди список, який містить наш тест
        saved_list = self.mock_repo.save_all_tests.call_args[0][0]
        self.assertIn(test, saved_list)

    def test_get_test_by_id_raises_not_found_error(self):
        # --- Arrange (Підготовка) ---
        invalid_id = "non_existing_id"

        # --- Act & Assert (Дія та Перевірка) ---
        # Ми очікуємо, що BLL згенерує наше власне виключення
        with self.assertRaises(TestNotFoundError):
            self.service.find_test_by_id(invalid_id)

    def test_add_question_to_test(self):
        # --- Arrange (Підготовка) ---
        test = self.service.create_test("Тест з питаннями", 60)
        question_text = "Скільки буде 2+2?"

        # --- Act (Дія) ---
        new_question = self.service.add_question(test.id, question_text)

        # --- Assert (Перевірка) ---
        self.assertEqual(new_question.text, question_text)
        self.assertIn(new_question, test.questions)
        self.assertEqual(len(test.questions), 1)

    def test_add_answer_to_question(self):
        # --- Arrange (Підготовка) ---
        test = self.service.create_test("Тест з відповідями", 60)
        q = self.service.add_question(test.id, "Яка мова програмування?")
        
        answer_text = "Python"
        is_correct = True

        # --- Act (Дія) ---
        new_answer = self.service.add_answer(test.id, q.id, answer_text, is_correct)

        # --- Assert (Перевірка) ---
        self.assertEqual(new_answer.text, answer_text)
        self.assertEqual(new_answer.is_correct, is_correct)
        self.assertIn(new_answer, q.answers)

    # Тут можна додати тести для remove_question, edit_question,
    # remove_answer, edit_answer...

# --- Тести для TestingService (друга сутність) ---
# Завдання вимагає 50% покриття для інших, тому додамо кілька тестів

class TestTestingService(unittest.TestCase):

    def setUp(self):
        # Створимо "живі" об'єкти для тестування логіки
        self.test = Test("Повноцінний тест", 60)
        q1 = Question("Питання 1")
        q1.add_answer(Answer("Правильна 1", is_correct=True))
        q1.add_answer(Answer("Неправильна 1", is_correct=False))
        
        q2 = Question("Питання 2")
        q2.add_answer(Answer("Правильна 2", is_correct=True))
        q2.add_answer(Answer("Неправильна 2", is_correct=False))
        
        self.test.add_question(q1)
        self.test.add_question(q2)

    def test_start_test_with_no_questions_raises_error(self):
        # --- Arrange (Підготовка) ---
        empty_test = Test("Порожній тест", 60)

        # --- Act & Assert (Дія та Перевірка) ---
        with self.assertRaises(InvalidTestError):
            TestingService(empty_test)
            
    def test_calculate_results_100_percent(self):
        # --- Arrange (Підготовка) ---
        service = TestingService(self.test)
        
        # Імітуємо проходження тесту
        q1 = self.test.questions[0]
        q2 = self.test.questions[1]
        
        # Знаходимо правильні відповіді
        correct_ans1_id = [a.id for a in q1.answers if a.is_correct][0]
        correct_ans2_id = [a.id for a in q2.answers if a.is_correct][0]

        service.user_answers = {
            q1.id: correct_ans1_id,
            q2.id: correct_ans2_id
        }

        # --- Act (Дія) ---
        results = service.calculate_results()

        # --- Assert (Перевірка) ---
        self.assertEqual(results["percent"], 100.0)
        self.assertEqual(results["correct"], 2)
        self.assertEqual(results["total"], 2)

    def test_calculate_results_50_percent(self):
        # --- Arrange (Підготовка) ---
        service = TestingService(self.test)
        
        q1 = self.test.questions[0]
        q2 = self.test.questions[1]
        
        correct_ans1_id = [a.id for a in q1.answers if a.is_correct][0]
        incorrect_ans2_id = [a.id for a in q2.answers if not a.is_correct][0]

        service.user_answers = {
            q1.id: correct_ans1_id,
            q2.id: incorrect_ans2_id
        }

        # --- Act (Дія) ---
        results = service.calculate_results()

        # --- Assert (Перевірка) ---
        self.assertEqual(results["percent"], 50.0)
        self.assertEqual(results["correct"], 1)
        self.assertEqual(results["total"], 2)

if __name__ == '__main__':
    unittest.main()
