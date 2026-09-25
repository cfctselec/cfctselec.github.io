% Télécharger OCTAVE depuis https://wiki.octave.org/Using_Octave et l'installer
% Puis copier-coller le code dans OCTAVE

% Données de l'exercice
f = 50;        % Fréquence du réseau [Hz]
n = 1425;      % Fréquence du rotor en pleine charge [tr/min]

% 1. Recherche du nombre de paires de pôles
% Les fréquences de synchronisme possibles sont n_s = 60*f/p
% On recherche p tel que n_s est la valeur la plus proche de n
% (le rotor tourne toujours légèrement en dessous de n_s)
p = 1;
while (true)
  n_s = 60 * f / p;
  printf("p = %d paires de pôles  ->  n_s = %.0f tr/min\n", p, n_s);
  if (n_s <= n)
    % On conserve la dernière valeur de n_s supérieure à n
    if (p > 1)
      p = p - 1;
      n_s = 60 * f / p;
    end
    break;
  end
  p = p + 1;
end

printf("\n--- Résultats ---\n");
printf("Nombre de paires de pôles du stator : p = %d (soit %d pôles)\n", p, 2*p);
printf("Fréquence de synchronisme retenue     : n_s = %.0f tr/min\n", n_s);

% 2. Calcul du glissement
g = (n_s - n) / n_s;
printf("Glissement                          : g = %.4f\n", g);
printf("Glissement en pourcentage           : g = %.1f %%\n", g * 100);