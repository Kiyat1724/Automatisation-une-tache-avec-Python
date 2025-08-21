import requests
from bs4 import BeautifulSoup
import csv
import re

# -------------------------------
# CONFIGURATION
# -------------------------------
BASE_URL = "https://books.toscrape.com/catalogue/category/books/fiction_10/"
DOMAIN = "https://books.toscrape.com/catalogue/"

def get_soup(url):
    """Télécharge et parse une page HTML"""
    print(f"[INFO] Récupération de la page : {url}")
    response = requests.get(url)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")

def extract_book_data(book_url):
    """Scrape toutes les infos d’un livre"""
    print(f"   └── Scraping du livre : {book_url}")
    soup = get_soup(book_url)

    product_main = soup.find("div", class_="product_main")

    # Titre
    title = product_main.find("h1").text.strip()

    # Tableau infos produit
    table = soup.find("table", class_="table table-striped")
    data = {row.th.text.strip(): row.td.text.strip() for row in table.find_all("tr")}
    upc = data.get("UPC")
    price_excl_tax = data.get("Price (excl. tax)")
    price_incl_tax = data.get("Price (incl. tax)")
    availability = data.get("Availability")

    # Nombre disponible
    number_available = "0"
    if availability:
        match = re.search(r"\((\d+) available\)", availability)
        number_available = match.group(1) if match else "0"

    # Description
    description_tag = soup.find("div", id="product_description")
    product_description = description_tag.find_next("p").text.strip() if description_tag else ""

    # Catégorie
    category = soup.find("ul", class_="breadcrumb").find_all("li")[2].text.strip()

    # Review rating
    rating_tag = product_main.find("p", class_="star-rating")
    rating = rating_tag["class"][1] if rating_tag else "Zero"
    rating_map = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
    review_rating = rating_map.get(rating, 0)

    # Image
    image_url = soup.find("div", class_="item active").img["src"].replace("../../", DOMAIN)

    return {
        "product_page_url": book_url,
        "universal_product_code (upc)": upc,
        "title": title,
        "price_including_tax": price_incl_tax,
        "price_excluding_tax": price_excl_tax,
        "number_available": number_available,
        "product_description": product_description,
        "category": category,
        "review_rating": review_rating,
        "image_url": image_url
    }

def scrape_category(base_url):
    """Scrape toutes les pages d'une catégorie"""
    all_books = []
    page_url = base_url + "index.html"

    while page_url:
        soup = get_soup(page_url)

        # Récupérer les liens des livres sur cette page
        book_links = soup.select("h3 a")
        print(f"[INFO] {len(book_links)} livres trouvés sur {page_url}")

        for a in book_links:
            relative_url = a["href"].replace("../../../", "")
            book_url = DOMAIN + relative_url
            book_data = extract_book_data(book_url)
            all_books.append(book_data)

        # Vérifier s’il y a une page suivante
        next_button = soup.find("li", class_="next")
        if next_button:
            next_page = next_button.a["href"]
            page_url = base_url + next_page
        else:
            page_url = None  # Fin de la boucle

    return all_books

def main():
    print("[INFO] Début du scraping de la catégorie Fiction")
    all_books = scrape_category(BASE_URL)

    # Écriture CSV
    csv_file = "All_fiction_books.csv"
    print(f"[INFO] Écriture des données dans le fichier : {csv_file}")

    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "product_page_url",
            "universal_product_code (upc)",
            "title",
            "price_including_tax",
            "price_excluding_tax",
            "number_available",
            "product_description",
            "category",
            "review_rating",
            "image_url"
        ])
        writer.writeheader()
        writer.writerows(all_books)

    print("[✅] Scraping terminé avec succès !")
    print(f"[✅] {len(all_books)} livres ont été sauvegardés dans {csv_file}")

if __name__ == "__main__":
    main()


