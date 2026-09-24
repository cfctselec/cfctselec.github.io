% Données de l'énoncé
n = 19;            % Nombre de fils par conducteur
d = 2.84;          % Diamètre de chaque fil [mm]
I_Cu = 340;        % Courant max dans la corde de cuivre [A]
I_Al = 265;        % Courant max dans la corde d'aluminium [A]

% 1. Calcul de la section d'un fil
A_fil = (pi * d^2) / 4;
printf("Section d'un fil individuel : A_fil = %.4f [mm^2]\n", A_fil);

% 2. Calcul de la section totale de la corde
A_tot = n * A_fil;
printf("Section totale de la corde : A_tot = %.4f [mm^2]\n", A_tot);

% 3. Calcul des densités de courant (J = I / S)
J_Cu = I_Cu / A_tot;
J_Al = I_Al / A_tot;
printf("Densité de courant dans le cuivre : J_Cu = %.4f [A/mm^2]\n", J_Cu);
printf("Densité de courant dans l'aluminium : J_Al = %.4f [A/mm^2]\n", J_Al);

% 4. Calcul de la différence de charge en pourcentage
delta_p = ((I_Cu - I_Al) / I_Cu) * 100;
printf("Différence de charge : delta_p = %.4f [%%]\n", delta_p);