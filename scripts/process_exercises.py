#!/usr/bin/env python3
"""Pipeline complet : validation, extraction YAML, enrichissement Gemini, build statique."""
import yaml
import re, json, shutil, hashlib, os, sys, logging, unicodedata, subprocess, datetime
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
PREAMBULE_PATH = Path(__file__).resolve().parent / "preambule.tex"

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

def update_tex_metadata(tex_path: Path, updates: dict):
    """Met à jour chirurgicalement le YAML dans le fichier .tex."""
    if not tex_path.exists(): return
    content = tex_path.read_text(encoding="utf-8")
    match = re.search(r'(%\s*---\s*\n)(.*?)(%\s*---)', content, re.DOTALL)
    if not match:
        # Si pas de bloc YAML, on n'en crée pas ici pour ne pas corrompre le LaTeX
        return

    header, yaml_part, footer = match.groups()
    lines = yaml_part.splitlines()
    new_lines = []
    keys_found = set()
    
    for line in lines:
        new_line = line
        for key, val in updates.items():
            if re.match(fr'^\s*%\s*{key}\s*:', line):
                val_str = json.dumps(val, ensure_ascii=False) if isinstance(val, (list, dict)) else (f'"{val}"' if isinstance(val, str) else str(val))
                new_line = re.sub(fr'^(\s*%\s*)({key})(\s*:\s*)(.*)$', fr'\1\2\3{val_str}', line)
                keys_found.add(key)
                break
        new_lines.append(new_line)

    # Ajouter les clés manquantes à la fin du bloc YAML
    updated = len(keys_found) > 0
    for key, val in updates.items():
        if key not in keys_found:
            val_str = json.dumps(val, ensure_ascii=False) if isinstance(val, (list, dict)) else (f'"{val}"' if isinstance(val, str) else str(val))
            new_lines.append(f"% {key} : {val_str}")
            updated = True
    
    if updated:
        new_content = content[:match.start()] + header + "\n".join(new_lines) + "\n" + footer + content[match.end():]
        tex_path.write_text(new_content, encoding="utf-8")

def format_for_display(text: str) -> str:
    """Assure que le texte commence par une majuscule (gère les accents) pour l'affichage HTML."""
    if not text: return ""
    return text[0].upper() + text[1:]

def find_referenced_images(tex_content: str) -> list:
    r"""Recherche les noms de fichiers images dans les commandes \includegraphics."""
    # Capture le contenu entre les accolades de \includegraphics{...}
    return re.findall(r'\\includegraphics(?:\[.*?\])?\{([^{}]+)\}', tex_content)

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

# Helper to extract questions block from user's input
def extract_body_content(content: str) -> str:
    """Extrait le corps de l'exercice en retirant le bloc YAML."""
    # On cherche la fin du bloc YAML
    match_yaml = re.search(r'%\s*---\s*\n.*?%\s*---', content, re.DOTALL)
    if match_yaml:
        body = content[match_yaml.end():].strip()
    else:
        body = content.strip()
    
    # Si l'utilisateur a déjà mis \begin{questions}, on extrait l'intérieur, sinon on prend tout
    match_q = re.search(r'\\begin\{questions\}(.*?)\\end\{questions\}', body, re.DOTALL)
    if match_q:
        return match_q.group(1).strip()
    return body

def extract_yaml_block_from_input(content: str) -> str:
    match = re.search(r'(%\s*---\s*\n.*?%\s*---)', content, re.DOTALL)
    return match.group(1).strip() if match else ""

def prompt_with_default(prompt_text, default_value):
    """Pose une question à l'utilisateur avec une valeur par défaut."""
    try:
        res = input(f"{prompt_text} [{default_value}] : ").strip()
        return res if res else default_value
    except EOFError:
        return default_value

