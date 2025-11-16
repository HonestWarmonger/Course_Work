import random
from bll.models import Test, Question, Answer, TestResult
from dal.repository import FileRepository # BLL залежить від *абстракції* DAL
from bll.exceptions import * # Імпортуємо наші виключення

# --- Сервіс 1: Керування тестами (для Адміністратора) ---
# Цей клас реалізує Функціональні вимоги 1, 2, 3.1, 3.2, 4.1

class TestManagementService:
    
    def __init__(self, repository: FileRepository):
        # 7. Inversion of Control: Ми отримуємо репозиторій, а не створюємо
        self._repository = repository
        self._tests = self._repository.load_all_tests()

    def _get_test_by_id(self, test_id: str) -> Test:
        """Допоміжний приватний метод для пошуку тесту."""
        for test in self._tests:
            if test.id == test_id:
                return test
        # 5. Генерація власного виключення
        raise TestNotFoundError(f"Тест з ID {test_id} не знайдено.")

    def _get_question_by_id(self, test: Test, question_id: str) -> Question:
        for q in test.questions:
            if q.id == question_id:
                return q
        raise QuestionNotFoundError(f"Питання з ID {question_id} не знайдено.")

    def save_changes(self):
        """Зберігає всі зміни у сховищі."""
        self._repository.save_all_tests(self._tests)

    # --- 1. Керування питаннями ---
    
    def add_question(self, test_id: str, question_text: str) -> Question:
        test = self._get_test_by_id(test_id)
        new_question = Question(text=question_text)
        test.add_question(new_question)
        return new_question # Повертаємо, щоб інтерфейс знав ID

    def remove_question(self, test_id: str, question_id: str):
        test = self._get_test_by_id(test_id)
        question = self._get_question_by_id(test, question_id)
        test.questions.remove(question)

    def edit_question(self, test_id: str, question_id: str, new_text: str):
        test = self._get_test_by_id(test_id)
        question = self._get_question_by_id(test, question_id)
        question.text = new_text

    def get_all_questions(self, test_id: str) -> list[Question]:
        test = self._get_test_by_id(test_id)
        return test.questions

    # --- 2. Керування відповідями ---

    def add_answer(self, test_id: str, question_id: str, text: str, is_correct: bool) -> Answer:
        test = self._get_test_by_id(test_id)
        question = self._get_question_by_id(test, question_id)
        new_answer = Answer(text=text, is_correct=is_correct)
        question.add_answer(new_answer)
        return new_answer

    def remove_answer(self, test_id: str, question_id: str, answer_id: str):
        test = self._get_test_by_id(test_id)
        question = self._get_question_by_id(test, question_id)
        for ans in question.answers:
            if ans.id == answer_id:
                question.answers.remove(ans)
                return
        raise AnswerNotFoundError(f"Відповідь з ID {answer_id} не знайдено.")
    
    def edit_answer(self, test_id: str, q_id: str, ans_id: str, new_text: str, new_is_correct: bool):
        answer = self._get_answer_by_id(test_id, q_id, ans_id)
        answer.text = new_text
        answer.is_correct = new_is_correct

    def get_answers_for_question(self, test_id: str, question_id: str) -> list[Answer]:
        test = self._get_test_by_id(test_id)
        question = self._get_question_by_id(test, question_id)
        return question.answers
    
    def _get_answer_by_id(self, test_id: str, q_id: str, ans_id: str) -> Answer:
        question = self._get_question_by_id(self._get_test_by_id(test_id), q_id)
        for ans in question.answers:
            if ans.id == ans_id:
                return ans
        raise AnswerNotFoundError(f"Відповідь з ID {ans_id} не знайдено.")

    # --- 3. Керування тестами ---

    def create_test(self, title: str, time_per_question: int = 60) -> Test:
        new_test = Test(title=title, time_per_question=time_per_question)
        self._tests.append(new_test)
        return new_test
    
    def edit_test_settings(self, test_id: str, new_title: str, new_time: int):
        test = self._get_test_by_id(test_id)
        test.title = new_title
        test.time_per_question = new_time
    
    # --- 4. Пошук ---
    
    def get_all_tests(self) -> list[Test]:
        # 4.1. Пошук тестів (у нашому випадку - повертаємо всі)
        return self._tests

    def find_test_by_id(self, test_id: str) -> Test:
        return self._get_test_by_id(test_id)


# --- Сервіс 2: Проходження тестування (для Студента) ---
# Цей клас реалізує вимоги 2.5, 3.3, 3.4

class TestingService:
    def __init__(self, test: Test):
        if not test.questions:
            # 5. Перевірка виняткової ситуації
            raise InvalidTestError("Неможливо почати тест, у ньому немає питань.")
        
        self.test = test
        self.current_question_index = -1
        # Використовуємо словник для зберігання {question_id: selected_answer_id}
        self.user_answers: dict[str, str] = {}
        self._shuffled_questions = random.sample(self.test.questions, len(self.test.questions))

    def get_next_question(self) -> Question | None:
        """Повертає наступне питання або None, якщо тест закінчено."""
        self.current_question_index += 1
        if self.current_question_index < len(self._shuffled_questions):
            question = self._shuffled_questions[self.current_question_index]
            
            # 2.5. Варіанти відповідей генеруються автоматично (перемішуються)
            random.shuffle(question.answers)
            return question
        return None

    def submit_answer(self, question_id: str, answer_id: str):
        """Зберегти відповідь користувача."""
        self.user_answers[question_id] = answer_id

    def stop_test(self) -> dict:
        """3.4. Можливість передчасно вийти з тесту (та порахувати результат)."""
        return self.calculate_results()

    def calculate_results(self) -> dict:
        """3.3. Можливість порахувати процент правильних відповідей."""
        correct_count = 0
        total_questions = len(self._shuffled_questions)
        
        if total_questions == 0:
            return {"percent": 0, "correct": 0, "total": 0}

        for question in self._shuffled_questions:
            selected_answer_id = self.user_answers.get(question.id)
            if selected_answer_id:
                for answer in question.answers:
                    if answer.id == selected_answer_id and answer.is_correct:
                        correct_count += 1
                        break
        
        percent = (correct_count / total_questions) * 100
        return {"percent": round(percent, 2), "correct": correct_count, "total": total_questions}

# --- Сервіс 3: Статистика ---
# Цей клас реалізує вимогу 4.2

class StatisticsService:
    def __init__(self, repository: FileRepository):
        self._repository = repository

    def record_result(self, test_id: str, test_title: str, score: float, student: str):
        """Зберегти результат проходження."""
        result = TestResult(
            test_title=test_title,
            test_id=test_id,
            score_percent=score,
            student_name=student
        )
        self._repository.save_statistic(result)

    def get_test_statistics(self) -> list[dict]:
        """4.2. Перегляд статистики тестів."""
        all_results = self._repository.load_statistics()
        all_tests = self._repository.load_all_tests()
        
        stats = []
        for test in all_tests:
            results_for_test = [r for r in all_results if r.test_id == test.id]
            if not results_for_test:
                stats.append({
                    "title": test.title,
                    "attempts": 0,
                    "average_score": 0
                })
                continue
                
            attempts = len(results_for_test)
            average_score = sum(r.score_percent for r in results_for_test) / attempts
            
            stats.append({
                "title": test.title,
                "attempts": attempts,
                "average_score": round(average_score, 2)
            })
        return stats
