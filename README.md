# Scraping de books.toscrape.com

Ce projet contient des scripts Python permettant de scraper le site [Books to Scrape](https://books.toscrape.com/), d’extraire les informations produit de tous les livres, de télécharger leurs images et d’enregistrer les données dans des fichiers CSV.  

---

## Fonctionnalités

1. **Scraping par catégorie**
   - Extraction de toutes les catégories disponibles sur le site.
   - Parcours de **toutes les pages** pour chaque catégorie.
   - Extraction des informations suivantes pour chaque livre :
     - `product_page_url`
     - `universal_product_code (upc)`
     - `title`
     - `price_including_tax`
     - `price_excluding_tax`
     - `number_available`
     - `product_description`
     - `category`
     - `review_rating`
     - `image_url`
   - Les données sont enregistrées dans un **CSV séparé pour chaque catégorie** (`csv/<nom_categorie>.csv`).

2. **Téléchargement des images**
   - Chaque livre a son image téléchargée dans un dossier `images/<nom_categorie>/UPC.jpg`.
   - Création automatique des dossiers par catégorie.
   - Gestion des erreurs de téléchargement.

3. **Barre de progression**
   - Une barre de progression (`tqdm`) permet de visualiser l’avancement du scraping pour chaque catégorie et livre.

---

## Installation

1. Cloner ce dépôt ou copier les scripts sur votre machine.
2. Installer les dépendances Python nécessaires :

```bash
pip install requests beautifulsoup4 tqdm
