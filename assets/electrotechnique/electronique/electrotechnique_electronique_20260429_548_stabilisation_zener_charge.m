% Télécharger OCTAVE depuis https://wiki.octave.org/Using_Octave et l'installer
% Puis copier-coller le code dans OCTAVE

U1 = 12;    % [V] Tension d'entrée
Rv = 100;   % [Ohm] Résistance série
Uz = 6.2;   % [V] Tension Zener
Rl = 220;   % [Ohm] Résistance de charge

% a) Tension de sortie
U2 = Uz;
printf("a) Tension de sortie : U2 = %.2f [V]\n", U2);

% b) Courant dans la résistance série
Irv = (U1 - U2) / Rv;
printf("b) Courant Irv : Irv = %.4f [A] (%.2f [mA])\n", Irv, Irv*1000);

% c) Courant dans la charge
Il = U2 / Rl;
printf("c) Courant charge Il : Il = %.4f [A] (%.2f [mA])\n", Il, Il*1000);

% d) Courant dans la Zener
Iz = Irv - Il;
printf("d) Courant Zener Iz : Iz = %.4f [A] (%.2f [mA])\n", Iz, Iz*1000);

% e) Puissance Zener
Pz = Uz * Iz;
printf("e) Puissance dissipee Pz : Pz = %.4f [W] (%.2f [mW])\n", Pz, Pz*1000);