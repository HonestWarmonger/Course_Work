import json
import os
from bll.models import Test, TestResult

class FileRepository:
    def __init__(self, tests_file_path: str, stats_file_path: str):
        self.tests_file_path = tests_file_path
        self.stats_file_path = stats_file_path
        
        self._ensure_file_exists(self.tests_file_path, [])
        self._ensure_file_exists(self.stats_file_path, [])

    def _ensure_file_exists(self, file_path, default_content):
        if not os.path.exists(file_path):
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(default_content, f)
            except IOError as e:
                print(f"Помилка при створенні файлу {file_path}: {e}")
    def load_all_tests(self) -> list[Test]:
        try:
            with open(self.tests_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

                return [Test.from_dict(test_data) for test_data in data]
        except (IOError, json.JSONDecodeError, FileNotFoundError):
            return []

    def save_all_tests(self, tests: list[Test]):

        directory = os.path.dirname(self.tests_file_path)
        if not os.path.exists(directory):
            os.makedirs(directory)

        try:
            with open(self.tests_file_path, 'w', encoding='utf-8') as f:
                data_to_save = [test.to_dict() for test in tests]
                json.dump(data_to_save, f, indent=4, ensure_ascii=False)
        except IOError as e:
            print(f"Помилка збереження тестів: {e}")
            raise DataAccessError(f"Не вдалося зберегти дані у файл {self.tests_file_path}")

    def load_statistics(self) -> list[TestResult]:
        try:
            with open(self.stats_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [TestResult.from_dict(stat_data) for stat_data in data]
        except (IOError, json.JSONDecodeError, FileNotFoundError):
            return []

    def save_statistic(self, result: TestResult):
        stats = self.load_statistics()
        stats.append(result)


        directory = os.path.dirname(self.stats_file_path)
        if not os.path.exists(directory):
            os.makedirs(directory)

        try:
            with open(self.stats_file_path, 'w', encoding='utf-8') as f:
                data_to_save = [stat.to_dict() for stat in stats]
                json.dump(data_to_save, f, indent=4, ensure_ascii=False)
        except IOError as e:
            print(f"Помилка збереження статистики: {e}")
            raise DataAccessError(f"Не вдалося зберегти дані у файл {self.stats_file_path}")

class DataAccessError(Exception):
    pass
