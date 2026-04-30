#!/usr/bin/env python3
"""Pipeline complet : validation, extraction YAML, enrichissement Gemini, build statique."""
import yaml
import re, json, shutil, hashlib, os, sys, logging, unicodedata, subprocess
import time # Importation de 'time' pour les délais
from pathlib import Path
from collections import defaultdict

# ──────────────────────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────────────────────
CONTRIB_DIR = Path("contributions")
DOCS_DIR = Path("docs")
ASSETS_DIR = DOCS_DIR / "assets"
DATA_DIR = DOCS_DIR / "data"
CACHE_DIR = Path(".gemini_cache")
ENABLE_GEMINI = os.getenv("ENABLE_GEMINI", "true").lower() != "false"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# ──────────────────────────────────────────────────────────────
# GEMINI 2.5 FLASH
# ──────────────────────────────────────────────────────────────
def get_gemini_client():
    if not ENABLE_GEMINI or not GEMINI_API_KEY:
        return None, None
    try:
        from google import genai
        from google.genai import types
        return genai.Client(api_key=GEMINI_API_KEY), types
    except ImportError:
        logging.warning("⚠️ SDK google-genai non installé. Mode dégradé.")
        return None, None

def call_gemini(tex_content: str, existing: dict) -> dict:
    client, types = get_gemini_client()
    if not client:
        return {}
        
    # Cache basé sur hash du contenu
    cache_key = hashlib.sha256(tex_content.encode()).hexdigest()[:16]
    cache_file = CACHE_DIR / f"{cache_key}.json"
    if cache_file.exists():
        logging.info("♻️ Cache Gemini utilisé")
        return json.loads(cache_file.read_text())
        
    prompt = f"""Tu es un expert en pédagogie physique/électrotechnique/mécanique.
Analyse cet extrait LaTeX et retourne UNIQUEMENT un JSON valide respectant ce schéma :
{{
  "domain": "string",
  "subdomain": "string", 
  "title": "string",
  "tags": ["string"],
  "difficulty": 1-5,
  "audience": "student|teacher|both",
  "description": "string"
}}
Règles strictes :
1. Si un champ existe dans le YAML fourni, CONSERVE-LE.
2. Retourne UNIQUEMENT le JSON, sans markdown ni texte.
3. Utilise null si indéterminable.
4. Langue : français.

YAML existant : {json.dumps(existing, ensure_ascii=False)}
Extrait LaTeX (600 premiers caractères) : {tex_content[:600]}"""

    for attempt in range(3):
        try:
            config = types.GenerateContentConfig(temperature=0.1, response_mime_type="application/json") if types else {}
            resp = client.models.generate_content(model="gemini-1.5-flash-8b", contents=prompt, config=config)
            result = json.loads(resp.text)
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            cache_file.write_text(json.dumps(result, ensure_ascii=False, indent=2))
            logging.info("✅ Gemini enrichi")
            return result
        except Exception as e:
            if "429" in str(e):
                wait_time = (attempt + 1) * 5
                logging.warning(f"⚠️ Quota atteint (429). Attente de {wait_time}s...")
                time.sleep(wait_time)
                continue
            logging.warning(f"⚠️ Gemini échoué : {e}")
            break
            
    return {}

# ──────────────────────────────────────────────────────────────
# PARSING & VALIDATION
# ──────────────────────────────────────────────────────────────
def get_base_name(filename: str) -> str:
    """Extrait le radical du fichier en retirant les suffixes connus."""
    name = Path(filename).name
    # Retire .tex, .m, et les variantes PDF
    return re.sub(r'(_donnee\.pdf|_solution\.pdf|\.tex|\.m)$', '', name)

