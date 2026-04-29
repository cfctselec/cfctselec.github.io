% Télécharger OCTAVE depuis https://wiki.octave.org/Using_Octave et l'installer
% Puis copier-coller le code dans OCTAVE

% Données
m = 650;     % Masse [kg]
g = 9.81;    % Gravité [m/s^2]
h = 12;      % Hauteur [m]

% Calcul
Wp = m * g * h;

% Affichage
printf("Masse de la charge : %.0f [kg]\n", m);
printf("Hauteur de levage : %.0f [m]\n", h);
printf("Énergie potentielle (travail) : %.2f [J]\n", Wp);
printf("Soit : %.2f [kJ]\n", Wp / 1000);