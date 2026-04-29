% Télécharger OCTAVE depuis https://wiki.octave.org/Using_Octave et l'installer
% Puis copier-coller le code dans OCTAVE

% Données de l'exercice (Inspiré par la source 2025_TS_PELE)
P2 = 11000;         % Puissance utile [W]
U = 400;            % Tension réseau [V]
cosphi = 0.85;      % Facteur de puissance
eta = 0.88;         % Rendement
t = 8;              % Temps de fonctionnement [h]
prix_kwh = 0.25;    % Prix de l'énergie [CHF/kWh]

% a) Puissance absorbée P1
P1 = P2 / eta;

% b) Courant de ligne I
I = P1 / (U * sqrt(3) * cosphi);

% c) Puissance apparente S et réactive Q
S = P1 / cosphi;
Q = sqrt(S^2 - P1^2);

% d) Énergie consommée W
W_kwh = (P1 / 1000) * t;

% e) Coût
cout = W_kwh * prix_kwh;

% Affichage des résultats
printf("Puissance absorbée P1 : %.2f [W]\n", P1);
printf("Intensité du courant I : %.2f [A]\n", I);
printf("Puissance réactive Q : %.2f [var]\n", Q);
printf("Énergie consommée W : %.2f [kWh]\n", W_kwh);
printf("Coût d'exploitation : %.2f [CHF]\n", cout);