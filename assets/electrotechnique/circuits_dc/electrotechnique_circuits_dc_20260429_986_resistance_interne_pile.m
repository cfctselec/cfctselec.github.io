% Télécharger OCTAVE depuis https://wiki.octave.org/Using_Octave et l'installer 
% Puis copier-coller le code dans OCTAVE

% Données du projet 
Em = 750;  % Éclairement requis [lux] 
longueur = 15;      % [m] 
largeur = 8;        % [m] 
eta = 0.6;          % Rendement global (facteur maintenance inclus) 
phi_L = 8500;       % Flux d'un luminaire [lm]

% Calcul de la surface A = longueur * largeur;
% Calcul du nombre théorique de luminaires 
n_theo = (Em * A) / (phi_L * eta);
% Arrondi à l'entier supérieur 
n_reel = ceil(n_theo);
% Affichage des résultats 
printf("Surface à éclairer : %.2f [m^2]\n", A); 
printf("Nombre théorique de luminaires : %.2f\n", n_theo); 
printf("Nombre de luminaires à installer : %d\n", n_reel); 
printf("Éclairement final estimé : %.2f [lux]\n", (n_reel * phi_L * eta) / A);