def parse_yaml(content: str) -> dict:
    match = re.search(r'%\s*---\s*\n(.*?)%\s*---', content, re.DOTALL)
    if not match: return {}
    yaml_text = "\n".join(re.sub(r'^\s*%\s?', '', l).rstrip() for l in match.group(1).split("\n"))
    # Correction proactive pour les unités physiques (ex: *kWh) qui cassent le YAML (alias)
    # On entoure de guillemets les mots commençant par '*' s'ils ne le sont pas déjà.
    yaml_text = re.sub(r'(?<=[:\[,\s])(\*\w+)(?=\s*[,\]\n]|$)', r'"\1"', yaml_text)
    try:
        data = yaml.safe_load(yaml_text) or {}
    except yaml.YAMLError as e:
        # Évite le crash complet du pipeline si un fichier LaTeX a un YAML malformé (ex: *kWh non quoté)
        logging.error(f"❌ Erreur de syntaxe YAML ignorée : {e}")
        return {}
    # Nettoyage des chaînes (supprime les guillemets résiduels du LaTeX)
    return {k: (v.strip('"\'') if isinstance(v, str) else v) for k, v in data.items()}

def extract_octave_code(tex_content: str) -> str:
    """Extrait le code Octave/Matlab d'un bloc verbatim ou lstlisting dans le LaTeX."""
    # Cherche des blocs verbatim ou lstlisting qui ressemblent à du code
    patterns = [r'\\begin\{verbatim\}(.*?)\\end\{verbatim\}', r'\\begin\{lstlisting\}(.*?)\\end\{lstlisting\}']
    for pattern in patterns:
        matches = re.finditer(pattern, tex_content, re.DOTALL)
        for match in matches:
            code = match.group(1)
            if "%" in code and ("=" in code or "printf" in code or "function" in code):
                lines = code.splitlines()
                content_lines = [l for l in lines if l.strip()]
                if not content_lines: return code.strip()
                indent = min(len(l) - len(l.lstrip()) for l in content_lines)
                return "\n".join(l[indent:] if len(l) >= indent else l for l in lines).strip()
    return None

def slugify(text: str) -> str:
    """Transforme une chaîne en version ASCII stricte sans accents ni caractères spéciaux."""
    if not text: return "divers"
    # Normalisation NFD : sépare les caractères de leurs accents
    text = unicodedata.normalize('NFD', str(text))
    # Encodage ASCII en ignorant les caractères non-convertibles (accents), puis retour en string
    text = text.encode('ascii', 'ignore').decode('ascii')
    # Mise en minuscule et remplacement des caractères spéciaux par _
    text = re.sub(r'[^a-z0-9]+', '_', text.lower())
    # Suppression des lettres isolées par fusion (ex: technique_d_eclairage -> technique_declairage)
    # On cherche un '_' suivi d'une lettre seule suivie d'un '_'
    text = re.sub(r'_([a-z0-9])_', r'_\1', text)
    # Nettoyage des underscores en début/fin
    return text.strip('_')

def count_questions(tex_content: str) -> int:
    r"""
    Compte le nombre d'unités de travail (questions ou parts) dans un document LaTeX exam.
    Si une question contient des parties (\part), on compte les parties.
    Sinon, on compte la question elle-même.
    """
    # Découpage du contenu par \question (on ignore le préambule avant la première question)
    questions = re.split(r'\\question\b(?:\[.*?\])?', tex_content)[1:]
    
    total_units = 0
    for q_block in questions:
        # On cherche les \part à l'intérieur de ce bloc de question
        parts = re.findall(r'\\part\b(?:\[.*?\])?', q_block)
        total_units += len(parts) if parts else 1
    return total_units

