from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import (
    TimeoutException,
    InvalidSessionIdException,
    WebDriverException,
    StaleElementReferenceException,
)
from difflib import SequenceMatcher
import re
import time
import unicodedata

import config

# Map visually similar / semantically equivalent Unicode chars to ASCII
_UNICODE_REPLACEMENTS = str.maketrans({
    '\u2018': "'",  # left single quotation mark
    '\u2019': "'",  # right single quotation mark
    '\u201c': '"',  # left double quotation mark
    '\u201d': '"',  # right double quotation mark
    '\u2013': '-',  # en dash
    '\u2014': '-',  # em dash
    '\u2026': '...',# ellipsis
    '\u00a0': ' ',  # non-breaking space
    '\u200b': '',   # zero-width space
    '\u200c': '',   # zero-width non-joiner
    '\u200d': '',   # zero-width joiner
    '\ufeff': '',   # BOM
})


def _normalize(text):
    """Lowercase, collapse whitespace, strip non-alphanumeric (keep spaces).

    Also applies Unicode normalization (NFKC) and replaces look-alike
    characters so that CSV entries and scraped text compare equal even
    when the source encoding differs.
    """
    # 1) Replace known look-alike characters before decomposition
    text = text.translate(_UNICODE_REPLACEMENTS)
    # 2) NFKC: decompose then re-compose in canonical form (handles accented
    #    chars, ligatures, fullwidth digits, etc.)
    text = unicodedata.normalize('NFKC', text)
    text = text.lower().strip()
    text = re.sub(r'[^\w\s]', '', text)   # remove punctuation
    text = re.sub(r'\s+', ' ', text)       # collapse whitespace
    return text


def _similarity(a, b):
    """Return 0.0–1.0 similarity ratio between two strings."""
    return SequenceMatcher(None, a, b).ratio()


def _find_answer(question_text, qa_database):
    """Look up a question in the database with fuzzy matching."""
    if not qa_database:
        return None

    # 1) Exact match
    if question_text in qa_database:
        return qa_database[question_text]

    norm_q = _normalize(question_text)

    # 2) Normalized exact match
    for csv_question, csv_answer in qa_database.items():
        if _normalize(csv_question) == norm_q:
            return csv_answer

    # 3) Substring: CSV question inside website text or vice-versa
    for csv_question, csv_answer in qa_database.items():
        norm_csv = _normalize(csv_question)
        if norm_csv in norm_q or norm_q in norm_csv:
            return csv_answer

    # 4) Fuzzy: pick the best match above 85% similarity
    best_answer = None
    best_score = 0.0
    for csv_question, csv_answer in qa_database.items():
        score = _similarity(norm_q, _normalize(csv_question))
        if score > best_score:
            best_score = score
            best_answer = csv_answer

    if best_score >= 0.75:
        print(f"  (fuzzy match {best_score:.0%})")
        return best_answer

    return None


def _extract_question(raw_text):
    """Pull the actual question (line ending with '?') from the element's full text.

    The question element often contains extra text like '1/10', option labels, etc.
    We look for the first line ending with '?' which is the real question.
    """
    for line in raw_text.splitlines():
        line = line.strip()
        if line.endswith("?"):
            return line
    return raw_text.strip()


def _is_result_screen(raw_text):
    """Detect the result/score screen that appears after answering.

    It shows text like '+600', '+300', 'Correct', 'Incorrect', etc.
    """
    return bool(re.search(r'^\+\d+', raw_text.strip(), re.MULTILINE))


def _visible_text(el):
    try:
        if not el.is_displayed():
            return ""
    except Exception:
        return ""
    return (el.text or "").strip()


def _first_line(text):
    """Return only the first line of a multi-line button text."""
    return text.split('\n')[0].strip()


def _is_answer_option(text):
    """Filter out buttons that are clearly not answer choices."""
    first = _first_line(text)
    # Skip game-code-like strings: digits with spaces (e.g. "762 012")
    if re.match(r'^\d+\s+\d+', first):
        return False
    # Skip leaderboard positions like "17th", "8th"
    if re.match(r'^\d+(st|nd|rd|th)$', first, re.IGNORECASE):
        return False
    # Skip score text like "+600"
    if re.match(r'^\+\d+', first):
        return False
    return True


def _wait_for_new_question(driver, last_raw=None, timeout_s=60):
    """Wait for a genuine new question screen (not a result screen)."""
    wait = WebDriverWait(driver, timeout_s)

    def _has_new_question(d):
        try:
            el = d.find_element(By.CSS_SELECTOR, config.QUESTION_SELECTOR)
        except Exception:
            return False

        raw = (el.text or "").strip()
        if not raw:
            return False

        # Skip result/score screens
        if _is_result_screen(raw):
            return False

        # Must look different from last time
        if last_raw and raw == last_raw:
            return False

        return el

    return wait.until(_has_new_question)


def play_quiz(driver, qa_database=None, read_only=False):

    answered = 0
    last_raw = None

    if read_only:
        print("\n[READ-ONLY MODE] Showing questions only — no auto-clicking.")

    while True:

        try:
            question_el = _wait_for_new_question(driver, last_raw)
        except TimeoutException:
            print("No new question detected.")
            break
        except (InvalidSessionIdException, WebDriverException):
            print("Browser closed.")
            break

        raw_text = (question_el.text or "").strip()
        last_raw = raw_text

        question_text = _extract_question(raw_text)

        print(f"\n=== QUESTION ({answered + 1}) ===")
        print(question_text)

        raw_options = driver.find_elements(
            By.CSS_SELECTOR,
            config.OPTION_SELECTOR
        )

        options = [
            o for o in raw_options
            if _visible_text(o) and _is_answer_option(_visible_text(o))
        ]

        print("\n=== CHOICES ===")

        for idx, opt in enumerate(options):
            print(f"[{idx}] {_first_line(_visible_text(opt))}")

        if not options:
            print("No options detected")
            continue

        if read_only:
            answered += 1
            time.sleep(1)
            continue

        correct_answer = _find_answer(question_text, qa_database)

        if not correct_answer:
            print("Answer not found in CSV")
            continue

        print("Correct answer:", correct_answer)
        print(">> 0.5s pause — click the bonus multiplier (x2/x3) now!")
        time.sleep(0.5)

        # Auto click
        clicked = False

        for opt in options:
            try:
                text = _visible_text(opt)
            except StaleElementReferenceException:
                continue

            if correct_answer.lower() in text.lower():
                print("Clicking:", _first_line(text))
                try:
                    driver.execute_script(
                        "arguments[0].scrollIntoView({block:'center'});",
                        opt
                    )
                    opt.click()
                    clicked = True
                except StaleElementReferenceException:
                    print("Element went stale, skipping click.")
                break

        if not clicked:
            print("Answer found but option text not matched.")

        answered += 1

        # Wait for the result screen to pass before looking for next question
        time.sleep(3)

    return answered