def create_new_exercise_from_input():
    print("\n--- 📝 MODE CRÉATION D'EXERCICE ---")
    print("1. Collez votre contenu LaTeX (YAML + Corps).")
    print("2. Validez avec Ctrl+Z puis ENTREE (Windows) ou Ctrl+D (Unix).")
    print("-" * 40)
    
    user_latex_content = sys.stdin.read()
    
    # Réouverture du terminal pour les questions interactives après le pipe/EOF
    sys.stdin = open('CON' if os.name == 'nt' else '/dev/tty')

    if not user_latex_content.strip():
        logging.info("Aucun contenu fourni. Annulation de la création d'exercice.")
        return

    # 1. Parse user's input
    user_yaml_block = extract_yaml_block_from_input(user_latex_content)
    user_meta = parse_yaml(user_latex_content)
    user_questions_body = extract_body_content(user_latex_content)

    # Extraction du nom de fichier
    filename_from_meta = user_meta.get("filename")
    if isinstance(filename_from_meta, list):
        filename_from_meta = filename_from_meta[0]
    
    if not filename_from_meta:
        logging.error("❌ 'filename' manquant dans le bloc YAML. Impossible de créer l'exercice.")
        return
    
    if not filename_from_meta.endswith(".tex"):
        filename_from_meta += ".tex"

    output_tex_path = CONTRIB_DIR / filename_from_meta

    # 2. Load preambule.tex content
    if not PREAMBULE_PATH.exists():
        logging.error(f"❌ Le fichier de préambule {PREAMBULE_PATH} est introuvable.")
        return
    template = PREAMBULE_PATH.read_text(encoding="utf-8")

    # 3. Modify preambule.tex content
    print("\n--- 🛠️ CONFIGURATION DES MÉTADONNÉES ---")
    print("Appuyez sur ENTREE pour conserver la valeur par défaut.\n")

    nomauteur_val = prompt_with_default("E-mail de l'auteur", 
                                        user_meta.get("author", "bdminasmorgul@protonmail.com"))
    dateTe_val = prompt_with_default("Date de l'épreuve", 
                                     user_meta.get("dateTe", datetime.date.today().strftime("%d.%m.%Y")))
    brancheTe_val = prompt_with_default("Branche (ex: TS, DT)", 
                                        user_meta.get("brancheTe", "TS"))
    section_title_val = prompt_with_default("Titre de la section", 
                                            user_meta.get("section_title", "Préparation TS PQ CFC ELMO,IELE,PELE"))

    # Remplacement des variables LaTeX
    # On utilise des lambdas pour éviter l'interprétation des backslashes dans les chaînes de remplacement
    template = re.sub(r'(\\newcommand\\nomauteur\{)(.*?)(\})', lambda m: m.group(1) + nomauteur_val + m.group(3), template)
    template = re.sub(r'(\\newcommand\\dateTe\{)(.*?)(\})', lambda m: m.group(1) + dateTe_val + m.group(3), template)
    template = re.sub(r'(\\newcommand\\brancheTe\{)(.*?)(\})', lambda m: m.group(1) + brancheTe_val + m.group(3), template)
    
    # Remplacement de la section
    template = re.sub(r'(\\section\*\{)(.*?)(\})', lambda m: m.group(1) + section_title_val + m.group(3), template)

    # Insertion du corps dans l'environnement questions
    # On cherche le bloc \begin{questions} ... \end{questions} du template pour le remplir
    if r"\begin{questions}" in template:
        final_tex = re.sub(r'(\\begin\{questions\})(.*?)(\\end\{questions\})', 
                           lambda m: m.group(1) + '\n' + user_questions_body + '\n' + m.group(3), 
                           template, flags=re.DOTALL)
    else:
        # Sécurité au cas où le template n'a pas le bloc
        final_tex = template.replace(r"\end{document}", r"\begin{questions}" + "\n" + user_questions_body + "\n" + r"\end{questions}" + "\n" + r"\end{document}")
    
    # Reconstruction finale avec le YAML original au sommet
    final_output = (user_yaml_block if user_yaml_block else "% --- \n% filename : " + filename_from_meta + "\n% ---") + "\n" + final_tex

    try:
        output_tex_path.write_text(final_output, encoding="utf-8")
        logging.info(f"✅ Fichier créé : {output_tex_path}")
    except Exception as e:
        logging.error(f"❌ Erreur lors de l'écriture du fichier {output_tex_path}: {e}")

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

            # Identification des fichiers liés (par nom de base)
            related_files = [f for f in CONTRIB_DIR.iterdir() if f.is_file() and (f.stem == base_name or f.name.startswith(f"{base_name}"))]
            
            # Identification des images explicitement nommées dans le code LaTeX (Smart Detection)
            img_names = find_referenced_images(content)
            for img_name in img_names:
                # On teste le chemin tel quel, puis avec des extensions courantes si besoin
                candidates = [img_name]
                if not Path(img_name).suffix:
                    candidates += [f"{img_name}{ext}" for ext in ['.png', '.jpg', '.jpeg', '.pdf', '.eps']]
                
                for candidate in candidates:
                    img_path = CONTRIB_DIR / candidate
                    if img_path.exists() and img_path not in related_files:
                        related_files.append(img_path)
                        break # On prend la première correspondance trouvée
            
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
        
        # Session-wide maps to simplify repeated renames/skips
        domain_decisions = {} # orig_slug -> {'action': 'keep'|'rename'|'skip', 'slug': str, 'display': str}
        sub_decisions = {}    # (dom_slug, orig_sub_slug) -> {'action': 'keep'|'rename'|'skip', 'slug': str, 'display': str}

        for move in planned_moves:
            orig_dom_slug = move["domain"]
            
            # 1. Validation du DOMAINE
            if orig_dom_slug in domain_decisions:
                decision = domain_decisions[orig_dom_slug]
            else:
                dom = move["domain"]
                if dom not in known_domains and not (ASSETS_DIR / dom).exists() and dom != "divers":
                    print(f"\n--- 🌐 NOUVEAU DOMAINE ---")
                    print(f"Dossier suggéré : {dom}")
                    if existing_domains:
                        print(f"Existants : {', '.join(sorted(existing_domains))}")
                    
                    ans = input(f"Domaine '{dom}' OK ? [Y]es / [r]ename / [s]kip : ").lower()
                    if ans == 's': decision = {'action': 'skip'}
                    elif ans == 'r':
                        new_dom = input(f"Nouveau nom : ").strip()
                        if new_dom:
                            new_slug = slugify(new_dom)
                            decision = {'action': 'rename', 'slug': new_slug, 'display': new_dom}
                            known_domains.add(new_slug)
                        else: decision = {'action': 'keep', 'slug': dom}
                    else: decision = {'action': 'keep', 'slug': dom}
                else: decision = {'action': 'keep', 'slug': dom}
                domain_decisions[orig_dom_slug] = decision

            if decision['action'] == 'skip':
                move["skip"] = True
                continue
            
            move["domain"] = decision['slug']
            if decision['action'] == 'rename':
                update_tex_metadata(move["tex"], {"domain": decision['display']})

            # 2. Validation du SOUS-DOMAINE (si défini)
            orig_sub_slug = move["subdomain"]
            if not orig_sub_slug: continue

            sub_key = (move["domain"], orig_sub_slug)
            if sub_key in sub_decisions:
                s_decision = sub_decisions[sub_key]
            else:
                sub = move["subdomain"]
                if not (ASSETS_DIR / move['domain'] / sub).exists():
                    print(f"\n--- 🌿 NOUVEAU SOUS-DOMAINE ---\nDomaine : {move['domain']} | Sous-domaine : {sub}")
                    existing_subs = existing_struct.get(move["domain"], [])
                    if existing_subs:
                        print(f"Existants : {', '.join(sorted(existing_subs))}")
                    
                    ans = input(f"Sous-domaine '{sub}' OK ? [Y]es / [r]ename / [s]kip : ").lower()
                    if ans == 's': s_decision = {'action': 'skip'}
                    elif ans == 'r':
                        new_sub = input(f"Nouveau nom : ").strip()
                        s_decision = {'action': 'rename', 'slug': slugify(new_sub), 'display': new_sub} if new_sub else {'action': 'keep', 'slug': sub}
                    else: s_decision = {'action': 'keep', 'slug': sub}
                else: s_decision = {'action': 'keep', 'slug': sub}
                sub_decisions[sub_key] = s_decision

            if s_decision['action'] == 'skip':
                move["skip"] = True
                continue
            
            move["subdomain"] = s_decision['slug']
            if s_decision['action'] == 'rename':
                update_tex_metadata(move["tex"], {"subdomain": s_decision['display']})

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
        # Le domaine est forcé en TOUTES MAJUSCULES (avec accents)
        meta["domain"] = str(meta.get("domain", tex_path.parent.parent.name)).upper()
        meta.setdefault("title", base.replace("_", " ").title())
        # Le sous-domaine garde la majuscule initiale (via format_for_display)
        meta["subdomain"] = format_for_display(meta.get("subdomain", tex_path.parent.name))
        meta["id"] = slugify(meta.get("id", base))
        
        # Utilisation du timestamp de création (Windows: st_ctime) pour la date originale
        ctime = tex_path.stat().st_ctime
        meta["date"] = datetime.datetime.fromtimestamp(ctime).strftime('%Y-%m-%dT%H:%M:%S')

        if "time_solve" not in meta:
            meta["time_solve"] = int(meta.get("difficulty", 2)) * (max(1, num_questions) * 2)

        meta["tex_url"] = (rel_folder / tex_path.name).as_posix()
        
        # Fichiers compagnons
        # Uniquement ceux référencés dans le LaTeX pour garantir une association exacte
        meta["images"] = []
        referenced_imgs = find_referenced_images(content)
        for img_ref in referenced_imgs:
            # On extrait le nom de fichier seul (le pipeline aplatit les structures)
            img_name_only = Path(img_ref).name
            # On vérifie l'existence physique pour confirmer l'association
            candidates = [img_name_only]
            if not Path(img_name_only).suffix:
                candidates += [f"{img_name_only}{ext}" for ext in ['.png', '.jpg', '.jpeg', '.pdf', '.eps', '.PNG', '.JPG']]
            
            for cand in candidates:
                if (tex_path.parent / cand).exists():
                    meta["images"].append(Path(cand).name)
                    break
        meta["images"] = sorted(list(set(meta["images"]))) # Déduplication et tri

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

    # Tri des exercices par date de création (du plus ancien au plus récent)
    # Cela permet à la colonne "N°" dans l'interface de suivre l'ordre chronologique réel
    exercises.sort(key=lambda x: x.get("date", ""))

    # Génération index
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(DATA_DIR / "exercises.json", "w", encoding="utf-8") as f:
        json.dump(exercises, f, ensure_ascii=False, indent=2)
    logging.info(f"✅ {len(exercises)} exercices indexés → {DATA_DIR / 'exercises.json'}")

if __name__ == "__main__":
    print("\n--- Menu principal ---")
    print("1. Traiter les exercices existants dans contribution (compilation, indexation)")
    print("2. Créer un nouvel exercice à partir d'un copier-coller LaTeX")
    print("3. Quitter")
    
    choice = input("Votre choix : ").strip()

    if choice == '1':
        process_exercises()
    elif choice == '2':
        create_new_exercise_from_input()
    elif choice == '3':
        logging.info("Exiting.")
        sys.exit(0)
    else:
        logging.warning("Choix invalide.")