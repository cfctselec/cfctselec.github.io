% Données de l'énoncé
N = 800;              % Nombre de spires
l = 0.25;             % Longueur de la bobine [m] (25 cm)
S = 15e-4;            % Section de la bobine [m^2] (15 cm^2)
I = 5;                % Intensité du courant [A]
mu_0 = 4 * pi * 1e-7; % Perméabilité du vide [H/m]

% 1. Calcul du champ magnétique H
H = (N * I) / l;
printf("Champ magnétique : H = %.2f [A/m]\n", H);

% 2. Calcul de l'induction magnétique B
B = mu_0 * H;
printf("Induction magnétique : B = %.6f [T]\n", B);

% 3. Calcul du flux magnétique Phi
Phi = B * S;
printf("Flux magnétique : Phi = %.8e [Wb] (soit %.3f [uWb])\n", Phi, Phi * 1e6);