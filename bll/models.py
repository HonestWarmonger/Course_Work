import uuid
from abc import ABC

class Entity(ABC):
    def __init__(self, id: str = None):
        self.id = id or str(uuid.uuid4())

    def to_dict(self):
        return {"id": self.id}

class Answer(Entity):
    def __init__(self, text: str, is_correct: bool = False, id: str = None):
        super().__init__(id)
        self.text = text
        self.is_correct = is_correct

    def to_dict(self):
        data = super().to_dict()
        data.update({"text": self.text, "is_correct": self.is_correct})
        return data

    @classmethod
    def from_dict(cls, data):
        return cls(data['text'], data['is_correct'], data['id'])

class Question(Entity):
    def __init__(self, text: str, id: str = None):
        super().__init__(id)
        self.text = text
        self.answers: list[Answer] = []

    def add_answer(self, answer: Answer):
        self.answers.append(answer)

    def to_dict(self):
        data = super().to_dict()
        data.update({
            "text": self.text,
            "answers": [ans.to_dict() for ans in self.answers]
        })
        return data

    @classmethod
    def from_dict(cls, data):
        question = cls(data['text'], data['id'])
        question.answers = [Answer.from_dict(ans_data) for ans_data in data['answers']]
        return question

class Test(Entity):
    def __init__(self, title: str, time_per_question: int = 60, id: str = None):
        super().__init__(id)
        self.title = title
        self.time_per_question = time_per_question
        self.questions: list[Question] = []

    def add_question(self, question: Question):
        self.questions.append(question)

    def to_dict(self):
        data = super().to_dict()
        data.update({
            "title": self.title,
            "time_per_question": self.time_per_question,
            "questions": [q.to_dict() for q in self.questions]
        })
        return data

    @classmethod
    def from_dict(cls, data):
        test = cls(data['title'], data['time_per_question'], data['id'])
        test.questions = [Question.from_dict(q_data) for q_data in data['questions']]
        return test

class TestResult:

    def __init__(self, test_title: str, test_id: str, score_percent: float, student_name: str = "Анонім"):
        self.test_title = test_title
        self.test_id = test_id
        self.score_percent = score_percent
        self.student_name = student_name

    def to_dict(self):
        return {
            "test_title": self.test_title,
            "test_id": self.test_id,
            "score_percent": self.score_percent,
            "student_name": self.student_name
        }

    @classmethod
    def from_dict(cls, data):
        return cls(data['test_title'], data['test_id'], data['score_percent'], data.get('student_name', 'Анонім'))