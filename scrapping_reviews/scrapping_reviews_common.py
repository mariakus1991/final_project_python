import re
import time
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

OUTPUT_CSV = Path(__file__).parent / "processed_reviews.csv"

MALE_NAMES = {
    "александр", "алексей", "андрей", "антон", "артём", "артем", "богдан",
    "борис", "вадим", "валентин", "валерий", "василий", "виктор", "виталий",
    "владимир", "владислав", "вячеслав", "геннадий", "георгий", "григорий",
    "данил", "даниил", "денис", "дмитрий", "евгений", "егор", "иван", "игорь",
    "илья", "кирилл", "константин", "леонид", "максим", "михаил", "никита",
    "николай", "олег", "павел", "пётр", "петр", "роман", "руслан", "сергей",
    "станислав", "степан", "тимофей", "фёдор", "федор", "эдуард", "юрий",
    "ярослав",
}
FEMALE_NAMES = {
    "александра", "алина", "алла", "анастасия", "ангелина", "анна", "валентина",
    "валерия", "вера", "вероника", "виктория", "галина", "дарья", "евгения",
    "екатерина", "елена", "елизавета", "жанна", "зинаида", "зоя", "инна",
    "ирина", "кристина", "ксения", "лариса", "лидия", "любовь", "людмила",
    "маргарита", "марго", "марина", "мария", "надежда", "наталья", "нина",
    "оксана", "ольга", "полина", "раиса", "светлана", "софья", "софия",
    "тамара", "татьяна", "юлия", "яна",
}
MALE_NAME_EXCEPTIONS = {"никита", "илья", "фома", "кузьма", "лука", "саша"}

RU_MONTHS = {
    "января": 1,
    "февраля": 2,
    "марта": 3,
    "апреля": 4,
    "мая": 5,
    "июня": 6,
    "июля": 7,
    "августа": 8,
    "сентября": 9,
    "октября": 10,
    "ноября": 11,
    "декабря": 12,
}


def format_review_date(date_text):
    if not date_text:
        return ""

    date_text = date_text.strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_text):
        return date_text

    normalized = date_text.lower().replace("ё", "е")
    today = date.today()
    if normalized.startswith("сегодня"):
        return today.strftime("%Y-%m-%d")
    if normalized.startswith("вчера"):
        return (today - timedelta(days=1)).strftime("%Y-%m-%d")

    match = re.search(r"(\d{1,2})\s+([а-яё]+)", normalized)
    if not match:
        return date_text

    day = int(match.group(1))
    month = RU_MONTHS.get(match.group(2))
    if not month:
        return date_text

    year = today.year
    parsed = date(year, month, day)
    if parsed > today:
        parsed = date(year - 1, month, day)

    return parsed.strftime("%Y-%m-%d")


def extract_author_name(author_text):
    if not author_text:
        return ""
    return author_text.split("\n")[0].strip().split(" ")[0].strip()


def detect_author_sex(author_text):
    name = extract_author_name(author_text)
    normalized = name.lower().replace("ё", "е")
    if normalized in MALE_NAMES:
        return "мужской"
    if normalized in FEMALE_NAMES:
        return "женский"
    if normalized in MALE_NAME_EXCEPTIONS:
        return "мужской"
    if normalized.endswith(("а", "я")):
        return "женский"
    if re.fullmatch(r"[а-яё-]+", normalized):
        return "мужской"

    print(f"Неизвестно: {name}")
    return "неизвестно"


def get_text(parent, selector):
    try:
        return parent.find_element(By.CSS_SELECTOR, selector).text.strip()
    except NoSuchElementException:
        return ""


def get_rating_from_selectors(parent, rating_selectors):
    for stars, selector in rating_selectors.items():
        if parent.find_elements(By.CSS_SELECTOR, selector):
            return stars
    return None


def get_rating_from_star_count(parent, rating_block_selector, selected_selector):
    try:
        rating_block = parent.find_element(By.CSS_SELECTOR, rating_block_selector)
    except NoSuchElementException:
        return None
    return len(rating_block.find_elements(By.CSS_SELECTOR, selected_selector))


def parse_review(block, header_selector, date_selector, text_selector, get_rating_fn):
    author_raw = get_text(block, header_selector)
    return {
        "author": extract_author_name(author_raw),
        "sex": detect_author_sex(author_raw),
        "date": format_review_date(get_text(block, date_selector)),
        "rating": get_rating_fn(block),
        "text": get_text(block, text_selector),
    }


def scroll_to_review_blocks(driver, selector, pause=2, max_attempts=10):
    for _ in range(max_attempts):
        blocks = driver.find_elements(By.CSS_SELECTOR, selector)
        if blocks:
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", blocks[0]
            )
            time.sleep(pause)
            return
        driver.execute_script("window.scrollBy(0, window.innerHeight);")
        time.sleep(pause)


def scroll_through_reviews(driver, selector, pause=2, max_attempts=10):
    last_count = 0
    for _ in range(max_attempts):
        blocks = driver.find_elements(By.CSS_SELECTOR, selector)
        if not blocks:
            break
        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'end'});", blocks[-1]
        )
        time.sleep(pause)
        count = len(driver.find_elements(By.CSS_SELECTOR, selector))
        if count == last_count:
            break
        last_count = count


def scroll_to_bottom(driver, pause=2, max_attempts=3):
    last_height = 0
    for _ in range(max_attempts):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(pause)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height


def save_reviews_to_csv(reviews, output_path, marketplace, debug=False):
    if debug:
        for i, review in enumerate(reviews, start=1):
            print(f"Review {i}: {review}")

    df = pd.DataFrame(
        {
            "create_date": [review["date"] for review in reviews],
            "name": [review["author"] for review in reviews],
            "sex": [review["sex"] for review in reviews],
            "review": [review["text"] for review in reviews],
            "rate": [
                float(review["rating"]) if review["rating"] is not None else None
                for review in reviews
            ],
            "market": [marketplace] * len(reviews),
        }
    )
    file_exists = Path(output_path).exists()
    df.to_csv(
        output_path,
        mode="a" if file_exists else "w",
        header=not file_exists,
        index=False,
    )
