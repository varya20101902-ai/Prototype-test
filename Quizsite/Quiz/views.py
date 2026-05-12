import json
import os
import re
import xml.etree.ElementTree as ET
import zipfile
from urllib import error as urllib_error
from urllib import request as urllib_request

from django.conf import settings
from django.shortcuts import redirect, render
from django.urls import reverse


HF_API_URL = "https://router.huggingface.co/v1/chat/completions"
HF_DEFAULT_MODEL = "openai/gpt-oss-20b:novita"
QUIZ_SESSION_KEY = "generated_quiz"
QUIZ_FILENAME_SESSION_KEY = "generated_quiz_filename"
QUIZ_TIMER_SESSION_KEY = "generated_quiz_timer"
QUIZ_HTML_SESSION_KEY = QUIZ_SESSION_KEY
DEFAULT_TIMER_SECONDS = 120
MIN_TIMER_SECONDS = 30
MAX_TIMER_SECONDS = 3600


def home(request):
    return render(request, "Page/home.html", build_home_context(request))


def create_test_view(request):
    if request.method != "POST":
        return redirect("home")

    uploaded_file = request.FILES.get("material")
    timer_seconds = parse_time_limit(request.POST.get("timer"))

    if not uploaded_file:
        context = build_home_context(request)
        context["error_message"] = "Загрузите файл перед созданием теста."
        return render(request, "Page/home.html", context)

    try:
        source_text = extract_text_from_uploaded_file(uploaded_file)
        generated_quiz = build_quiz_with_hugging_face(uploaded_file.name, source_text)
    except (ValueError, RuntimeError, zipfile.BadZipFile, ET.ParseError) as exc:
        context = build_home_context(request)
        context["error_message"] = str(exc)
        return render(request, "Page/home.html", context)

    request.session[QUIZ_SESSION_KEY] = generated_quiz
    request.session[QUIZ_FILENAME_SESSION_KEY] = uploaded_file.name
    request.session[QUIZ_TIMER_SESSION_KEY] = timer_seconds
    request.session.modified = True

    return redirect(reverse("Quiz1"))


def Quiz1(request):
    generated_quiz = request.session.get(QUIZ_SESSION_KEY)
    if not generated_quiz:
        return render(
            request,
            "Page/Quiz1.html",
            {
                "error_message": "Сначала загрузите файл, чтобы создать тест.",
                "time_limit": DEFAULT_TIMER_SECONDS,
            },
        )

    return render(
        request,
        "Page/Quiz1.html",
        {
            "generated_quiz": generated_quiz,
            "uploaded_filename": request.session.get(QUIZ_FILENAME_SESSION_KEY),
            "time_limit": request.session.get(QUIZ_TIMER_SESSION_KEY, DEFAULT_TIMER_SECONDS),
        },
    )


def submit_quiz_view(request):
    generated_quiz = request.session.get(QUIZ_SESSION_KEY)
    if request.method != "POST" or not generated_quiz:
        return redirect("home")

    results = []
    score = 0
    questions = generated_quiz.get("questions", [])

    for index, question in enumerate(questions):
        selected_raw = request.POST.get(f"question_{index}")
        selected_index = parse_selected_index(selected_raw)
        options = question.get("options", [])
        answer_index = question.get("answer_index")
        is_correct = selected_index == answer_index

        if is_correct:
            score += 1

        results.append(
            {
                "number": index + 1,
                "question": question.get("question", ""),
                "options": options,
                "selected_index": selected_index,
                "selected_answer": get_option_text(options, selected_index),
                "correct_index": answer_index,
                "correct_answer": get_option_text(options, answer_index),
                "is_correct": is_correct,
            }
        )

    return render(
        request,
        "Page/results.html",
        {
            "generated_quiz": generated_quiz,
            "uploaded_filename": request.session.get(QUIZ_FILENAME_SESSION_KEY),
            "score": score,
            "total": len(questions),
            "results": results,
        },
    )


def build_home_context(request):
    return {
        "has_generated_quiz": bool(request.session.get(QUIZ_SESSION_KEY)),
        "uploaded_filename": request.session.get(QUIZ_FILENAME_SESSION_KEY),
        "timer": request.session.get(QUIZ_TIMER_SESSION_KEY, DEFAULT_TIMER_SECONDS),
    }


def parse_time_limit(timer_value):
    try:
        timer = int(timer_value)
    except (TypeError, ValueError):
        timer = DEFAULT_TIMER_SECONDS

    return min(max(timer, MIN_TIMER_SECONDS), MAX_TIMER_SECONDS)


def parse_selected_index(selected_raw):
    try:
        return int(selected_raw)
    except (TypeError, ValueError):
        return None


def get_option_text(options, selected_index):
    if isinstance(selected_index, int) and 0 <= selected_index < len(options):
        return options[selected_index]
    return ""


def extract_text_from_uploaded_file(uploaded_file):
    uploaded_file.seek(0)
    file_name = uploaded_file.name.lower()

    if file_name.endswith(".txt"):
        return uploaded_file.read().decode("utf-8", errors="ignore").strip()

    if file_name.endswith(".docx"):
        return extract_text_from_docx(uploaded_file)

    if file_name.endswith(".pptx"):
        return extract_text_from_pptx(uploaded_file)

    raise ValueError("Неподдерживаемый тип файла. Используйте .txt, .docx или .pptx.")


def extract_text_from_docx(uploaded_file):
    paragraphs = []
    with zipfile.ZipFile(uploaded_file) as archive:
        with archive.open("word/document.xml") as document:
            root = ET.parse(document).getroot()

    namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    for paragraph in root.findall(".//w:p", namespace):
        texts = [node.text for node in paragraph.findall(".//w:t", namespace) if node.text]
        if texts:
            paragraphs.append("".join(texts))

    return "\n".join(paragraphs).strip()


