% Télécharger OCTAVE depuis https://wiki.octave.org/Using_Octave et l'installer
% Puis copier-coller le code dans OCTAVE
R = 80;        % [Ohm] Valeur d'une résistance
U = 400;       % [V] Tension composée (entre phases)
Uph = 230;     % [V] Tension simple (entre phase et neutre)
P_mes = 1.984; % [kW] Puissance mesurée par le technicien
% a) Puissance en couplage triangle
P_delta_W = 3 * (U^2 / R);
P_delta_kW = P_delta_W / 1000;
printf("a) Puissance en triangle : P_delta = %.2f [kW]\n", P_delta_kW);
% b) Puissance en couplage étoile
P_star_W = 3 * (Uph^2 / R);
P_star_kW = P_star_W / 1000;
printf("b) Puissance en etoile : P_star = %.3f [kW]\n", P_star_kW);

% c) Vérification du couplage
if abs(P_star_kW - P_mes) < 0.01
printf("c) Le couplage detecte est : ETOILE\n");
elseif abs(P_delta_kW - P_mes) < 0.01
printf("c) Le couplage detecte est : TRIANGLE\n");
else
printf("c) Mesure non conforme aux couplages standards.\n");
end