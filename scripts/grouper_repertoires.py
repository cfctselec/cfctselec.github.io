import os
import re
import shutil

def extraire_annee(nom, chemin_complet):
    """Cherche une année (19xx ou 20xx) dans le nom ou dans l'arborescence parente."""
    # 1. Test dans le nom du dossier
    match = re.search(r'(19|20)\d{2}', nom)
    if match:
        return match.group(0)
    # 2. Test dans le chemin complet (dossiers parents)
    match = re.search(r'(19|20)\d{2}', chemin_complet)
    return match.group(0) if match else "Inconnue"

def grouper_par_tp_et_annee(racine, cible="TP_Regroupes"):
    racine = os.path.abspath(racine)
    chemin_cible = os.path.join(racine, cible)
    
    prefixes_valides = ['tp11', 'tp12', 'tp13', 'tp21', 'tp24', 'tp25', 'tp31']
    print(f"--- Début du regroupement dans : {chemin_cible} ---")
    
    # Parcours en profondeur pour trouver tous les dossiers
    for chemin_racine, dossiers, _ in os.walk(racine):
        if chemin_cible in chemin_racine:
            continue
            
        for dossier in dossiers:
            d_lower = dossier.lower()
            # On identifie si le dossier commence par l'un des préfixes cibles
            match_prefix = next((p for p in prefixes_valides if d_lower.startswith(p)), None)
            
            if match_prefix:
                chemin_src = os.path.join(chemin_racine, dossier)
                annee = extraire_annee(dossier, chemin_racine)
                
                # Nom du répertoire de regroupement (ex: tp11_2024)
                nom_groupe = f"{match_prefix}_{annee}"
                dir_dest_groupe = os.path.join(chemin_cible, nom_groupe)
                os.makedirs(dir_dest_groupe, exist_ok=True)
                
                # Chemin de destination final
                dest_final = os.path.join(dir_dest_groupe, dossier)
                
                # Si le nom existe déjà, on ajoute le nom du parent pour différencier
                if os.path.exists(dest_final):
                    parent_name = os.path.basename(chemin_racine)
                    dest_final = os.path.join(dir_dest_groupe, f"{dossier}_{parent_name}")

                try:
                    print(f"Copie : {dossier} (Année: {annee}) -> {nom_groupe}")
                    shutil.copytree(chemin_src, dest_final, dirs_exist_ok=True)
                except Exception as e:
                    print(f"Erreur sur {dossier} : {e}")
    
    print(f"\nTerminé ! Tous les dossiers ont été regroupés dans : {chemin_cible}")

if __name__ == "__main__":
    saisie = input("Entrez le chemin du dossier à scanner [Défaut: .] : ").strip()
    racine = saisie if saisie else "."
    
    if os.path.isdir(racine):
        grouper_par_tp_et_annee(racine)
    else:
        print(f"Erreur : Le chemin '{racine}' n'est pas un dossier valide.")