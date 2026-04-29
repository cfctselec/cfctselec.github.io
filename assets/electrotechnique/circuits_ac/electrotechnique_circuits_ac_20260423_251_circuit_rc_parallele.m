% Télécharger OCTAVE depuis https://wiki.octave.org/Using_Octave et l'installer
% Puis copier-coller le code dans OCTAVE

% Données du problème
U = 500;        % Tension [V]
R = 500;        % Résistance [Ohm]
C = 6.37e-6;    % Capacité [F]
f = 50;         % Fréquence [Hz]

% Calculs intermédiaires
omega = 2 * pi * f;
printf('Pulsation omega = %.2f rad/s\n', omega);

Xc = 1 / (C * omega);
printf('Réactance capacitive Xc = %.2f Ohm\n', Xc);

% Intensités
Ir = U / R;
Ic = U / Xc;
Itot = sqrt(Ir^2 + Ic^2);
printf('Courant Ir = %.2f A, Ic = %.2f A, Itot = %.3f A\n', Ir, Ic, Itot);

% Impédance et facteur de puissance
Z = U / Itot;
cos_phi = Ir / Itot;
printf('Impédance Z = %.2f Ohm, cos(phi) = %.3f\n', Z, cos_phi);

% Puissances
P = U * Ir;
Q = U * Ic;
S = U * Itot;
printf('Puissance P = %.2f W, Q = %.2f var, S = %.2f VA\n', P, Q, S);