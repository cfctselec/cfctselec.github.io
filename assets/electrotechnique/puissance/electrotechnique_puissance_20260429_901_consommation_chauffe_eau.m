% Télécharger OCTAVE depuis https://wiki.octave.org/Using_Octave et l'installer
% Puis copier-coller le code dans OCTAVE

% Données
P = 2200;    % Puissance [W]
t = 3.5;     % Temps [h]

% Calcul
W_kwh = (P / 1000) * t;

% Affichage
printf("Puissance de l'appareil : %.1f [kW]\n", P/1000);
printf("Temps de fonctionnement : %.1f [h]\n", t);
printf("Énergie consommée : %.2f [kWh]\n", W_kwh);