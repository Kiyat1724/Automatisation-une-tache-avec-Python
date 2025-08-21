import requests                     # Bibliothèque qui permet d'envoyer des requêtes HTTP (télécharger des pages web)
from bs4 import BeautifulSoup       # Outil pour analyser (parser) du HTML facilement 
import csv                          # Pour écrire ou lire des fichiers CSV (tableurs)
import re                           # Expressions régulières (recherche ou extraire des motifs dans du texte)


#Ecriture d'un script python en se basant d'une page produit sur le site de Books to Scrape
# -------------------------------
# CONFIGURATION
# -------------------------------
# Lien de la page de la catégorie "Fiction"
BASE_URL = "https://books.toscrape.com/catalogue/category/books/fiction_10/index.html"          # URL de départ : page catégorie

# Domaine de base du site (pour reconstruire les liens complets vers les livres et les images)
DOMAIN = "https://books.toscrape.com/catalogue/"                                                # Préfixe commun aux URLs relatives des livres/images

# -------------------------------
# FONCTION : Télécharger et parser une page HTML
# -------------------------------
def get_soup(url):
    """
    Cette fonction télécharge le contenu HTML d'une page web
    et le convertit en objet "soup" (structure facile à analyser avec BeautifulSoup).
    """
    print(f"[INFO] Récupération de la page : {url}")        # Affiche dans la console l'URL en cours de chargement
    response = requests.get(url)          # On envoie une requête HTTP GET pour obtenir la page
    response.raise_for_status()           # Si la page ne répond pas correctement, on arrête le script; Autrement lève une erreur si le statut HTTP n'est pas 200 (OK) 
    return BeautifulSoup(response.text, "html.parser")  # On transforme le HTML brut en objet exploitable

# -------------------------------
# FONCTION : Extraire les infos d'un livre
# -------------------------------
def extract_book_data(book_url):
    """
    Cette fonction prend l'URL d'un livre et va chercher
    toutes les informations demandées dans l'énoncé :
    - UPC
    - Titre
    - Prix TTC et HT
    - Disponibilité
    - Description
    - Catégorie
    - Note
    - URL de l'image
    """
    print(f"   └── Scraping du livre : {book_url}")     # Indique quel livre est en cours de scraping
    soup = get_soup(book_url)                           # Télécharge/parse la page du livre

    # Bloc principal qui contient le titre et la note
    product_main = soup.find("div", class_="product_main")      # Récupère le texte du <h1> et supprime les espaces superflus

    # ------------------ TITRE ------------------
    title = product_main.find("h1").text.strip()

    # ------------------ TABLEAU D'INFOS PRODUIT ------------------
    # Ce tableau contient l'UPC, prix, disponibilité, etc.
    table = soup.find("table", class_="table table-striped")                                # Sélectionne le tableau des specs
    data = {row.th.text.strip(): row.td.text.strip() for row in table.find_all("tr")}       # Construit un dict {clé: valeur}   
    upc = data.get("UPC")                                                                   # Code produit unique 
    price_excl_tax = data.get("Price (excl. tax)")                                          # Prix HT (hors taxes)
    price_incl_tax = data.get("Price (incl. tax)")                                          # Prix TTC (toutes taxes comprises)
    availability = data.get("Availability")                                                 # Texte de dispo (ex:"In stock (22 available)")

    # ------------------ DISPONIBILITÉ ------------------
    # Exemple : "In stock (22 available)" → on récupère uniquement le chiffre
    number_available = "0"                                                                  # Valeur par défaut si pas trouvé 
    if availability:                                                                        # Si le champ existe
        match = re.search(r"\((\d+) available\)", availability)                             # Cherche un nombre dans les parenthèses
        number_available = match.group(1) if match else "0"                                 # Récupère le nombre trouvé, sinon "0"

    # ------------------ DESCRIPTION ------------------
    description_tag = soup.find("div", id="product_description")                                    # Localise le bloc "product_description"
    product_description = description_tag.find_next("p").text.strip() if description_tag else ""    # Le <p> suivant contient le texte 

    # ------------------ CATÉGORIE ------------------
    # On trouve la catégorie dans le fil d’Ariane (breadcrumb)
    category = soup.find("ul", class_="breadcrumb").find_all("li")[2].text.strip()                  # 3e élément du breadcrumb = catégorie

    # ------------------ NOTE (review rating) ------------------
    # Exemple : <p class="star-rating Three"> → On récupère "Three" et on le convertit en chiffre
    rating_tag = product_main.find("p", class_="star-rating")                                           # Paragraphe avec classe "star-rating..."
    rating = rating_tag["class"][1] if rating_tag else "Zero"                                           # Deuxième classe ="One/Two/Three/Four/Five"
    rating_map = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}                                 # Conversion texte => entier 
    review_rating = rating_map.get(rating, 0)                                                           # Donne 0 si pas de note détextée 

    # ------------------ IMAGE ------------------
    # L’URL de l’image est relative → on la transforme en URL complète
    image_url = soup.find("div", class_="item active").img["src"].replace("../../", DOMAIN)             # Remplace le préfixe relatif par domain

    # ------------------ DICTIONNAIRE FINAL ------------------
    # On renvoie toutes les informations dans une structure facile à écrire dans un CSV
    return {
        "product_page_url": book_url,                                                               # URL de la fiche produit
        "universal_product_code (upc)": upc,                                                        # UPC
        "title": title,                                                                             # Titre du livre
        "price_including_tax": price_incl_tax,                                                      # Prix TTC
        "price_excluding_tax": price_excl_tax,                                                      # pRIX HT 
        "number_available": number_available,                                                       # Quantité disponible (nombre)
        "product_description": product_description,                                                 # Description du livre 
        "category": category,                                                                       # Catégorie (ex: Fiction)
        "review_rating": review_rating,                                                             # Note (1 à 5)
        "image_url": image_url                                                                      # URL absolue de l'image 
    }

