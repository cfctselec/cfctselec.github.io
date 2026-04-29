% Télécharger OCTAVE depuis https://wiki.octave.org/Using_Octave et l'installer
% Puis copier-coller le code dans OCTAVE

% Données
Q_mah = 4500;    % Capacité en mAh
U = 3.8;         % Tension nominale [V]

% Calculs
Q_ah = Q_mah / 1000;
W_wh = U * Q_ah;
W_j = W_wh * 3600;

% Affichage
printf("Capacité : %.1f [Ah]\n", Q_ah);
printf("Énergie stockée : %.2f [Wh]\n", W_wh);
printf("Énergie stockée : %.0f [J]\n", W_j);