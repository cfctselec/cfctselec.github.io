#!/bin/bash

# Ce script automatise l'initialisation de l'environnement,
# l'exécution du pipeline de traitement des exercices et le lancement d'un serveur local.

# --- Configuration ---
PYTHON_SCRIPT="scripts/process_exercises.py"
CONTRIB_DIR="contributions"
VENV_DIR=".venv"
REQUIREMENTS_FILE="requirements.txt"

# --- 1. Initialisation de l'environnement virtuel ---
echo "--- Étape 1: Initialisation de l'environnement virtuel ---"
if [ ! -d "$VENV_DIR" ]; then
    echo "Création de l'environnement virtuel '$VENV_DIR'..."
    python3 -m venv "$VENV_DIR"
else
    echo "Environnement virtuel '$VENV_DIR' déjà existant."
fi

# Activation de l'environnement virtuel
echo "Activation de l'environnement virtuel..."
if [ -f "$VENV_DIR/bin/activate" ]; then
    source "$VENV_DIR/bin/activate"
    echo "Environnement virtuel activé (Linux/macOS)."
elif [ -f "$VENV_DIR/Scripts/activate" ]; then # Pour Windows (Git Bash, WSL)
    source "$VENV_DIR/Scripts/activate"
    echo "Environnement virtuel activé (Windows)."
else
    echo "⚠️ Erreur: Impossible d'activer l'environnement virtuel. Veuillez l'activer manuellement."
    echo "   - Linux/macOS: source $VENV_DIR/bin/activate"
    echo "   - Windows (CMD/PowerShell): .$VENV_DIR\Scripts\Activate.ps1 ou .$VENV_DIR\Scripts\activate.bat"
    exit 1
fi

# Installation des dépendances
echo "Installation des dépendances depuis '$REQUIREMENTS_FILE'..."
pip install -r "$REQUIREMENTS_FILE"

# --- 2. Préparation du dossier de contributions ---
echo "--- Étape 2: Vérification du dossier '$CONTRIB_DIR' ---"
mkdir -p "$CONTRIB_DIR"
if [ -z "$(ls -A $CONTRIB_DIR 2>/dev/null)" ]; then
    echo "📁 Le dossier '$CONTRIB_DIR' est vide."
    echo "   Déposez-y vos fichiers d'exercices (ex: exo_001.tex, exo_001_donnee.pdf, exo_001_solution.pdf, exo_001.m)."
    echo "   Le script continuera, mais aucun exercice ne sera traité."
fi

# --- 3. Exécution du pipeline (Compilation + Indexation) ---
echo "--- Étape 3: Traitement des exercices (Compilation + Indexation) ---"
echo "   (L'enrichissement Gemini est désactivé pour un traitement plus rapide)"
export ENABLE_GEMINI=false
python "$PYTHON_SCRIPT"

# --- 4. Lancement du serveur local pour prévisualisation ---
echo "--- Étape 4: Lancement du serveur local pour prévisualisation ---"
# --- 5. Lancement du serveur local pour prévisualisation ---
echo "--- Étape 5: Lancement du serveur local ---"
echo "   Le site sera accessible via votre navigateur."
echo "   → Sur ce PC: http://localhost:8000"
echo "   → Sur mobile/autre appareil (même réseau): http://$(hostname -I 2>/dev/null | awk '{print $1}'):8000 (si l'IP est détectée)"
echo "   Appuyez sur Ctrl+C pour arrêter le serveur."
python -m http.server 8000 --directory docs

# --- Instructions supplémentaires ---
echo ""
echo "--- Instructions supplémentaires ---"
echo "Pour exécuter le pipeline AVEC Gemini (enrichissement automatique des métadonnées):"
echo "  1. Obtenez une clé API Gemini (https://ai.google.dev/gemini-api/docs/get-started/python)"
echo "  2. Configurez votre clé API (remplacez 'VOTRE_CLE_API' par votre clé réelle):"
echo "     - Linux/macOS: export GEMINI_API_KEY=\"VOTRE_CLE_API\""
echo "     - Windows (CMD): set GEMINI_API_KEY=\"VOTRE_CLE_API\""
echo "     - Windows (PowerShell): \$env:GEMINI_API_KEY=\"VOTRE_CLE_API\""
echo "  3. Relancez le script Python (après avoir activé l'environnement virtuel si ce n'est pas déjà fait):"
echo "     python $PYTHON_SCRIPT"
echo ""
echo "Pour désactiver l'environnement virtuel une fois terminé:"
echo "  deactivate"
echo ""
echo "Script terminé."