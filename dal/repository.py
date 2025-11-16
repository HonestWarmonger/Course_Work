import json
import os
from bll.models import Test, TestResult  # Імпортуємо наші моделі

class FileRepository:
    def __init__(self, tests_file_path: str, stats_file_path: str):
        self.tests_file_path = tests_file_path
        self.stats_file_path = stats_file_path
        
        # Переконуємося, що файли існують (можна створити порожні, якщо їх немає)
        self._ensure_file_exists(self.tests_file_path, [])
        self._ensure_file_exists(self.stats_file_path, [])

    def _ensure_file_exists(self, file_path, default_content):
        # Допоміжна функція, щоб створити файл, якщо його немає
        if not os.path.exists(file_path):
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(default_content, f)
            except IOError as e:
                print(f"Помилка при створенні файлу {file_path}: {e}")

    # --- Робота з Тестами ---

    def load_all_tests(self) -> list[Test]:
        try:
            with open(self.tests_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Використовуємо .from_dict() для "оживлення" об'єктів
                return [Test.from_dict(test_data) for test_data in data]
        except (IOError, json.JSONDecodeError, FileNotFoundError):
            # Якщо файл пошкоджений або порожній, повертаємо порожній список
            # Це відповідає вимозі про обробку виняткових ситуацій
            return []

    def save_all_tests(self, tests: list[Test]):
        try:
            with open(self.tests_file_path, 'w', encoding='utf-8') as f:
                # Використовуємо .to_dict() для серіалізації
                data_to_save = [test.to_dict() for test in tests]
                json.dump(data_to_save, f, indent=4, ensure_ascii=False)
        except IOError as e:
            # Обробка виняткової ситуації (наприклад, немає прав на запис)
            print(f"Помилка збереження тестів: {e}")
            # Тут можна підняти власний клас виключення, як вимагалось
            raise DataAccessError(f"Не вдалося зберегти дані у файл {self.tests_file_path}")

    # --- Робота зі Статистикою ---

    def load_statistics(self) -> list[TestResult]:
        try:
            with open(self.stats_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [TestResult.from_dict(stat_data) for stat_data in data]
        except (IOError, json.JSONDecodeError, FileNotFoundError):
            return []

    def save_statistic(self, result: TestResult):
        # Ми не перезаписуємо всю статистику, а додаємо новий результат
        stats = self.load_statistics()
        stats.append(result)
        try:
            with open(self.stats_file_path, 'w', encoding='utf-8') as f:
                data_to_save = [stat.to_dict() for stat in stats]
                json.dump(data_to_save, f, indent=4, ensure_ascii=False)
        except IOError as e:
            print(f"Помилка збереження статистики: {e}")
            raise DataAccessError(f"Не вдалося зберегти дані у файл {self.stats_file_path}")

# Створимо власний клас виключення, як вимагає завдання (п.5)
class DataAccessError(Exception):
    pass
