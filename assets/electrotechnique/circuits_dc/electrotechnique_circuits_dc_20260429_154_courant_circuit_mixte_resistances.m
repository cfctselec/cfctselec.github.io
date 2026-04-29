% Télécharger OCTAVE depuis https://wiki.octave.org/Using_Octave et l'installer
% Puis copier-coller le code dans OCTAVE

% Données
U = 230;            % Tension appliquee entre D et C [V]
R7 = 460;           % Resistance segment entree [Ohm]
R3 = 35;            % Resistance segment derivation 1 [Ohm]
R2 = 35;            % Resistance segment derivation 2 [Ohm]
R5 = 120;           % Resistance segment derivation 3 [Ohm]
R6 = 120;           % Resistance charge en parallele [Ohm]
R8 = 20;            % Resistance segment de liaison [Ohm]
R10 = 850;          % Resistance segment sortie [Ohm]

% Calcul de la branche en derivation
R_br = R3 + R2 + R5;
% Calcul du groupement mixte parallele
R_par = 1 / (1/R_br + 1/R6);

% Resistance totale du circuit de distribution
Requ = R7 + R_par + R8 + R10;

% Intensite du courant total par la loi d'Ohm
I = U / Requ;

% Affichage detaille des etapes de calcul
printf("Resistance de la branche en derivation : %.2f [Ohm]\n", R_br);
printf("Resistance equivalente du bloc parallele : %.2f [Ohm]\n", R_par);
printf("Resistance totale equivalente (D-C) : %.2f [Ohm]\n", Requ);
printf("Courant total circulant : %.4f [A] soit %.2f [mA]\n", I, I*1000);