% Télécharger OCTAVE depuis https://wiki.octave.org/Using_Octave et l'installer
% Puis copier-coller le code dans OCTAVE
f_usa = 60;          % frequence du reseau americain [Hz]
n     = 850;         % fréquence de rotation relevee [tr/min]

% 1. fréquence de synchronisme la plus proche au-dessus de 850 tr/min a 60 Hz
p = 4;               % nombre de paires de poles recherche
ns_60 = 60 * f_usa / p;
printf("fréquence de synchronisme a 60 Hz : ns = %.0f tr/min\n", ns_60);

% Verification : p recalcule a partir de ns
p_calc = 60 * f_usa / ns_60;
printf("Nombre de paires de poles : p = %.0f (soit %.0f poles)\n", p_calc, 2*p_calc);

% 2. Glissement a 60 Hz
s = (ns_60 - n) / ns_60;
printf("Glissement : s = %.4f soit %.2f %%\n", s, 100*s);

% 3. fréquence a 50 Hz (meme charge => glissement identique)
f_fr = 50;
ns_50 = 60 * f_fr / p_calc;
n_50  = ns_50 * (1 - s);
printf("fréquence de synchronisme a 50 Hz : ns = %.0f tr/min\n", ns_50);
printf("fréquence de rotation a 50 Hz : n = %.1f tr/min\n", n_50);