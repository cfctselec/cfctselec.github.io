#!/usr/bin/env python3
import json
import re
import os
import logging
import datetime # Importation pour le timestamp
import shutil
import unicodedata
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def slugify(text: str) -> str:
    """Simplifie le titre pour l'utiliser comme nom de dossier (sans accents ni espaces)."""
    if not text: return "exercice"
    text = unicodedata.normalize('NFD', str(text))
    text = text.encode('ascii', 'ignore').decode('ascii')
    text = re.sub(r'[^a-z0-9]+', '_', text.lower())
    return text.strip('_')

# Configuration des chemins
PROJECT_ROOT = Path(r"c:/Downloaded Web Sites/QUEST_HOME_PAGE_2025/cfctselec.github.io")
DOCS_DIR = PROJECT_ROOT / "docs"
INPUT_JSON = PROJECT_ROOT / "selection_merge.json"
INDEX_JSON = DOCS_DIR / "data" / "exercises.json"

# Nouveau répertoire d'exportation
EXPORT_ROOT = Path(r"C:\Downloaded Web Sites\QUEST_HOME_PAGE_2025\exos_combinated")
# Génération d'un nom de fichier unique avec timestamp
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
# On crée un sous-dossier spécifique pour ce lot afin de faciliter la création du ZIP
BATCH_DIR = EXPORT_ROOT / f"batch_{timestamp}"
OUTPUT_TEX = BATCH_DIR / f"combined_exercises_{timestamp}.tex"
OUTPUT_ZIP = EXPORT_ROOT / f"combined_exercises_{timestamp}.zip"

def extract_sections(content):
    """Sépare le préambule et le corps des questions de manière robuste."""
    lines = content.splitlines()
    preamble_lines = []
    found_doc = False
    body_lines = []
    
    for line in lines:
        # On cherche le premier \begin{document} non commenté
        if not found_doc and re.search(r'^\s*\\begin\{document\}', line, re.IGNORECASE):
            found_doc = True
            continue
        
        if not found_doc:
            preamble_lines.append(line)
        else:
            body_lines.append(line)
            
    preamble = "\n".join(preamble_lines)
    body = "\n".join(body_lines).strip()
    
    # Questions : tout ce qui est entre \begin{questions} et \end{questions}
    # Support des options d'environnement comme \begin{questions}[resume]
    questions_match = re.search(r'\\begin\{questions\}(?:\[.*?\])?(.*?)\\end\{questions\}', body, re.DOTALL | re.IGNORECASE)
    questions_body = questions_match.group(1).strip() if questions_match else ""
    
    return preamble, questions_body

def find_images(text):
    r"""Trouve les chemins d'images dans un texte LaTeX."""
    return re.findall(r'\\includegraphics(?:\[.*?\])?\{([^{}]+)\}', text)

