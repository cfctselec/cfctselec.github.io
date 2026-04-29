% Télécharger OCTAVE depuis https://wiki.octave.org/Using_Octave et l'installer
% Puis copier-coller le code dans OCTAVE

% Données
m = 2.5;      % Masse [kg]
c = 4186;     % Capacité thermique massique [J/kgK]
T1 = 15;      % Temp initiale [°C]
T2 = 85;      % Temp finale [°C]

% Calcul
delta_T = T2 - T1;
Q = m * c * delta_T;

% Affichage
printf("Différence de température : %.0f [K]\n", delta_T);
printf("Énergie thermique nécessaire : %.0f [J]\n", Q);
printf("Soit : %.2f [kJ]\n", Q / 1000);