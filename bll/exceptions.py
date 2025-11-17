class TestLogicError(Exception):
    pass

class TestNotFoundError(TestLogicError):
    pass

class QuestionNotFoundError(TestLogicError):
    pass

class AnswerNotFoundError(TestLogicError):
    pass

class InvalidTestError(TestLogicError):
    pass

class QuestionValidationError(TestLogicError):
    pass