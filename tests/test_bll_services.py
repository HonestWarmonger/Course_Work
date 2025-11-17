import unittest
from unittest.mock import Mock, patch
import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from bll.services import TestManagementService, StatisticsService, TestingService
from bll.exceptions import TestNotFoundError, InvalidTestError
from bll.models import Test, Question, Answer
from dal.repository import FileRepository

class TestTestManagementService(unittest.TestCase):

    def setUp(self):
        """Цей метод викликається перед кожним тестом."""
        
        self.mock_repo = Mock(spec=FileRepository)

        self.mock_repo.load_all_tests.return_value = []
        
        self.service = TestManagementService(self.mock_repo)

    def test_create_test_success(self):
        title = "Новий Тест"
        time = 30

        new_test = self.service.create_test(title, time)

        self.assertIsNotNone(new_test)
        self.assertEqual(new_test.title, title)
        self.assertEqual(new_test.time_per_question, time)
        self.assertIn(new_test, self.service.get_all_tests())

    def test_save_changes_calls_repository_save(self):
        test = self.service.create_test("Тест для збереження", 60)

        self.service.save_changes()

        self.mock_repo.save_all_tests.assert_called_once()

        saved_list = self.mock_repo.save_all_tests.call_args[0][0]
        self.assertIn(test, saved_list)

    def test_get_test_by_id_raises_not_found_error(self):
        invalid_id = "non_existing_id"

        with self.assertRaises(TestNotFoundError):
            self.service.find_test_by_id(invalid_id)

    def test_add_question_to_test(self):
        test = self.service.create_test("Тест з питаннями", 60)
        question_text = "Скільки буде 2+2?"

        new_question = self.service.add_question(test.id, question_text)

        self.assertEqual(new_question.text, question_text)
        self.assertIn(new_question, test.questions)
        self.assertEqual(len(test.questions), 1)

    def test_add_answer_to_question(self):
        test = self.service.create_test("Тест з відповідями", 60)
        q = self.service.add_question(test.id, "Яка мова програмування?")
        
        answer_text = "Python"
        is_correct = True

        new_answer = self.service.add_answer(test.id, q.id, answer_text, is_correct)

        self.assertEqual(new_answer.text, answer_text)
        self.assertEqual(new_answer.is_correct, is_correct)
        self.assertIn(new_answer, q.answers)


class TestTestingService(unittest.TestCase):

    def setUp(self):
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
        empty_test = Test("Порожній тест", 60)

        with self.assertRaises(InvalidTestError):
            TestingService(empty_test)
            
    def test_calculate_results_100_percent(self):
        service = TestingService(self.test)

        q1 = self.test.questions[0]
        q2 = self.test.questions[1]

        correct_ans1_id = [a.id for a in q1.answers if a.is_correct][0]
        correct_ans2_id = [a.id for a in q2.answers if a.is_correct][0]

        service.user_answers = {
            q1.id: correct_ans1_id,
            q2.id: correct_ans2_id
        }

        results = service.calculate_results()

        self.assertEqual(results["percent"], 100.0)
        self.assertEqual(results["correct"], 2)
        self.assertEqual(results["total"], 2)

    def test_calculate_results_50_percent(self):
        service = TestingService(self.test)
        
        q1 = self.test.questions[0]
        q2 = self.test.questions[1]
        
        correct_ans1_id = [a.id for a in q1.answers if a.is_correct][0]
        incorrect_ans2_id = [a.id for a in q2.answers if not a.is_correct][0]

        service.user_answers = {
            q1.id: correct_ans1_id,
            q2.id: incorrect_ans2_id
        }

        results = service.calculate_results()

        self.assertEqual(results["percent"], 50.0)
        self.assertEqual(results["correct"], 1)
        self.assertEqual(results["total"], 2)

if __name__ == '__main__':
    unittest.main()
