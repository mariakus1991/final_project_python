import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from scrapping_reviews_common import (
    OUTPUT_CSV,
    get_rating_from_selectors,
    parse_review,
    save_reviews_to_csv,
    scroll_to_bottom,
)

REVIEW_BLOCK_SELECTOR = ".comments__item.feedback.product-feedbacks__block-wrapper"
REVIEW_TEXT_SELECTOR = ".feedback__text--item"
REVIEW_HEADER_SELECTOR = ".feedback__header"
REVIEW_DATE_SELECTOR = ".feedback__date"
RATING_SELECTORS = {
    5: ".stars-line.star5",
    4: ".stars-line.star4",
    3: ".stars-line.star3",
    2: ".stars-line.star2",
    1: ".stars-line.star1",
}
MARKETPLACE = "Wildberries"
URL = (
    "https://www.wildberries.ru/catalog/264651515/feedbacks"
    "?imtId=2473727594&size=410784067"
)


def get_rating(parent):
    return get_rating_from_selectors(parent, RATING_SELECTORS)


def scrape_reviews(output_path=OUTPUT_CSV, chrome_version=149):
    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = uc.Chrome(options=options, version_main=chrome_version)
    try:
        driver.get(URL)

        wait = WebDriverWait(driver, 100)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, REVIEW_BLOCK_SELECTOR)))

        scroll_to_bottom(driver, pause=2)

        review_blocks = driver.find_elements(By.CSS_SELECTOR, REVIEW_BLOCK_SELECTOR)
        reviews = []
        for block in review_blocks:
            review = parse_review(
                block,
                REVIEW_HEADER_SELECTOR,
                REVIEW_DATE_SELECTOR,
                REVIEW_TEXT_SELECTOR,
                get_rating,
            )
            if any(review.values()):
                reviews.append(review)

        save_reviews_to_csv(reviews, output_path, MARKETPLACE)
        return len(reviews)
    finally:
        driver.quit()


if __name__ == "__main__":
    count = scrape_reviews()
    print(f"Wildberries: {count} reviews saved")
