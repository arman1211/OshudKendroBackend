import requests
import csv
import time
from tqdm import tqdm


BASE_URL = "https://medeasy.health/_next/data/Y1HE6dHcgAJ3VgyeXKrAh/en/category/otc-medicine.json"
CSV_FILE = "medeasy_products.csv"


def fetch_page(page_number):
    params = {"page": page_number, "slug": "otc-medicine"}
    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching page {page_number}: {e}")
        return None


def extract_product_data(product):
    print(product)
    return {
        "id": product.get("id"),
        "medicine_name": product.get("medicine_name"),
        "generic_name": product.get("generic_name"),
        "strength": product.get("strength"),
        "manufacturer_name": product.get("manufacturer_name"),
        "category_name": product.get("category_name"),
        "is_available": product.get("is_available"),
        "rx_required": product.get("rx_required"),
        "discount_type": product.get("discount_type"),
        "discount_value": product.get("discount_value"),
        "medicine_image": product.get("medicine_image"),
        "slug": product.get("slug"),
        "unit_prices": "; ".join(
            [f"{u['unit']}: {u['price']}" for u in product.get("unit_prices", [])]
        ),
    }


def scrape_all_pages():
    all_products = []
    page = 1
    has_more = True

    with tqdm(desc="Scraping pages") as pbar:
        while has_more:
            data = fetch_page(page)
            if not data:
                break

            page_props = data.get("pageProps", {})
            products = page_props.get("products", [])
            pagination = page_props.get("pagination", {})

            for product in products:
                all_products.append(extract_product_data(product))

            has_more = pagination.get("has_next", False)
            page += 1
            pbar.update(1)

            time.sleep(1)

    return all_products


def save_to_csv(products):
    if not products:
        print("No products to save")
        return

    fieldnames = [
        "id",
        "medicine_name",
        "generic_name",
        "strength",
        "manufacturer_name",
        "category_name",
        "is_available",
        "rx_required",
        "discount_type",
        "discount_value",
        "medicine_image",
        "slug",
        "unit_prices",
    ]

    with open(CSV_FILE, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(products)

    print(f"Successfully saved {len(products)} products to {CSV_FILE}")


def main():
    print("Starting MedEasy product scraper...")
    products = scrape_all_pages()
    save_to_csv(products)
    print("Scraping completed!")


if __name__ == "__main__":
    main()
