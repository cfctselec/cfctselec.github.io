% Télécharger OCTAVE depuis https://wiki.octave.org/Using_Octave et l'installer 
% Puis copier-coller le code dans OCTAVE
% Situation a 
P1_a = 2500; 
P2_a = 2100; 
eta_a = (P2_a / P1_a) * 100; 
printf("a) Rendement moteur : %.2f %\n", eta_a);
% Situation b P1_b = 12000; 
Pp_b = 1800; 
P2_b = P1_b - Pp_b; 
eta_b = P2_b / P1_b; 
printf("b) 
Rendement transformateur : %.2f\n", eta_b);
% Situation c 
P2_c = 4500; 
eta_c = 0.82; 
P1_c = P2_c / eta_c; 
printf("c) Puissance absorbee pompe : %.2f [W]\n", P1_c);
% Situation d 
P1_d = 1500; 
eta_d = 0.75; 
P2_d = P1_d * eta_d; 
Pp_d = P1_d - P2_d; 
printf("d) Puissance perdue chauffage : %.2f [W]\n", Pp_d);
% Situation e 
P2_e = 3000; 
eta_e = 0.88; 
U = 400; 
cosphi = 0.78; 
P1_e = P2_e / eta_e; 
I = P1_e / (U * sqrt(3) * cosphi); 
printf("e) Courant de ligne moteur : %.2f [A]\n", I);