def extract_text_from_pptx(uploaded_file):
    slides_text = []
    with zipfile.ZipFile(uploaded_file) as archive:
        slide_names = sorted(
            name
            for name in archive.namelist()
            if name.startswith("ppt/slides/slide") and name.endswith(".xml")
        )
        namespace = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}

        for slide_name in slide_names:
            with archive.open(slide_name) as slide:
                root = ET.parse(slide).getroot()
            texts = [node.text for node in root.findall(".//a:t", namespace) if node.text]
            if texts:
                slides_text.append(" ".join(texts))

    return "\n".join(slides_text).strip()


def build_quiz_with_hugging_face(uploaded_filename, source_text):
    cleaned_text = normalize_source_text(source_text)
    safe_filename = os.path.basename(uploaded_filename or "uploaded_file")
    token = getattr(settings, "HF_API_TOKEN", None) or os.environ.get("HF_API_TOKEN")
    model = getattr(settings, "HF_MODEL", None) or os.environ.get("HF_MODEL") or HF_DEFAULT_MODEL

    if not token:
        raise RuntimeError("Укажите HF_API_TOKEN в .env, settings.py или переменных окружения.")

    prompt = (
        "Ты создаешь тесты с вариантами ответов по учебному материалу.\n"
        "Верни только корректный JSON строго в такой структуре:\n"
        "{"
        '"title": "string", '
        '"questions": ['
        '{"question": "string", "options": ["string", "string", "string", "string"], "answer_index": 0}'
        "]"
        "}\n"
        "Правила:\n"
        "- Напиши название, каждый вопрос и каждый вариант ответа на русском языке.\n"
        "- Если исходный материал не на русском языке, переведи содержание теста на естественный русский.\n"
        "- Создай ровно 5 вопросов.\n"
        "- В каждом вопросе должно быть ровно 4 варианта ответа.\n"
        "- answer_index должен быть целым числом от 0 до 3.\n"
        "- Каждый вопрос должен опираться на загруженный учебный материал.\n"
        "- Не используй markdown-блоки. Не добавляй объяснения.\n\n"
        f"Имя загруженного файла: {safe_filename}\n"
        f"Учебный материал:\n{cleaned_text}"
    )

    payload = json.dumps(
        {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "Ты создаешь корректные JSON-тесты по учебному материалу. Всегда пиши содержание теста на русском языке.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "max_tokens": 900,
            "temperature": 0.2,
        }
    ).encode("utf-8")

    api_request = urllib_request.Request(
        HF_API_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib_request.urlopen(api_request, timeout=60) as response:
            raw_response = response.read().decode("utf-8")
    except urllib_error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="ignore")
        hint = ""
        if exc.code == 404:
            hint = " Проверьте, что HF_MODEL доступна через Hugging Face Inference Providers."
        raise RuntimeError(f"Ошибка API Hugging Face ({exc.code}): {details or exc.reason}{hint}") from exc
    except urllib_error.URLError as exc:
        raise RuntimeError(f"Не удалось подключиться к Hugging Face: {exc.reason}") from exc

    return parse_hugging_face_quiz_response(raw_response)


def normalize_source_text(source_text):
    cleaned_text = re.sub(r"\s+", " ", source_text or "").strip()
    if not cleaned_text:
        raise ValueError("Загруженный файл не содержит читаемого текста.")

    return cleaned_text[:6000]


def parse_hugging_face_quiz_response(raw_response):
    try:
        response_data = json.loads(raw_response)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Hugging Face вернул нечитаемый ответ.") from exc

    if isinstance(response_data, dict) and response_data.get("error"):
        raise RuntimeError(f"Ошибка Hugging Face: {response_data['error']}")

    generated_text = ""
    if isinstance(response_data, dict) and response_data.get("choices"):
        choice = response_data["choices"][0]
        message = choice.get("message", {})
        generated_text = message.get("content", "") or choice.get("text", "")
    elif isinstance(response_data, list) and response_data:
        generated_text = response_data[0].get("generated_text", "")
    elif isinstance(response_data, dict):
        generated_text = response_data.get("generated_text", "")

    if not generated_text:
        raise RuntimeError("Hugging Face не вернул содержимое теста.")

    json_match = re.search(r"\{.*\}", generated_text, re.DOTALL)
    if not json_match:
        raise RuntimeError("Hugging Face вернул текст теста в неожиданном формате.")

    try:
        quiz_payload = json.loads(json_match.group(0))
    except json.JSONDecodeError as exc:
        raise RuntimeError("Не удалось разобрать JSON теста от Hugging Face.") from exc

    questions = quiz_payload.get("questions")
    if not isinstance(questions, list) or not questions:
        raise RuntimeError("Созданный тест не содержит корректных вопросов.")

    normalized_questions = []
    for item in questions:
        question_text = str(item.get("question", "")).strip()
        options = [str(option).strip() for option in item.get("options", [])]
        answer_index = item.get("answer_index")

        if not question_text or len(options) != 4:
            continue
        if not isinstance(answer_index, int) or not 0 <= answer_index < len(options):
            continue

        normalized_questions.append(
            {
                "question": question_text,
                "options": options,
                "answer_index": answer_index,
            }
        )

    if not normalized_questions:
        raise RuntimeError("Вопросы созданного теста заполнены не полностью.")

    return {
        "title": str(quiz_payload.get("title", "Сгенерированный тест")).strip() or "Сгенерированный тест",
        "questions": normalized_questions,
    }
