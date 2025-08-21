import requests                     # Bibliothèque qui permet d'envoyer des requêtes HTTP (télécharger des pages web)
from bs4 import BeautifulSoup       # Librairie qui permet d'analyser (parser) du HTML facilement 
import csv                          # Permet d'écrire ou lire des fichiers CSV (tableurs)
import os                           # Permet de gérer les fichiers et dossiers (création et enregistrement)
from tqdm import tqdm               # Permet d'afficher une barre de progression sympa pendant les boucles 

# -------------------------------
# CONFIGURATION DE BASE
# -------------------------------

BASE_URL = "https://books.toscrape.com/"                # L'URL de la page d'accueil
DOMAIN = "https://books.toscrape.com/catalogue/"        # Domaine utilisé pour reconstruire les liens des livres 

# -------------------------------
# Télécharger et analyser une page HTML
# -------------------------------
def get_soup(url):
    """Télécharge le contenu HTML d'une page et retourne un objet BeautifulSoup."""
    response = requests.get(url)                            # Télécharger la page depuis internet 
    response.raise_for_status()                             # Vérifie qu'il n' y a pas d'erreur (402, 500...)
    return BeautifulSoup(response.text, "html.parser")      # Transforme le texte HTML en objet manipulable 

# -------------------------------
# Extraction des informations d'un livre
# -------------------------------

def extract_book_data(book_url, category_name, images_dir):
    """Extrait toutes les informations d'un livre donné et télécharge son image."""
    soup = get_soup(book_url)                                                           # On télécharge la page du livre 
    product_main = soup.find("div", class_="product_main")                              # On récupère le bloc principal (titre,prix, etc.)

    # Titre du livre
    title = product_main.find("h1").text.strip()

    # Tableau d'infos produit (UPC, prix, disponibilité, etc.)
    table = soup.find("table", class_="table table-striped")    # Le tableau des infos (UPC, prix, etc.)
    # On transforme le HTML en dictionnaire Python
    data = {row.th.text.strip(): row.td.text.strip() for row in table.find_all("tr")}
    
    # On récupère les infos principales
    upc = data.get("UPC")
    price_excl_tax = data.get("Price (excl. tax)")
    price_incl_tax = data.get("Price (incl. tax)")
    availability = data.get("Availability")

    # Nombre d'exemplaires disponibles (extraction via regex)
    number_available = "0"
    if availability:
        import re
        match = re.search(r"\((\d+) available\)", availability)         # Cherche un nombre dans le texte
        number_available = match.group(1) if match else "0"

    # Description du livre 
    description_tag = soup.find("div", id="product_description")
    product_description = description_tag.find_next("p").text.strip() if description_tag else ""

    # -------------------------------
    # Catégorie du livre
    # -------------------------------
    # Catégorie (breadcrumb → le 3e élément est la catégorie)
    category = soup.find("ul", class_="breadcrumb").find_all("li")[2].text.strip()

    # Note (nombre d'étoiles)
    # Note (ex: "star-rating Three")
    rating_tag = product_main.find("p", class_="star-rating")
    rating = rating_tag["class"][1] if rating_tag else "Zero"
    rating_map = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}         # Exemple: "One", "Two", "Three"...
    review_rating = rating_map.get(rating, 0)                                   # On converti en chiffre

    # URL de l'image (corriger le chemin relatif → URL absolue)
    image_url = soup.find("div", class_="item active").img["src"].replace("../../", BASE_URL)

    # --- Téléchargement de l'image ---
    os.makedirs(os.path.join(images_dir, category_name), exist_ok=True)     # Créer un dossier pour la catégorie (si déjà existant => pas d'erreur)
    image_filename = os.path.join(images_dir, category_name, f"{upc}.jpg")  # Le nom de l'image = code UPC du livre
    try:
        img_data = requests.get(image_url).content              # Télécharger l'image 
        with open(image_filename, "wb") as handler:             # Ouvre le fichier en mode "binaire"
            handler.write(img_data)                             # Enregistre l'image sur le disque
    except Exception as e:
        print(f"⚠️ Erreur lors du téléchargement de l'image pour {title}: {e}")

    # Retourner toutes les informations sous forme de dictionnaire
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

    # Scraper une catégorie entière 
def scrape_category(category_name, category_url):
    """Scrape tous les livres d'une catégorie donnée et sauvegarde un CSV + images."""
    print(f"\n📚 Scraping catégorie: {category_name}")

    page_url = category_url         # Lien de départ
    all_books = []                  # Liste où l'on stocke les infos de tous les livres
    images_dir = "V4_images"        # Dossier de sauvegarde des images

    # Boucle sur toutes les pages de la catéforie
    while True:
        soup = get_soup(page_url)           # On télécharge la page 
        book_links = soup.select("h3 a")    # Tous les liens des livres 

    # Extraction des infos de chaque livre 
        for a in tqdm(book_links, desc=f"Catégorie {category_name}", unit="livre"):
            relative_url = a["href"].replace("../../../", "")
            book_url = DOMAIN + relative_url                                    # Nettoie l'URL relative 
            book_data = extract_book_data(book_url, category_name, images_dir)  # Construit l'URL complète 
            all_books.append(book_data)

        # Vérifier s’il existe une page suivante
        next_button = soup.find("li", class_="next")
        if next_button:
            next_page = next_button.a["href"]
            page_url = "/".join(page_url.split("/")[:-1]) + "/" + next_page
        else:
            break               # pas de page suivante => on arrête la boucle 

    # Sauvegarde en CSV
    os.makedirs("csv", exist_ok=True)                               # Créer dossier "csv"
    csv_file = os.path.join("csv", f"V4_{category_name}.csv")       # Nom du fichier CSV
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
        writer.writeheader()                    # écrit les titres des colonnes
        writer.writerows(all_books)             # écrit toutes les données 
        
    # Confirmation 
    print(f"✅ {len(all_books)} livres sauvegardés dans {csv_file}")
    print(f"✅ Images enregistrées dans dossier: {os.path.join(images_dir, category_name)}")

    # -------------------------------
    # Programme principal
    # -------------------------------
def main():
    """Scrape toutes les catégories du site books.toscrape.com"""
    print("🚀 Lancement du scraping complet du site...")

    homepage = get_soup(BASE_URL)                           # Télécharge la page d'accueil
    categories = homepage.select("div.side_categories ul li ul li a")   # Récupération de la liste des catégories
    
    # -------------------------------
    # Boucle sur toutes les catégories
    # -------------------------------
    for cat in categories:
        category_name = cat.text.strip()                # Nom de la catégorie
        category_url = BASE_URL + cat["href"]           # URL complète 
        scrape_category(category_name, category_url)    # Scraper la catégorie

    # -------------------------------
    # Fin du scraping
    # -------------------------------
    print("\n🎉 Scraping terminé pour toutes les catégories !")
    
    # -------------------------------
    # Lancer le programme 
    # -------------------------------
if __name__ == "__main__":
    main()
