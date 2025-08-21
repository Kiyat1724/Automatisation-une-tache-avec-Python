import requests
from bs4 import BeautifulSoup
import csv
import os
from tqdm import tqdm

BASE_URL = "https://books.toscrape.com/"
DOMAIN = "https://books.toscrape.com/catalogue/"

def get_soup(url):
    """Télécharge le contenu HTML d'une page et retourne un objet BeautifulSoup."""
    response = requests.get(url)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")

def extract_book_data(book_url, category_name, images_dir):
    """Extrait toutes les informations d'un livre donné et télécharge son image."""
    soup = get_soup(book_url)
    product_main = soup.find("div", class_="product_main")

    # Titre
    title = product_main.find("h1").text.strip()

    # Tableau d'infos produit (UPC, prix, disponibilité, etc.)
    table = soup.find("table", class_="table table-striped")
    data = {row.th.text.strip(): row.td.text.strip() for row in table.find_all("tr")}
    upc = data.get("UPC")
    price_excl_tax = data.get("Price (excl. tax)")
    price_incl_tax = data.get("Price (incl. tax)")
    availability = data.get("Availability")

    # Nombre disponible (extraction via regex)
    number_available = "0"
    if availability:
        import re
        match = re.search(r"\((\d+) available\)", availability)
        number_available = match.group(1) if match else "0"

    # Description
    description_tag = soup.find("div", id="product_description")
    product_description = description_tag.find_next("p").text.strip() if description_tag else ""

    # Catégorie (breadcrumb → le 3e élément est la catégorie)
    category = soup.find("ul", class_="breadcrumb").find_all("li")[2].text.strip()

    # Note (ex: "star-rating Three")
    rating_tag = product_main.find("p", class_="star-rating")
    rating = rating_tag["class"][1] if rating_tag else "Zero"
    rating_map = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
    review_rating = rating_map.get(rating, 0)

    # Image URL (corriger le chemin relatif → URL absolue)
    image_url = soup.find("div", class_="item active").img["src"].replace("../../", BASE_URL)

    # --- Téléchargement de l'image ---
    os.makedirs(os.path.join(images_dir, category_name), exist_ok=True)
    image_filename = os.path.join(images_dir, category_name, f"{upc}.jpg")
    try:
        img_data = requests.get(image_url).content
        with open(image_filename, "wb") as handler:
            handler.write(img_data)
    except Exception as e:
        print(f"⚠️ Erreur lors du téléchargement de l'image pour {title}: {e}")

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

def scrape_category(category_name, category_url):
    """Scrape tous les livres d'une catégorie donnée et sauvegarde un CSV + images."""
    print(f"\n📚 Scraping catégorie: {category_name}")

    page_url = category_url
    all_books = []
    images_dir = "V4_images"

    while True:
        soup = get_soup(page_url)
        book_links = soup.select("h3 a")

        for a in tqdm(book_links, desc=f"Catégorie {category_name}", unit="livre"):
            relative_url = a["href"].replace("../../../", "")
            book_url = DOMAIN + relative_url
            book_data = extract_book_data(book_url, category_name, images_dir)
            all_books.append(book_data)

        # Vérifier s’il existe une page suivante
        next_button = soup.find("li", class_="next")
        if next_button:
            next_page = next_button.a["href"]
            page_url = "/".join(page_url.split("/")[:-1]) + "/" + next_page
        else:
            break

    # Sauvegarde en CSV
    os.makedirs("csv", exist_ok=True)
    csv_file = os.path.join("csv", f"V4_{category_name}.csv")
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

    print(f"✅ {len(all_books)} livres sauvegardés dans {csv_file}")
    print(f"✅ Images enregistrées dans dossier: {os.path.join(images_dir, category_name)}")

def main():
    """Scrape toutes les catégories du site books.toscrape.com"""
    print("🚀 Lancement du scraping complet du site...")

    homepage = get_soup(BASE_URL)
    categories = homepage.select("div.side_categories ul li ul li a")

    for cat in categories:
        category_name = cat.text.strip()
        category_url = BASE_URL + cat["href"]
        scrape_category(category_name, category_url)

    print("\n🎉 Scraping terminé pour toutes les catégories !")

if __name__ == "__main__":
    main()
