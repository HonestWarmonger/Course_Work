class TestLogicError(Exception):
    """Базовий клас для помилок бізнес-логіки."""
    pass

class TestNotFoundError(TestLogicError):
    """Виникає, коли тест не знайдено."""
    pass

class QuestionNotFoundError(TestLogicError):
    """Виникає, коли питання не знайдено."""
    pass

class AnswerNotFoundError(TestLogicError):
    """Виникає, коли відповідь не знайдено."""
    pass

class InvalidTestError(TestLogicError):
    """Виникає, коли тест не можна почати (напр., немає питань)."""
    pass
