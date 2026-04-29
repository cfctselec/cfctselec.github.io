% Télécharger OCTAVE depuis [https://wiki.octave.org/Using_Octave]
% et l'installer. Puis copier-coller le code dans OCTAVE.
% === Étape 4 : Tangente, pente et résistance R ===
% Données du point A : U = 7 V, I = 14 mA
U_A = 7;            % [V]
I_A_mA = 14;        % [mA]
I_A = I_A_mA / 1000;% [A] conversion

% --- Résistance directe (méthode recommandée) ---
R_direct = U_A / I_A;
printf("Point A : U = %.1f [V], I = %.1f [mA]\n", U_A, I_A_mA);
printf("Resistance R = DeltaU/DeltaI = %.1f [ohm]\n\n", R_direct);

% --- Tangente sur papier (avec échelles) ---
ech_V_cm = 1;       % [V/cm] verticale
ech_mA_cm = 2;      % [mA/cm] horizontale
ech_A_cm = ech_mA_cm / 1000; % [A/cm]

delta_y_cm = U_A / ech_V_cm;
delta_x_cm = I_A_mA / ech_mA_cm;
tan_papier = delta_y_cm / delta_x_cm;
theta_deg = atand(tan_papier);

printf("Pente papier (tan theta) : %.2f (sans unite)\n", tan_papier);
printf("Angle theta papier : %.1f [degres]\n", theta_deg);
printf("Pente en % : %.1f %\n\n", tan_papier * 100);

% --- Résistance via échelles ---
R_echelles = tan_papier * (ech_V_cm / ech_A_cm);
printf("Resistance via echelles : %.1f [ohm]\n", R_echelles);

% --- Tangente papier requise pour R = 500 ohm ---
tan_requis = R_direct * ech_A_cm / ech_V_cm;
theta_requis = atand(tan_requis);
printf("\nPour R = %.1f [ohm] avec ces echelles :\n", R_direct);
printf("  Tangente papier requise : %.2f\n", tan_requis);
printf("  Angle requis : %.1f [degres]\n", theta_requis);

% --- Vérification ---
if abs(R_echelles - R_direct) < 1e-6
printf("\nVerification : OK - methodes concordantes.\n");
else
printf("\nAttention : échelles non adaptees au point A.\n");
end