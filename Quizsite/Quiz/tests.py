import json
from unittest.mock import MagicMock, patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, override_settings

from .views import (
    QUIZ_FILENAME_SESSION_KEY,
    QUIZ_SESSION_KEY,
    QUIZ_TIMER_SESSION_KEY,
    parse_hugging_face_quiz_response,
    parse_time_limit,
)


@override_settings(
    HF_API_TOKEN="test-token",
    SESSION_ENGINE="django.contrib.sessions.backends.signed_cookies",
)
class HuggingFaceQuizTests(SimpleTestCase):
    def build_mock_generated_response(self):
        return {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "title": "Тест по биологии",
                                "questions": [
                                    {
                                        "question": "Как расшифровывается ДНК?",
                                        "options": [
                                            "Дезоксирибонуклеиновая кислота",
                                            "Динамический атом азота",
                                            "Цифровой сетевой массив",
                                            "Двойная нуклеиновая кислота",
                                        ],
                                        "answer_index": 0,
                                    },
                                    {
                                        "question": "Где хранится генетический материал?",
                                        "options": ["Ядро", "Кожа", "Кость", "Волос"],
                                        "answer_index": 0,
                                    },
                                    {
                                        "question": "Какая часть клетки производит энергию?",
                                        "options": ["Митохондрия", "Хлорофилл", "Рибосома", "Мембрана"],
                                        "answer_index": 0,
                                    },
                                    {
                                        "question": "Что переносит кислород в крови?",
                                        "options": ["Гемоглобин", "Коллаген", "Инсулин", "Кератин"],
                                        "answer_index": 0,
                                    },
                                    {
                                        "question": "Что является основной единицей жизни?",
                                        "options": ["Клетка", "Атом", "Орган", "Белок"],
                                        "answer_index": 0,
                                    },
                                ],
                            }
                        )
                    }
                }
            ]
        }

    def build_legacy_generated_response(self):
        return [
            {
                "generated_text": json.dumps(
                    {
                        "title": "Тест по биологии",
                        "questions": [
                            {
                                "question": "Как расшифровывается ДНК?",
                                "options": [
                                    "Дезоксирибонуклеиновая кислота",
                                    "Динамический атом азота",
                                    "Цифровой сетевой массив",
                                    "Двойная нуклеиновая кислота",
                                ],
                                "answer_index": 0,
                            },
                            {
                                "question": "Где хранится генетический материал?",
                                "options": ["Ядро", "Кожа", "Кость", "Волос"],
                                "answer_index": 0,
                            },
                            {
                                "question": "Какая часть клетки производит энергию?",
                                "options": ["Митохондрия", "Хлорофилл", "Рибосома", "Мембрана"],
                                "answer_index": 0,
                            },
                            {
                                "question": "Что переносит кислород в крови?",
                                "options": ["Гемоглобин", "Коллаген", "Инсулин", "Кератин"],
                                "answer_index": 0,
                            },
                            {
                                "question": "Что является основной единицей жизни?",
                                "options": ["Клетка", "Атом", "Орган", "Белок"],
                                "answer_index": 0,
                            },
                        ],
                    }
                )
            }
        ]

    @patch("Quiz.views.urllib_request.urlopen")
    def test_create_test_view_redirects_to_quiz1(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(self.build_mock_generated_response()).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        uploaded_file = SimpleUploadedFile(
            "biologiya.txt",
            "ДНК хранит генетическую информацию в клетках.".encode("utf-8"),
            content_type="text/plain",
        )

        response = self.client.post(
            "/create-test/",
            {"material": uploaded_file, "timer": "45"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/Quiz1/")

        session = self.client.session
        self.assertEqual(session[QUIZ_FILENAME_SESSION_KEY], "biologiya.txt")
        self.assertEqual(session[QUIZ_TIMER_SESSION_KEY], 45)
        self.assertEqual(session[QUIZ_SESSION_KEY]["title"], "Тест по биологии")
        self.assertEqual(len(session[QUIZ_SESSION_KEY]["questions"]), 5)

    @patch("Quiz.views.urllib_request.urlopen")
    def test_quiz1_page_renders_generated_test_form(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(self.build_mock_generated_response()).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        uploaded_file = SimpleUploadedFile(
            "biologiya.txt",
            "ДНК хранит генетическую информацию в клетках.".encode("utf-8"),
            content_type="text/plain",
        )
        self.client.post("/create-test/", {"material": uploaded_file, "timer": "60"})

        response = self.client.get("/Quiz1/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Тест по биологии")
        self.assertContains(response, 'action="/submit-quiz/"')
        self.assertContains(response, "Осталось времени")
        self.assertContains(response, "Как расшифровывается ДНК?")

    @patch("Quiz.views.urllib_request.urlopen")
    def test_submit_quiz_view_shows_results(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(self.build_mock_generated_response()).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        uploaded_file = SimpleUploadedFile(
            "biologiya.txt",
            "ДНК хранит генетическую информацию в клетках.".encode("utf-8"),
            content_type="text/plain",
        )
        self.client.post("/create-test/", {"material": uploaded_file, "timer": "60"})

        response = self.client.post(
            "/submit-quiz/",
            {
                "question_0": "0",
                "question_1": "0",
                "question_2": "1",
                "question_3": "0",
                "question_4": "0",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Результат: 4 / 5")
        self.assertContains(response, "Митохондрия")

    def test_parse_hugging_face_quiz_response_rejects_invalid_payload(self):
        with self.assertRaisesMessage(RuntimeError, "Hugging Face не вернул содержимое теста."):
            parse_hugging_face_quiz_response(json.dumps({}))

    def test_parse_hugging_face_quiz_response_accepts_legacy_payload(self):
        quiz = parse_hugging_face_quiz_response(json.dumps(self.build_legacy_generated_response()))

        self.assertEqual(quiz["title"], "Тест по биологии")
        self.assertEqual(len(quiz["questions"]), 5)

    def test_parse_time_limit_clamps_values(self):
        self.assertEqual(parse_time_limit("10"), 30)
        self.assertEqual(parse_time_limit("9000"), 3600)
        self.assertEqual(parse_time_limit("bad"), 120)
