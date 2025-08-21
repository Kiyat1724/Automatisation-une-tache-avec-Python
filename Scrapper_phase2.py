import requests                     # Librairie qui permet de télécharger des pages web (faire des requêtes HTTP)
from bs4 import BeautifulSoup       # Librairie qui permet d'analyser (parser) du code HTML facilement
import csv                          # Librairie pour écrire et lire des fichiers CSV
import re                           # Librairie pour travailler avec les expressions régulières (chercher un motif dans du texte)

# -------------------------------
# CONFIGURATION
# -------------------------------
BASE_URL = "https://books.toscrape.com/catalogue/category/books/fiction_10/"        # l'adresse de la catégorie Fiction du site 
DOMAIN = "https://books.toscrape.com/catalogue/"                                    # utilisé pour reconstruire les liens complets des livres


# -------------------------------
# Fonction pour télécharger une page 
# -------------------------------
def get_soup(url):
    """Télécharge et parse une page HTML"""
    print(f"[INFO] Récupération de la page : {url}")                # Message d'info pour l'utilisateur 
    response = requests.get(url)                                    # Télécharge la page web 
    response.raise_for_status()                                     # Vérifie qu'il n'y a pas d'erreur (404, 500, ...)
    return BeautifulSoup(response.text, "html.parser")              # Transforme le HTML en objet BeautifulSoup

# -------------------------------
# Fonction pour extraire les infos d'un livre 
# -------------------------------

def extract_book_data(book_url):
    """Scrape toutes les infos d’un livre"""
    print(f"   └── Scraping du livre : {book_url}")
    soup = get_soup(book_url)                                   # On récupère la page du livre 
# Récupération du bloc principal du produit 
    product_main = soup.find("div", class_="product_main")      

    # Titre
    title = product_main.find("h1").text.strip()

    # Récupération du tableau d'infos produit
    table = soup.find("table", class_="table table-striped")
    data = {row.th.text.strip(): row.td.text.strip() for row in table.find_all("tr")}
    
    # On crée un dictionnaire avec toutes les infos du tableau (UPC, prix, disponibilité...).
    upc = data.get("UPC")
    price_excl_tax = data.get("Price (excl. tax)")
    price_incl_tax = data.get("Price (incl. tax)")
    availability = data.get("Availability")

    # Nombre d'éxemplaires disponibles
    number_available = "0"
    if availability:
        match = re.search(r"\((\d+) available\)", availability)     # Cherche un nombre dans la phrase
        number_available = match.group(1) if match else "0"

    # Description du livre 
    description_tag = soup.find("div", id="product_description")
    product_description = description_tag.find_next("p").text.strip() if description_tag else ""

    # Catégorie du livre 
    category = soup.find("ul", class_="breadcrumb").find_all("li")[2].text.strip()

    # Review rating (note(étoiles))
    rating_tag = product_main.find("p", class_="star-rating")
    rating = rating_tag["class"][1] if rating_tag else "Zero"
    rating_map = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}     # Exemple:"One", "Two", etc.
    review_rating = rating_map.get(rating, 0)

    # Image
    image_url = soup.find("div", class_="item active").img["src"].replace("../../", DOMAIN)

    # Retourne toutes les infos dans un dictionnaire 
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

    # Fonction pour scraper toute une catégorie
def scrape_category(base_url):
    """Scrape toutes les pages d'une catégorie"""
    all_books = []
    page_url = base_url + "index.html"
    
    # Boucle sur toutes les pages

    while page_url:
        soup = get_soup(page_url)

        # Récupérer les liens des livres sur cette page
        book_links = soup.select("h3 a")
        print(f"[INFO] {len(book_links)} livres trouvés sur {page_url}")
        
    # Extraire chaque livre 
        for a in book_links:
            relative_url = a["href"].replace("../../../", "")       # Nettoyer l'URL 
            book_url = DOMAIN + relative_url                        # Construire l'URL complète
            book_data = extract_book_data(book_url)                 # Scraper le livre 
            all_books.append(book_data)                             # Ajouter à la liste 

        # Vérifier s’il y a une page suivante
        next_button = soup.find("li", class_="next")
        if next_button:
            next_page = next_button.a["href"]
            page_url = base_url + next_page
        else:
            page_url = None  # Pas de page suivante, on sort de la boucle
            
        # Retourner la liste des livres 
    return all_books
# -------------------------------
# Fonction principale
# -------------------------------
def main():
    print("[INFO] Début du scraping de la catégorie Fiction")
    all_books = scrape_category(BASE_URL)                       # Récupération de tous les livres

    # Écriture des résultats dans un fichier CSV
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
        writer.writeheader()                # écrire la première ligne (titres des colonnes)
        writer.writerows(all_books)         # écrire toutes les lignes (livres)

# -------------------------------
# Message final
# -------------------------------
    print("[✅] Scraping terminé avec succès !")
    print(f"[✅] {len(all_books)} livres ont été sauvegardés dans {csv_file}")

# -------------------------------
# Lancer le programme
# -------------------------------
if __name__ == "__main__":                  # Cela signifie: si on éxecute ce fichier directement, lancement de la fonction main(). 
    main()                                  # (Si l'on l'importes ailleurs, main() ne sera pas lancé automatiquement.)


