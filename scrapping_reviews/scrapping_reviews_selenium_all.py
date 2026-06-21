from scrapping_reviews_common import OUTPUT_CSV
from scrapping_reviews_selenium_ozon import scrape_reviews as scrape_ozon
from scrapping_reviews_selenium_wb import scrape_reviews as scrape_wb
from scrapping_reviews_selenium_ya import scrape_reviews as scrape_ya

CHROME_VERSION = 149


def scrape_all(output_path=OUTPUT_CSV, chrome_version=CHROME_VERSION):
    results = {}

    print("Scraping Wildberries...")
    results["Wildberries"] = scrape_wb(output_path, chrome_version)
    print(f"Wildberries: {results['Wildberries']} reviews saved")

    print("Scraping Ozon...")
    results["Ozon"] = scrape_ozon(output_path, chrome_version)
    print(f"Ozon: {results['Ozon']} reviews saved")

    print("Scraping Я.Маркет...")
    results["Я.Маркет"] = scrape_ya(output_path, chrome_version)
    print(f"Я.Маркет: {results['Я.Маркет']} reviews saved")

    total = sum(results.values())
    print(f"Total: {total} reviews saved to {output_path}")
    return results


if __name__ == "__main__":
    scrape_all()
