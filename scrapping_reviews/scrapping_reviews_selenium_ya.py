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
)

REVIEW_BLOCK_SELECTOR = ".ds-flex.ds-flex_col.ds-flex_gr_1._3NaES"
REVIEW_TEXT_SELECTOR = "._1xJG9"
REVIEW_HEADER_SELECTOR = ".ds-text.ds-text_group_core.ds-text_lineClamp_1.ds-text_weight_bold.ds-text_typography_text.ds-text_text_tight.ds-text_text_bold.ds-text_lineClamp"
REVIEW_DATE_SELECTOR = ".ds-text.ds-text_group_core.ds-text_weight_reg.ds-text_color_text-secondary.ds-text_typography_text.ds-text_text_tight.ds-text_text_reg"
RATING_BLOCK_SELECTOR = ".ds-flex.ds-flex_ai_c._3jGJh"
RATING_SELECTORS_SELECTED = "._3jOGl.IzKc5._3uJps.v1Oe7"
MARKETPLACE = "Я.Маркет"
URL = (
    "https://market.yandex.ru/offers/synergetic-antibakterialnyi-gel-dlia-mytia-posudy"
    "-aloe-vera/1729318722/reviews?sku=101612036739"
)


def get_rating(parent):
    return get_rating_from_star_count(
        parent, RATING_BLOCK_SELECTOR, RATING_SELECTORS_SELECTED
    )


def scrape_reviews(output_path=OUTPUT_CSV, chrome_version=149):
    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = uc.Chrome(options=options, version_main=chrome_version)
    try:
        driver.get(URL)

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

        save_reviews_to_csv(reviews, output_path, MARKETPLACE)
        return len(reviews)
    finally:
        driver.quit()


if __name__ == "__main__":
    count = scrape_reviews()
    print(f"Я.Маркет: {count} reviews saved")
