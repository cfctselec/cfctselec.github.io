#!/usr/bin/env python3
import os, re, json, logging, yaml, time
from pathlib import Path
from google import genai
from google.genai import types

# Chargement automatique des variables d'environnement depuis le fichier .env à la racine
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / '.env')
except ImportError:
    pass

# Configuration
CONTRIB_DIR = Path("contributions")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def get_gemini_client():
    if not GEMINI_API_KEY:
        raise ValueError("La variable d'environnement GEMINI_API_KEY est manquante.")
    return genai.Client(api_key=GEMINI_API_KEY)

def parse_yaml_metadata(content: str) -> dict:
    match = re.search(r'%\s*---\s*\n(.*?)%\s*---', content, re.DOTALL)
    if not match: return {}
    yaml_text = "\n".join(re.sub(r'^\s*%\s?', '', l).rstrip() for l in match.group(1).split("\n"))
    # Hack pour les alias YAML comme *kWh
    yaml_text = re.sub(r'(?<=[:\[,\s])(\*\w+)(?=\s*[,\]\n]|$)', r'"\1"', yaml_text)
    try:
        return yaml.safe_load(yaml_text) or {}
    except:
        return {}

def update_tex_file(tex_path: Path, updates: dict):
    """Met à jour chirurgicalement le YAML pour préserver la structure originale."""
    content = tex_path.read_text(encoding="utf-8")
    
    def replace_val(match):
        prefix, key, sep, old_val = match.groups()
        if key in updates:
            val = updates[key]
            if isinstance(val, (list, dict)):
                val_str = json.dumps(val, ensure_ascii=False)
            else:
                val_str = f'"{val}"' if isinstance(val, str) else str(val)
            return f"{prefix}{key}{sep}{val_str}"
        return match.group(0)

    # On cible uniquement le bloc YAML entre les marqueurs % ---
    match = re.search(r'(%\s*---\s*\n)(.*?)(%\s*---)', content, re.DOTALL)
    if not match: return

    header, yaml_part, footer = match.groups()
    updated_lines = []
    for line in yaml_part.splitlines():
        # On remplace uniquement les lignes de type "% clé : valeur"
        new_line = re.sub(r'^(\s*%\s*)([\w_]+)(\s*:\s*)(.*)$', replace_val, line)
        updated_lines.append(new_line)

    new_content = content[:match.start()] + header + "\n".join(updated_lines) + "\n" + footer + content[match.end():]
    tex_path.write_text(new_content, encoding="utf-8")

def ask_gemini_for_accents(client, tex_content, current_meta):
    prompt = f"""Tu es un expert en normalisation de métadonnées pour des exercices d'électricité.
Analyse ce bloc YAML et le début du code LaTeX. Réécris UNIQUEMENT les champs 'title', 'domain', 'subdomain' et 'tags'.

Règles strictes :
1. title : Utilise le français correct avec accents, espaces au lieu des underscores.
2. domain : Avec accents (ex: "Électrotechnique", "Électronique").
3. subdomain : Avec accents (ex: "Circuits AC", "Régime triphasé").
4. tags : Liste de mots en minuscules MAIS avec les accents corrects (ex: ["impédance", "triphasé"]).
5. Ne change PAS les champs techniques comme 'id' ou 'filename'.
6. Retourne UNIQUEMENT un JSON valide.

YAML actuel : {json.dumps(current_meta, ensure_ascii=False)}
Contenu LaTeX : {tex_content[:500]}
"""
    for attempt in range(3):
        try:
            config = types.GenerateContentConfig(temperature=0.1, response_mime_type="application/json")
            resp = client.models.generate_content(model="gemini-3.1-flash-lite-preview", contents=prompt, config=config)
            return json.loads(resp.text)
        except Exception as e:
            if "429" in str(e):
                wait_time = (attempt + 1) * 10
                logging.warning(f"⚠️ Quota atteint (429). Nouvelle tentative dans {wait_time}s...")
                time.sleep(wait_time)
                continue
            logging.error(f"Erreur Gemini : {e}")
            break
    return None

def main():
    client = get_gemini_client()
    tex_files = list(CONTRIB_DIR.glob("*.tex"))
    logging.info(f"Début de la ré-accentuation de {len(tex_files)} fichiers...")
    apply_all = False

    for tex_path in tex_files:
        logging.info(f"Traitement de {tex_path.name}...")
        content = tex_path.read_text(encoding="utf-8")
        current_meta = parse_yaml_metadata(content)
        
        if not current_meta:
            continue

        improved_meta = ask_gemini_for_accents(client, content, current_meta)
        
        if improved_meta:
            # Vérifier s'il y a un réel changement par rapport à l'existant
            has_changes = False
            for k in ['title', 'domain', 'subdomain', 'tags']:
                if k in improved_meta and str(improved_meta[k]) != str(current_meta.get(k)):
                    has_changes = True
                    break
            
            if not has_changes:
                logging.info(f"   ✨ Déjà correct (accents/formatage OK)")
                continue

            if not apply_all:
                print(f"\n--- 📝 Propositions pour {tex_path.name} ---")
                for k, v in improved_meta.items():
                    old = current_meta.get(k)
                    if str(old) != str(v):
                        print(f"  {k:10}: {old} -> {v}")
                
                ans = input("\nAppliquer ces modifications ? [y]es / [n]o / [a]ll / [q]uit : ").lower()
                if ans == 'q': break
                if ans == 'n': continue
                if ans == 'a': apply_all = True

            # Mise à jour chirurgicale
            update_tex_file(tex_path, improved_meta)
            logging.info(f"✅ Mis à jour : {tex_path.name}")
            
            # Petite pause pour respecter le quota RPM
            time.sleep(2)

if __name__ == "__main__":
    main()