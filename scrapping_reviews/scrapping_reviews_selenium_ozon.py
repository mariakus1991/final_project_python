import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from scrapping_reviews_common import (
    OUTPUT_CSV,
    get_rating_from_star_count,
    parse_review,
    save_reviews_to_csv,
    scroll_through_reviews,
    scroll_to_review_blocks,
)

REVIEW_BLOCK_SELECTOR = ".jn5_24"
REVIEW_TEXT_SELECTOR = ".m9j_24"
REVIEW_HEADER_SELECTOR = ".tsCompactControl500Medium"
REVIEW_DATE_SELECTOR = ".j8m_24"
RATING_BLOCK_SELECTOR = ".a5d5_4_1-a.a5d5_4_1-a1"
RATING_SELECTORS_SELECTED = ".a5d5_4_1-a8.undefined.a5d5_4_1-a9"
MARKETPLACE = "Ozon"
URL = (
    "https://www.ozon.ru/product/sredstvo-dlya-mytya-posudy-synergetic-gel-balzam"
    "-bazilik-i-svezhaya-myata-5-l-1706870951/?oos_search=false&reviewsVariantMode=1"
)


def get_rating(parent):
    return get_rating_from_star_count(
        parent, RATING_BLOCK_SELECTOR, RATING_SELECTORS_SELECTED
    )


def scrape_reviews(output_path=OUTPUT_CSV, chrome_version=149, debug=False):
    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = uc.Chrome(options=options, version_main=chrome_version)
    try:
        driver.get(URL)
        scroll_to_review_blocks(driver, REVIEW_BLOCK_SELECTOR, pause=2)

        wait = WebDriverWait(driver, 100)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, REVIEW_BLOCK_SELECTOR)))

        scroll_through_reviews(driver, REVIEW_BLOCK_SELECTOR, pause=2)

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

        save_reviews_to_csv(reviews, output_path, MARKETPLACE, debug=debug)
        return len(reviews)
    finally:
        driver.quit()


if __name__ == "__main__":
    count = scrape_reviews(debug=True)
    print(f"Ozon: {count} reviews saved")