def merge_tex():
    if not INPUT_JSON.exists():
        logging.error(f"❌ Fichier {INPUT_JSON.name} non trouvé à la racine.")
        print("Conseil : Sélectionnez des exercices dans l'index et cliquez sur 'JSON pour Fusion'.")
        return

    try:
        with open(INPUT_JSON, 'r', encoding='utf-8') as f:
            tex_relative_paths = json.load(f)
    except Exception as e:
        logging.error(f"❌ Erreur lors de la lecture du JSON : {e}")
        return

    # Chargement de l'index pour récupérer la liste des fichiers associés (images)
    exercise_index = {}
    if INDEX_JSON.exists():
        try:
            exercises_data = json.loads(INDEX_JSON.read_text(encoding='utf-8'))
            exercise_index = {ex['tex_url']: ex for ex in exercises_data}
        except Exception as e:
            logging.warning(f"⚠️ Impossible de charger l'index des exercices : {e}")

    if not tex_relative_paths:
        logging.warning("⚠️ La liste de sélection est vide.")
        return

    all_preambles = []
    all_questions = []

    logging.info(f"Analyse de {len(tex_relative_paths)} fichiers...")

    for rel_path in tex_relative_paths:
        full_path = DOCS_DIR / rel_path
        if not full_path.exists():
            logging.warning(f"  - Fichier introuvable : {full_path}")
            continue

        content = full_path.read_text(encoding='utf-8')
        preamble, questions = extract_sections(content)
        
        if preamble:
            # On nettoie le bloc YAML spécifique pour ne pas polluer le préambule
            clean_p = re.sub(r'^%\s*---\s*$.*?^%\s*---\s*$', '', preamble, flags=re.DOTALL | re.MULTILINE)
            all_preambles.append(clean_p.strip())
        
        # GESTION DES IMAGES : Collecte et Aplatissement des chemins
        # On utilise exercises.json comme MANIFESTE de build (Source de Vérité)
        posix_rel_path = Path(rel_path).as_posix()
        if posix_rel_path in exercise_index:
            ex_meta = exercise_index[posix_rel_path]
            manifest_imgs = ex_meta.get('images', [])
            
            # On utilise le titre slugifié comme nom de répertoire pour les images
            title = ex_meta.get('title', full_path.stem)
            ex_res_dirname = slugify(title)
            ex_res_dir = BATCH_DIR / ex_res_dirname

            if questions:
                tex_refs = find_images(questions)
                for img_filename in manifest_imgs:
                    source_img = full_path.parent / img_filename
                    
                    if source_img.exists():
                        # On ne crée le dossier que s'il y a physiquement des images à copier
                        ex_res_dir.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(source_img, ex_res_dir / img_filename)
                        logging.info(f"  📷 Image isolée : {ex_res_dirname}/{img_filename}")
                        
                        # RÉÉCRITURE DU CHEMIN LATEX
                        # On fait pointer \includegraphics vers le nouveau sous-répertoire
                        target_stem = Path(img_filename).stem.lower()
                        for ref in tex_refs:
                            if Path(ref).stem.lower() == target_stem:
                                pattern = fr'\{{\s*{re.escape(ref)}\s*\}}'
                                # Nouveau chemin : dossier_exercice/image.png
                                questions = re.sub(pattern, f'{{{ex_res_dirname}/{img_filename}}}', questions)
                    else:
                        logging.warning(f"  ⚠️ Manifeste : Image '{img_filename}' introuvable dans {full_path.parent}")
        
        # Sécurité : Vérification des références orphelines (non présentes dans le JSON)
        if questions:
            for ref in find_images(questions):
                if '/' not in ref and '\\' not in ref: # Si c'est un nom simple non traité
                    if not any(Path(img).stem.lower() == Path(ref).stem.lower() for img in exercise_index.get(posix_rel_path, [])):
                        logging.warning(f"  📎 Image '{ref}' citée dans le TeX mais absente du manifeste JSON.")
                    
        if questions:
            all_questions.append(f"\n% --- Source: {rel_path} ---\n{questions}\n")

    if not all_questions:
        logging.error("❌ Aucun contenu de type 'questions' n'a pu être extrait.")
        return

    # Choix du préambule le plus complet
    valid_preambles = [p for p in all_preambles if r'\documentclass' in p]
    if not valid_preambles:
        valid_preambles = all_preambles
        
    best_preamble = max(valid_preambles, key=lambda p: len(p.splitlines()))

    # --- SÉCURITÉ TIKZ / BABEL ---
    # Si babel french est présent, on force l'ajout de la librairie tikz 'babel'
    if 'french' in best_preamble.lower() and r'\usepackage{tikz}' in best_preamble:
        if r'\usetikzlibrary{' in best_preamble:
            best_preamble = best_preamble.replace(r'\usetikzlibrary{', r'\usetikzlibrary{babel, ')
        else:
            best_preamble += "\n\\usetikzlibrary{babel}"

    logging.info(f"✅ Préambule sélectionné ({len(best_preamble.splitlines())} lignes).")

    # Reconstruction du document
    new_content = []
    new_content.append(best_preamble)
    new_content.append("\n\\begin{document}")
    new_content.append(r"\section*{Recueil d'exercices combinés}")
    new_content.append("\\begin{questions}")
    new_content.append("\n".join(all_questions))
    new_content.append("\\end{questions}")
    new_content.append("\\end{document}")

    final_tex = "\n".join(new_content)
    
    try:
        BATCH_DIR.mkdir(parents=True, exist_ok=True)
        OUTPUT_TEX.write_text(final_tex, encoding='utf-8')

        # Création de l'archive ZIP contenant le TEX et ses images
        shutil.make_archive(
            str(OUTPUT_ZIP.with_suffix('')), 'zip', 
            root_dir=BATCH_DIR)
        
        logging.info(f"✨ Succès ! Fichier TEX : {OUTPUT_TEX.name}")
        logging.info(f"📦 Archive ZIP créée : {OUTPUT_ZIP.name}")
        
        print(f"\nLe dossier est prêt : {BATCH_DIR}")
        print(f"L'archive ZIP est prête : {OUTPUT_ZIP}")

    except Exception as e:
        logging.error(f"❌ Erreur lors de l'écriture du fichier : {e}")

if __name__ == "__main__":
    merge_tex()