# -------------------------------
# FONCTION PRINCIPALE : orchestrer le scraping
# -------------------------------
def main():
    """
    Fonction principale qui :
    1. Va chercher la page "Fiction"
    2. Récupère la liste des liens de livres
    3. Scrape chaque livre
    4. Sauvegarde les résultats dans un fichier CSV
    """
    print("[INFO] Début du scraping de la catégorie Fiction")                   # Message d'introduction

    # Charger la page catégorie Fiction
    soup = get_soup(BASE_URL)                                                   # Télécharge/parse la page catégorie 

    # Trouver tous les liens vers les pages de détail des livres
    book_links = soup.select("h3 a")                                            # Séléctionne tous les <a> à l'intérieur des <h3>
    print(f"[INFO] {len(book_links)} livres trouvés sur la page Fiction")       # Affiche le nombre de livres détectés

    # Liste pour stocker tous les résultats
    all_books = []                                                              # Sera remplie de dictionnaire (1 par livre)

    # Parcourir chaque lien de livre
    for a in book_links:                                    # Pour chaque balise <a> (un livre)
        relative_url = a["href"].replace("../../../", "")   # Nettoyage du lien relatif fournie par le site 
        book_url = DOMAIN + relative_url                    # Construire l'URL absolue vers la fiche produit
        book_data = extract_book_data(book_url)             # Scraper les infos détaillés du livre
        all_books.append(book_data)                         # Ajouter le résultat à la liste globale aux résultats

    # ------------------ ÉCRITURE CSV ------------------
    csv_file = "fiction_books.csv"
    print(f"[INFO] Écriture des données dans le fichier : {csv_file}")

    # On ouvre le fichier CSV et on écrit toutes les données
    with open(csv_file, "w", newline="", encoding="utf-8") as f:                # Ouvre le fichier en écriture, encodage UTF-8
        writer = csv.DictWriter(f, fieldnames=[                                 # Prépare un fichier CSV avec des colonnes nomées
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
        writer.writeheader()      # On écrit la première ligne (les noms de colonnes)       # écrit la ligne d'en-tête (noms des colonnes)
        writer.writerows(all_books)  # On écrit toutes les lignes de données                # écrit une ligne par dictionnaire de all_books

    print("[✅] Scraping terminé avec succès !")                                            # Message de succès
    print(f"[✅] Les données ont été sauvegardées dans le fichier : {csv_file}")            # Confirmation du fichier crée

# -------------------------------
# POINT D’ENTRÉE DU SCRIPT
# -------------------------------
if __name__ == "__main__":                                          # Ce bloc s'exécute uniquement si le fichier est lancé directement (pas importé)
    main()                                                          # Appel de la fonction principale 

