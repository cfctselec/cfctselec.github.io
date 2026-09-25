% Télécharger OCTAVE depuis https://wiki.octave.org/Using_Octave et l'installer
% Puis copier-coller le code dans OCTAVE

% Données de la plaque signalétique du moteur monophasé
P2_kW = 1.0;         % Puissance utile mécanique [kW]
P2 = P2_kW * 1000;   % Puissance utile [W]
U = 230;             % Tension alternative monophasée [V]
f = 50;              % Fréquence du réseau [Hz]
cos_phi = 0.8;       % Facteur de puissance
eta = 0.83;          % Rendement du moteur (83%)

% 1. Calcul de la puissance active électrique absorbée P1
P1 = P2 / eta;
printf("Puissance active absorbée : P1 = %.2f [W] (soit %.4f [kW])\n", P1, P1/1000);

% 2. Calcul du courant nominal absorbé I_N
I_N = P1 / (U * cos_phi);
printf("Courant nominal absorbé : I_N = %.4f [A]\n", I_N);

% 3. Valeur de réglage du disjoncteur thermique
I_reglage = I_N;
printf("Valeur de réglage de la protection thermique : I_réglage = %.2f [A]\n", I_reglage);