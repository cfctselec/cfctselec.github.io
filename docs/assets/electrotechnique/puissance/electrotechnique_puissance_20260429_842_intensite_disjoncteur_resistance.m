% Télécharger OCTAVE depuis https://wiki.octave.org/Using_Octave et l'installer
% Puis copier-coller le code dans OCTAVE

% Données de l'énoncé
W_kwh = 34;         % Énergie absorbée [kWh]
t_debut = 8;        % Heure de début [h]
t_fin = 20;         % Heure de fin [h]
U = 230;            % Tension d'alimentation [V]

% 1. Calcul de la durée de fonctionnement
t = t_fin - t_debut;
printf("Durée de fonctionnement : t = %d [h]\n", t);

% 2. Calcul de la puissance absorbée
% Conversion de kWh en W (W_wh / t)
P = (W_kwh * 1000) / t;
printf("Puissance absorbée : P = %.2f [W]\n", P);

% 3. Calcul de l'intensité du courant
I = P / U;
printf("Intensité du courant : I = %.4f [A]\n", I);

% 4. Calcul de la résistance
R = U / I;
printf("Résistance de l'appareil : R = %.4f [Ohm]\n", R);