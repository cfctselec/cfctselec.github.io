% Données de l'énoncé
U_eff = 35.36;    % Tension efficace de l'onde alternative [V]
S_v = 0.5;        % Déviation verticale de l'oscilloscope [mm/V]

% 1. Calcul de la tension maximale (crête)
U_max = U_eff * sqrt(2);
printf("Tension maximale : U_max = %.4f [V]\n", U_max);

% 2. Calcul de la tension crête-à-crête
U_pp = 2 * U_max;
printf("Tension crête-à-crête : U_pp = %.4f [V]\n", U_pp);

% 3. Calcul de la hauteur verticale de l'image
h = U_pp * S_v;
printf("Hauteur verticale de l'image : h = %.4f [mm]\n", h);