def compile_latex_if_needed(tex_path: Path):
    """Compile le PDF donnée et solution si le .tex est présent."""
    basename = tex_path.stem
    parent = tex_path.parent
    
    # Vérifier si pdflatex est disponible
    try:
        subprocess.run(['pdflatex', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        logging.error("❌ pdflatex n'est pas installé. Compilation impossible.")
        return

    def run_compilation(jobname, print_answers=False):
        content = tex_path.read_text(encoding="utf-8")
        # Toggle \printanswers
        if print_answers:
            content = content.replace(r'\noprintanswers', r'\printanswers')
            if r'\printanswers' not in content:
                content = "\\printanswers\n" + content
        else:
            content = content.replace(r'\printanswers', r'\noprintanswers')
        
        temp_tex = parent / f"temp_{jobname}.tex"
        temp_tex.write_text(content, encoding="utf-8")
        
        logging.info(f"   -> Compilation {jobname}...")
        for _ in range(2): # 2 passes pour les références/points
            subprocess.run(
                ['pdflatex', '-interaction=nonstopmode', f'-jobname={jobname}', temp_tex.name],
                cwd=str(parent), capture_output=True, text=True
            )
        temp_tex.unlink()
        # Nettoyage fichiers auxiliaires
        for ext in ['aux', 'log', 'out', 'toc']:
            p = parent / f"{jobname}.{ext}"
            if p.exists(): p.unlink()

    # Logique de "fraîcheur" (Timestamp comparison)
    tex_mtime = tex_path.stat().st_mtime
    
    def needs_compilation(pdf_name):
        pdf_path = parent / pdf_name
        if not pdf_path.exists(): return True
        return tex_mtime > pdf_path.stat().st_mtime

    if needs_compilation(f"{basename}_donnee.pdf"):
        run_compilation(f"{basename}_donnee", print_answers=False)
    else:
        logging.info(f"   ☕ {basename}_donnee.pdf est déjà à jour.")

    if needs_compilation(f"{basename}_solution.pdf"):
        run_compilation(f"{basename}_solution", print_answers=True)
    else:
        logging.info(f"   ☕ {basename}_solution.pdf est déjà à jour.")

def get_existing_structure():
    """Renvoie la liste des domaines et sous-domaines déjà présents dans assets."""
    if not ASSETS_DIR.exists():
        return [], {}
    domains = [d.name for d in ASSETS_DIR.iterdir() if d.is_dir()]
    structure = {}
    for d in domains:
        subs = [s.name for s in (ASSETS_DIR / d).iterdir() if s.is_dir()]
        if subs:
            structure[d] = subs
        else:
            structure[d] = []
    return domains, structure

def process_exercises():
    # S'assurer que le dossier existe sans arrêter le script
    CONTRIB_DIR.mkdir(parents=True, exist_ok=True)

    # --- Phase 1 : Identification, compilation et préparation des mouvements ---
    logging.info("🚀 Phase 1 : Identification et compilation des exercices dans 'contributions/'...")
    
    # Dictionary to hold exercise data, keyed by the base name of the .tex file
    exercises_to_process = {} # {base_name: {'tex_file': Path, 'related_files': [Path, ...], 'meta': {}, ...}}
    
    # First, find all .tex files, which are the primary indicators of an exercise
    tex_files_in_contrib = list(CONTRIB_DIR.glob("*.tex"))
    
    if not tex_files_in_contrib:
        logging.info("ℹ️ Aucun fichier .tex trouvé dans 'contributions/'.")
        # Log any other files that are just sitting there without a .tex
        unassociated_files = [f for f in CONTRIB_DIR.iterdir() if f.is_file()]
        if unassociated_files:
            logging.warning("⚠️ Des fichiers non .tex sont présents dans 'contributions/' mais aucun exercice n'a été détecté (pas de .tex).")
            for f in unassociated_files:
                logging.warning(f"   - Ignoré : {f.name}")

    planned_moves = []
    # On ne procède aux phases 1 et 2 que s'il y a des fichiers .tex
    if tex_files_in_contrib:
        # Process each .tex file
        for tex_file in tex_files_in_contrib:
            base_name = tex_file.stem # e.g., "electrotechnique_circuits_dc_20260429_420_pente_loi_ohm"
            
            # Compile the .tex file if needed
            try:
                compile_latex_if_needed(tex_file)
            except Exception as e:
                logging.error(f"❌ Erreur compilation sur {tex_file.name}: {e}")
                continue # Skip this exercise if compilation fails

            # Read content and parse YAML
            content = tex_file.read_text(encoding="utf-8")
            meta = parse_yaml(content)

            # Enrichissement Gemini si champs critiques manquants
            if ENABLE_GEMINI and (not meta.get("domain") or not meta.get("tags")):
                gemini = call_gemini(content, meta)
                for k, v in gemini.items():
                    if v and k not in meta:
                        meta[k] = v

            # Calculate destination path slugs
            prefix_domain = base_name.split('_')[0] if '_' in base_name else "divers"
            domain_val = meta.get("domain", prefix_domain)
            domain_slug = slugify(domain_val)
            sub_val = meta.get("subdomain", "").strip()
            subdomain_slug = slugify(sub_val) if sub_val else ""

            # Collect all files in CONTRIB_DIR that are related to this base_name
            related_files = [f for f in CONTRIB_DIR.iterdir() if f.is_file() and (f.stem == base_name or (f.name.startswith(f"{base_name}") and f.suffix in ['.pdf', '.log', '.aux', '.out', '.toc', '.m', '.png', '.jpg', '.jpeg']))]
            
            exercises_to_process[base_name] = {
                "tex_file": tex_file, "related_files": related_files, "meta": meta,
                "domain_slug": domain_slug, "subdomain_slug": subdomain_slug
            }

        # Log any files in CONTRIB_DIR that were not part of any identified exercise
        all_processed_files = set()
        for ex_data in exercises_to_process.values():
            for f in ex_data['related_files']:
                all_processed_files.add(f)
            
        unassociated_files = [f for f in CONTRIB_DIR.iterdir() if f.is_file() and f not in all_processed_files]
        for f in unassociated_files:
            logging.warning(f"⚠️ Fichier non associé à un exercice (.tex) et ignoré dans 'contributions/': {f.name}")

        ASSETS_DIR.mkdir(parents=True, exist_ok=True)
        logging.info(f"📦 Phase 2 : Analyse de {len(exercises_to_process)} exercices détectés...")
        
        # Convert exercises_to_process dict to a list for the validation phase
        planned_moves = []
        for base_name, ex_data in exercises_to_process.items():
            planned_moves.append({
                "base": base_name,
                "files": ex_data['related_files'],
                "domain": ex_data['domain_slug'],
                "subdomain": ex_data['subdomain_slug'],
                "meta": ex_data['meta'],
                "tex": ex_data['tex_file']
            })

        # Validation interactive des nouveaux répertoires
        existing_domains, existing_struct = get_existing_structure()
        known_domains = set(existing_domains)
        known_subdirs = set()  # Format: "domaine/sous_domaine"

        for move in planned_moves:
            # 1. Validation du DOMAINE
            dom = move["domain"]
            if dom not in known_domains and not (ASSETS_DIR / dom).exists():
                print(f"\n--- 🌐 NOUVEAU DOMAINE DÉTECTÉ ---")
                print(f"Exercice : {move['base']}")
            print(f"Domaine proposé : {dom}")
            if existing_domains:
                print(f"Domaines existants : {', '.join(sorted(existing_domains))}")
            
            ans = input(f"Le domaine est-il OK ? [Y]es / [r]ename / [s]kip : ").lower()
            if ans == 's':
                move["skip"] = True
                continue
            elif ans == 'r':
                new_dom = input(f"Entrez le nouveau nom de domaine : ").strip()
                if new_dom:
                    move["domain"] = slugify(new_dom)
                    dom = move["domain"]
                known_domains.add(dom)

            # 2. Validation du SOUS-DOMAINE (si défini)
            sub = move["subdomain"]
            if not sub:
                continue

            target_str = f"{move['domain']}/{sub}"
            # On vérifie si ce chemin complet est nouveau pour cette session ou sur le disque
            if target_str not in known_subdirs and not (ASSETS_DIR / move['domain'] / sub).exists():
                print(f"\n--- 🌿 NOUVEAU SOUS-DOMAINE DÉTECTÉ ---")
                print(f"Domaine : {move['domain']}")
                print(f"Sous-domaine proposé : {sub}")
                
                # Récupérer les sous-domaines existants pour le domaine (potentiellement renommé)
                existing_subs = existing_struct.get(move["domain"], [])
                if existing_subs:
                    print(f"Sous-domaines existants dans '{move['domain']}' : {', '.join(sorted(existing_subs))}")
                
                ans = input(f"Le sous-domaine est-il OK ? [Y]es / [r]ename / [s]kip : ").lower()
                if ans == 's':
                    move["skip"] = True
                    continue
                elif ans == 'r':
                    new_sub = input(f"Entrez le nouveau nom de sous-domaine : ").strip()
                    if new_sub:
                        move["subdomain"] = slugify(new_sub)
                        sub = move["subdomain"]
                        target_str = f"{move['domain']}/{sub}"
                
                known_subdirs.add(target_str)

    # Exécution des déplacements
    for move in planned_moves:
        if move.get("skip"): continue

        rel_dir = Path(move["domain"]) / move["subdomain"]
        ex_assets_abs = ASSETS_DIR / rel_dir
        ex_assets_abs.mkdir(parents=True, exist_ok=True)

        for f in move["files"]:
            dest_path = ex_assets_abs / f.name
            shutil.move(str(f), str(dest_path))

    # --- Phase 3 : Indexation de TOUS les assets ---
    logging.info("🔍 Phase 3 : Scan de tous les exercices dans assets pour l'index...")
    exercises = []
    for tex_path in ASSETS_DIR.rglob("*.tex"):
        base = get_base_name(tex_path.name)
        content = tex_path.read_text(encoding="utf-8")
        meta = parse_yaml(content)
        num_questions = count_questions(content)
        
        # URLs
        rel_folder = tex_path.parent.relative_to(DOCS_DIR)
        meta["domain"] = meta.get("domain", tex_path.parent.parent.name)
        meta.setdefault("title", base.replace("_", " ").title())
        meta.setdefault("subdomain", meta.get("subdomain", tex_path.parent.name))
        meta["id"] = slugify(meta.get("id", base))
        
        # Extraction de la date pour le tri/affichage (format YYYY-MM-DD)
        date_match = re.search(r'(\d{8})', meta["id"])
        if date_match:
            d_str = date_match.group(1)
            meta["date"] = f"{d_str[:4]}-{d_str[4:6]}-{d_str[6:8]}"
        else:
            meta["date"] = None

        if "time_solve" not in meta:
            meta["time_solve"] = int(meta.get("difficulty", 2)) * (max(1, num_questions) * 2)

        meta["tex_url"] = (rel_folder / tex_path.name).as_posix()
        
        # Fichiers compagnons
        for suffix, key in [("_donnee.pdf", "donnee_url"), ("_solution.pdf", "solution_url"), (".m", "octave_url")]:
            f_path = tex_path.parent / (base + suffix)
            if f_path.exists():
                meta[key] = (rel_folder / f_path.name).as_posix()
            elif key == "octave_url":
                # Extraction si .m absent
                code = extract_octave_code(content)
                if code:
                    f_path.write_text(code, encoding="utf-8")
                    meta[key] = (rel_folder / f_path.name).as_posix()
                    meta["has_octave"] = True

        # Texte de recherche
        # On inclut la version avec ET sans accents pour que la recherche soit tolérante
        search_raw = f"{meta['title']} {meta['domain']} {meta['subdomain']} {' '.join(meta.get('tags', []))}"
        search_parts = [
            search_raw,
            slugify(search_raw).replace('_', ' ') # Version sans accent pour la recherche "floue"
        ]
        meta["search_text"] = " ".join(filter(None, search_parts)).lower()

        exercises.append(meta)

    # Génération index
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(DATA_DIR / "exercises.json", "w", encoding="utf-8") as f:
        json.dump(exercises, f, ensure_ascii=False, indent=2)
    logging.info(f"✅ {len(exercises)} exercices indexés → {DATA_DIR / 'exercises.json'}")

if __name__ == "__main__":
    process_exercises()