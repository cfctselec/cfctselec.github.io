% Télécharger OCTAVE depuis https://wiki.octave.org/Using_Octave et l'installer
% Puis copier-coller le code dans OCTAVE

% Données (Polaire : Module et Angle en degrés)
I1_mag = 30; theta1_deg = 0;
I2_mag = 22; theta2_deg = 240;
I3_mag = 16; theta3_deg = 120;

% Conversion Polaire vers Rectangulaire (sans nombres complexes)
% Calcul des composantes x (horizontales)
I1x = I1_mag * cos(deg2rad(theta1_deg));
I2x = I2_mag * cos(deg2rad(theta2_deg));
I3x = I3_mag * cos(deg2rad(theta3_deg));
printf('I1x = %.2f A, I2x = %.2f A, I3x = %.2f A\n', I1x, I2x, I3x);

% Calcul des composantes y (verticales)
I1y = I1_mag * sin(deg2rad(theta1_deg));
I2y = I2_mag * sin(deg2rad(theta2_deg));
I3y = I3_mag * sin(deg2rad(theta3_deg));
printf('I1y = %.2f A, I2y = %.2f A, I3y = %.2f A\n', I1y, I2y, I3y);

% Sommes des composantes
Sum_x = I1x + I2x + I3x;
Sum_y = I1y + I2y + I3y;
printf('Somme totale x = %.2f A, Somme totale y = %.2f A\n', Sum_x, Sum_y);

% Composantes du courant de neutre (In = -Sum)
In_x = -Sum_x;
In_y = -Sum_y;
printf('Composantes du neutre : In_x = %.2f A, In_y = %.2f A\n', In_x, In_y);

% Conversion Rectangulaire vers Polaire (Pythagore et Atan2)
In_mag = sqrt(In_x^2 + In_y^2);
In_theta_deg = rad2deg(atan2(In_y, In_x));

printf('--- RESULTATS ---\n');
printf('Module du courant de neutre In = %.2f A\n', In_mag);
printf('Angle du courant de neutre theta_N = %.2f degres\n', In_theta_deg);