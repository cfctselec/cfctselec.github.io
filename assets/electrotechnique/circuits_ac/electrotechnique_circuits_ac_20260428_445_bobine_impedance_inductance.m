% Télécharger OCTAVE depuis https://wiki.octave.org/Using_Octave et l'installer
% Puis copier-coller le code dans OCTAVE

% Données de l'exercice
U_dc = 10;      % Tension continue [V]
I_dc = 0.4;     % Courant continu [A]
U_ac = 110;     % Tension alternative [V]
I_ac = 2;       % Courant alternatif [A]
f = 50;         % Fréquence [Hz]

% a) Calcul de la résistance R
R = U_dc / I_dc;

% b) Calcul de l'impédance Z
Z = U_ac / I_ac;

% c) Calcul de la réactance XL et de l'inductance L
Xl = sqrt(Z^2 - R^2);
L = Xl / (2 * pi * f);

% Affichage des résultats intermédiaires et finaux
printf("Resistance de la bobine (DC) : %.2f [Ohm]\n", R);
printf("Impedance de la bobine (AC) : %.2f [Ohm]\n", Z);
printf("Reactance inductive XL : %.2f [Ohm]\n", Xl);
printf("Inductance L calculee : %.4f [H] soit %.2f [mH]\n", L, L*1000);