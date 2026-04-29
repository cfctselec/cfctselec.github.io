#!/usr/bin/env python3
import json
import re, sys, shutil
import logging
from pathlib import Path

# Configuration
PROJECT_ROOT = Path(__file__).resolve().parent.parent
INDEX_FILE = PROJECT_ROOT / "docs" / "data" / "exercises.json"
CONTRIB_DIR = PROJECT_ROOT / "contributions"
DOCS_DIR = PROJECT_ROOT / "docs"

# --- CONFIGURATION DE LA TAXONOMIE ---
# Modifiez ce dictionnaire pour corriger massivement les tags ou les sous-domaines
REMAP_CONFIG = {
    "tags": {
        "loi_ohm": "Loi d'Ohm",
        "loi d'ohm": "Loi d'Ohm",
        "loi dohm": "Loi d'Ohm",
        "triphase": "Triphasé",
        "puissance_active": "Puissance active"
    },
    "subdomains": {
        "circuits": "Circuits DC",
        "regime_triphase": "Régime triphasé"
    }
}

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def normalize_value(val, category):
    """Applique le mapping de correction ou nettoie la valeur."""
    if not val: return ""
    low_val = val.lower().strip()
    # 1. Vérification dans le dictionnaire de mapping
    if low_val in REMAP_CONFIG.get(category, {}):
        return REMAP_CONFIG[category][low_val]
    # 2. Fallback : si c'est un tag snake_case, on le rend lisible
    return val.replace('_', ' ').strip()

def update_tex_metadata(tex_path, updates):
    """Met à jour chirurgicalement les lignes tags et subdomain dans le fichier .tex."""
    if not tex_path.exists():
        logging.warning(f"⚠️ Fichier introuvable : {tex_path}")
        return False

    content = tex_path.read_text(encoding="utf-8")

    # Cible uniquement le bloc YAML % ---
    yaml_match = re.search(r'(%\s*---\s*\n)(.*?)(%\s*---)', content, re.DOTALL)
    if not yaml_match: return False

    header, yaml_part, footer = yaml_match.groups()
    lines = yaml_part.splitlines()
    updated = False
    new_lines = []

    for line in lines:
        found_key = False
        for key in updates.keys():
            if re.match(fr'^\s*%\s*{key}\s*:', line):
                new_val = updates[key]
                if isinstance(new_val, list):
                    new_val_str = json.dumps(new_val, ensure_ascii=False)
                else:
                    new_val_str = f'"{new_val}"'
                
                new_line = re.sub(fr'^(\s*%\s*)({key})(\s*:\s*)(.*)$', fr'\1\2\3{new_val_str}', line)
                if new_line != line:
                    updated = True
                new_lines.append(new_line)
                found_key = True
                break
        if not found_key:
            new_lines.append(line)

    if updated:
        new_content = content[:yaml_match.start()] + header + "\n".join(new_lines) + "\n" + footer + content[yaml_match.end():]
        tex_path.write_text(new_content, encoding="utf-8")
        return True
    return False

def main():
    if not INDEX_FILE.exists():
        logging.error(f"❌ L'index {INDEX_FILE} n'existe pas. Lancez process_exercises.py d'abord.")
        return

    exercises = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    count = 0
    apply_all = False

    logging.info(f"🔍 Analyse de {len(exercises)} exercices pour normalisation des tags...")

    for ex in exercises:
        if "tex_url" not in ex or "tags" not in ex: continue

        # Chemin absolu vers le .tex (tex_url est relatif à docs/)
        tex_path = DOCS_DIR / ex["tex_url"]
        base_name = tex_path.stem
        
        # Préparation des mises à jour (Automatique via REMAP_CONFIG)
        old_tags = ex.get("tags", [])
        new_tags = sorted(list(set(normalize_value(t, "tags") for t in old_tags)))
        
        old_sub = ex.get("subdomain", "")
        new_sub = normalize_value(old_sub, "subdomains")

        updates = {}
        if old_tags != new_tags: updates["tags"] = new_tags
        if old_sub != new_sub: updates["subdomain"] = new_sub

        if updates:
            if not apply_all:
                print(f"\n--- 📝 MODIFICATION : {ex['title']} ---")
                print(f"  Fichier : {tex_path.name}")
                for k, v in updates.items():
                    print(f"  {k:10}: {ex.get(k)} -> {v}")
                
                ans = input("\nAppliquer et renvoyer en 'contributions' ? [y]es / [n]o / [a]ll / [q]uit / [e]dit : ").lower()
                if ans == 'q': sys.exit(0)
                if ans == 'n': continue
                if ans == 'a': apply_all = True
                if ans == 'e':
                    # Saisie manuelle à la main
                    custom_sub = input(f"  Nouveau sous-domaine [{new_sub}] : ").strip()
                    if custom_sub: new_sub = custom_sub
                    custom_tags = input(f"  Nouveaux tags (séparés par ,) [{', '.join(new_tags)}] : ").strip()
                    if custom_tags: new_tags = sorted(list(set(t.strip() for t in custom_tags.split(','))))
                    updates = {"tags": new_tags, "subdomain": new_sub}

            # 1. Mise à jour chirurgicale du fichier .tex
            if update_tex_metadata(tex_path, updates):
                # 2. Déplacement vers 'contributions' pour re-traitement par le pipeline principal
                files_to_move = list(tex_path.parent.glob(f"{base_name}*"))
                CONTRIB_DIR.mkdir(parents=True, exist_ok=True)
                for f in files_to_move:
                    shutil.move(str(f), str(CONTRIB_DIR / f.name))
                
                logging.info(f"✅ Mis à jour et déplacé vers contributions/ : {base_name}")
                count += 1

    logging.info(f"\n✨ Terminé. {count} fichiers mis à jour.")
    logging.info("💡 Relancez process_exercises.py pour recompiler les PDF et mettre à jour l'index.")

if __name__ == "__main__":
    main()