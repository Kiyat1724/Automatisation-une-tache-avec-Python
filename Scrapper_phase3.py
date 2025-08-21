import requests                 # permet de télécharger des pages web (HTTP)
from bs4 import BeautifulSoup   # permet d'analyser (parser) du HTML facilement
import csv                      # pour écrire les données dans un fichier CSV
import re                       # pour utiliser des expressions régulières (extractions de texte)
from tqdm import tqdm           # ✅ affiche une barre de progression dans la console

# Domaine principal du site (utilisé pour construire des URLs complètes)
BASE_SITE = "https://books.toscrape.com/"

# Partie du site où se trouvent les fiches détaillées des livres
CATALOGUE = "https://books.toscrape.com/catalogue/"

# Fonctions utilitaires
def get_soup(url):
    """Télécharge et parse une page HTML."""
    response = requests.get(url) # envoie une requête HTTP GET vers l'URL
    response.raise_for_status()  # lève une erreur si le statut HTTP n'est pas 200 (OK)
    
    # Transforme le texte HTML en un objet BeautifulSoup pour faciliter la recherche d'éléments
    return BeautifulSoup(response.text, "html.parser")

#   Extraction d'un livre 

def extract_book_data(book_url):
    """Scrape toutes les infos d'un livre donné (à partir de son URL)."""
    soup = get_soup(book_url)

#   La selection "product_main" contient titre, prix, rating, etc.
    product_main = soup.find("div", class_="product_main")

#   Titre
#   On cherche le <h1> dans "product_main" et on supprime les espaces inutiles
    title = product_main.find("h1").text.strip()

#   Tableau infos produit(UPC, prix, disponibilité ...)
#   On récupère le tableau <table  class="table table-striped"> puis chaque ligne <tr>
    table = soup.find("table", class_="table table-striped")
    data = {row.th.text.strip(): row.td.text.strip() for row in table.find_all("tr")}
    upc = data.get("UPC")                               # Code produit unique
    price_excl_tax = data.get("Price (excl. tax)")      # Prix hors taxes
    price_incl_tax = data.get("Price (incl. tax)")      # Prix TTC
    availability = data.get("Availability")             # Chaîne contenant le stock

    # Nombre d'expemples disponibles
    # Exemple d'availability : "In stock (22 available)"
    number_available = "0"      # Valeur par défaut
    if availability:
        # On cherche un nombre entre parenthèse avant "available"
        match = re.search(r"\((\d+) available\)", availability)
        # Si trouvé, on prend le premier groupe capturé (le nombre) sinon "0"
        number_available = match.group(1) if match else "0"

    # Description d'un produit
    # La description se trouve après un <div id="product_description"> puis dans le <p> suivant
    description_tag = soup.find("div", id="product_description")
    product_description = description_tag.find_next("p").text.strip() if description_tag else ""

    # Catégorie
    # Le fil d'Ariane (breadcrum) est une liste <ul>; la 3e <li> (index2) est la catégorie
    category = soup.find("ul", class_="breadcrumb").find_all("li")[2].text.strip()

    #  Note (Review rating)
    #  La note est encodée via une classe CSS du style "star-rating Three"
    rating_tag = product_main.find("p", class_="star-rating")
    rating = rating_tag["class"][1] if rating_tag else "Zero"               # "One", "Two", etc.
    rating_map = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
    review_rating = rating_map.get(rating, 0)                               # Convertit en entier (O si absent)

    # URL de l'Image
    # L'attribut src est relatif (commence par ../../); on le convertit en URL absolue
    image_url = soup.find("div", class_="item active").img["src"].replace("../../", CATALOGUE)

    # On renvoie toutes les informations sous forme de dictionnaire (clé=> valeur)
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


    # Scraping d'une catégorie complète 
def scrape_category(category_name, category_url):
    """Scrape toutes les pages et livres d'une catégorie donnée avec barre de progression."""
    print(f"\n[INFO] Début du scraping de la catégorie : {category_name}")
    all_books = []                          # Liste qui contiendra les dictionnaires de tous les livres 
    page_url = category_url                 # URL courante de page (on commence par la première)

    # On boucle tant qu'il existe une page à traiter 
    while page_url:
        soup = get_soup(page_url)       # Télécharge/parse la page de la catégorie

        # Liens des livres sur la page
        # Chaque livre est dans un <h3><a href="..."></a></h3>
        book_links = soup.select("h3 a")

        # ✅ Barre de progression sur les livres de cette page
        for a in tqdm(book_links, desc=f"Scraping {category_name}", unit="livre"):
        #   Les URLs de détail sont relatives; on enlève "../../../" pour construire une URL complète
            relative_url = a["href"].replace("../../../", "")
            book_url = CATALOGUE + relative_url                 # Construit l'URL absolue du livre 
            book_data = extract_book_data(book_url)             # Récupère les infos du livre 
            all_books.append(book_data)                         # Ajoute le dictionnaire à la liste 

        # Pagination : Vérifier s’il y a une page suivante
        next_button = soup.find("li", class_="next")        # <li class="next"><a href="page-2.html">
        if next_button:
            next_page = next_button.a["href"]               # "page-2.html" (exemple)
            base = page_url.rsplit("/", 1)[0] + "/"         # On garde le dossier de base de la page courante
            page_url = base + next_page                     # Construit l'URL de la page suivante
        else:
            page_url = None                                 # Plus de page suivante => on arrête la boucle 

    # Sauvegarde des résultats dans un CSV spécifique à la catégorie
    filename = f"V2_{category_name.replace(' ', '_')}.csv"                  # Nom de fichier basé sur la catégorie
    print(f"[INFO] Écriture des données dans le fichier : {filename}")
    # Ouverture du fichier en écriture, encodage UTF-8, sans lignes vides superflues (newline="")
    with open(filename, "w", newline="", encoding="utf-8") as f:
    # On définit l'ordre et les noms des colonnes
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
        writer.writeheader()                    # écrit la première ligne d'en-têtes de colonnes
        writer.writerows(all_books)             # écrit chaque dictionnaire de all_books comme une ligne csv
        
# Petit récapitulatif en console
    print(f"[✅] {len(all_books)} livres sauvegardés dans {filename}")

# Point d'entrée principal

def main():
    """Scrape tout le site et génère un CSV par catégorie."""
    print("[INFO] Scraping du site complet en cours...")

    soup = get_soup(BASE_SITE)          # Récupère la page d'accueil 

    # Récupéreration de la liste des catégories depuis la barre latérale)
    categories = soup.select("div.side_categories ul li ul li a")

# On parcourt chaque lien de catégorie
    for cat in categories:
        category_name = cat.text.strip()                # Nom affiché de la catégorie
        category_url = BASE_SITE + cat["href"]          # URL absolue de la catégorie
        scrape_category(category_name, category_url)    # Scrape et exporte le CSV

    print("\n[✅] Scraping du site terminé avec succès !")

# Lancement du script uniquement si exécuté directement 
# Ce bloc empêche l'éxécution de main() quand le fichier est importé comme module. 
if __name__ == "__main__":
    main()



