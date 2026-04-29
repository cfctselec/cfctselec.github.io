% Télécharger OCTAVE depuis https://wiki.octave.org/Using_Octave et l'installer
% Puis copier-coller le code dans OCTAVE

% Données du problème
c = 200;      % Constante du compteur [tr/kWh]
n = 15;       % Nombre de tours
t_sec = 60;   % Temps en secondes
U = 400;      % Tension composée [V]
I = 8.5;      % Courant de ligne [A]

% Calcul de l'énergie
W_kwh = n / c;
printf('Énergie mesurée W = %.4f kWh\n', W_kwh);

% Calcul de la puissance active
t_h = t_sec / 3600;
P_watt = (W_kwh / t_h) * 1000;
printf('Puissance active P = %.2f W\n', P_watt);

% Calcul de la puissance apparente
S_va = sqrt(3) * U * I;
printf('Puissance apparente S = %.2f VA\n', S_va);

% Facteur de puissance
cos_phi = P_watt / S_va;
printf('Facteur de puissance cos(phi) = %.3f\n', cos_phi);