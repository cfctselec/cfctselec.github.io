% Données de l'énoncé
U = 4.5;          % Tension de la pile [V]
C = 3;            % Capacité de la pile [Ah]
prix = 1.50;      % Prix d'achat de la pile [Fr.]

% 1. Calcul de l'énergie totale en Wh (notion d'énergie notée W)
W_wh = U * C;
printf("Énergie totale de la pile : W_wh = %.2f [Wh]\n", W_wh);

% 2. Conversion de l'énergie en kWh
W_kwh = W_wh / 1000;
printf("Énergie totale en kWh : W_kwh = %.5f [kWh]\n", W_kwh);

% 3. Calcul du coût du kWh d'énergie
cout_kwh = prix / W_kwh;
printf("Coût du kWh d'énergie : cout_kwh = %.4f [Fr./kWh]\n", cout_kwh);