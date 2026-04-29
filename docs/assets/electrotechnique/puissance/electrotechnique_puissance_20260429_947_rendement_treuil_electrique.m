% Télécharger OCTAVE depuis https://wiki.octave.org/Using_Octave et l'installer
% Puis copier-coller le code dans OCTAVE

% Données
W_utile = 120000;    % Travail utile [J]
eta = 0.75;          % Rendement

% Calcul
W_abs = W_utile / eta;

% Affichage
printf("Travail utile requis : %.0f [J]\n", W_utile);
printf("Rendement de l'installation : %.2f\n", eta);
printf("Énergie absorbée au réseau : %.0f [J]\n", W_abs);
printf("Soit : %.2f [kJ]\n", W_abs / 1000);