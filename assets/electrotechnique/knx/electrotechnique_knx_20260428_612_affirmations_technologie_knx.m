% Télécharger OCTAVE depuis https://wiki.octave.org/Using_Octave et l'installer 
% Puis copier-coller le code dans OCTAVE

% Parametres de conception KNX 
U_bus_nom = 29;              % Tension nominale [V] L_max_alim_dev = 350;
% Distance max alim-appareil [m] L_max_dev_dev = 700;         

% Distance max appareil-appareil [m] L_tot_ligne = 1000;          
% Longueur totale de cable par ligne [m]
% Verification des affirmations printf("--- Analyse de la technologie KNX ---\n"); 
printf("1. Tension nominale du bus : %.0f [V] DC\n", U_bus_nom); 
printf("2. Topologie autorisee : Bus, Etoile, Arbre (Boucle interdite).\n"); 
printf("3. Adresse physique X.Y.0 : Coupleur de ligne (Z.L.0)\n"); 
printf("4. Distance maximale entre 2 participants : %.0f [m]\n", L_max_dev_dev); 
printf("5. Distance maximale Alimentation-Participant : %.0f [m]\n", L_max_alim_dev);