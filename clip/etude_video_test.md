# Étude de la vidéo de test (0:00-0:50)

Source : `references/reference_test_0-50s.mp4` (1280×720, 30 img/s, 50,0 s). Planches-contact : `out/review/test_*.jpg` (1 image / 0,5 s).
Mesures : `tools/cuts.py` → `out/review/cuts_test.json`.

## Mesures automatiques
- **Audio** : calé exactement sur le MP3 (décalage mesuré : 0,000 s).
- **Coupes** : 64 détectées sur 50 s, soit un plan toutes les 0,77 s en moyenne. C'est le rythme de l'annexe B (hook et Éden très serrés, 20-40 s plus lent).
- **Synchro** : 91 % des coupes tombent à ±2 images d'un temps ou d'un demi-temps, mais **seulement 28 % à ±1 image**. En moyenne, les coupes arrivent **+32 ms en retard** sur le pic d'attaque et +46 ms sur le début d'attaque (qui précède le pic de 17 ms).
  Cause probable : le test utilisait une grille de temps quantifiée à 23 ms, avec un premier temps à 0,116 s au lieu de 0,20 s.
  → **Règle de la reconstruction** : chaque coupe tombe sur l'image qui contient le début d'attaque (`temps_s − 0,017`), vérifiée par `tools/cuts.py`. Objectif : ≥ 90 % des coupes à ±1 image.
- **Statisme** (différence moyenne < 0,6 sur 1,5 s) : 34,5-37,5 s, soit la caverne (ombres fixes) et le début des deux poings. C'est exactement le plan à repenser.
- Les symboles de 13,5-15,5 s sont coupés au demi-temps, sur les bons instants (écart 20-50 ms, comme le reste).

## Plan par plan : ce que je garde, ce que je corrige
| t (s) | plan | garder | corriger / améliorer |
|---|---|---|---|
| 0-0,6 | goutte d'encre sur papier vierge | papier crème, grain | l'éclaboussure est un cercle de points réguliers : lui donner des lobes et gouttelettes irrégulières (règle de l'encre) |
| 0,6-1,0 | le point devient soleil + horizon | très lisible | l'horizon est un trait isolé : le faire naître du point (la ligne 9.0) |
| 1,0-1,5 | pied figé, poussière | couches de collines, herbe fine | la silhouette est coupée en haut du cadre (jambes seules), le pied reste peu lisible : recadrer sur un vrai profil de pied (talon, voûte, orteils) |
| 1,5-3,3 | point de lumière qui trace, profil de l'enfant, plan large | la frontière papier vierge / monde coloré, déchirée : l'idée la plus forte du hook | le profil de l'enfant à 2,0 s a une tête ronde lisse, soit l'effet « casque » refusé : il faut les ancres d'identité (frange, mèche, oreilles) → `enfant_ref.jpg` indispensable |
| 3,3-4,7 | tronc de l'arbre d'Éden, Adam et Ève | arbre récursif très réussi (feuillage effilé), soleil gravé | la ligne doit visiblement *devenir* le tronc (continuité du trait du plan précédent) |
| 4,7-7,8 | fruit, main d'Ève, Adam, serpent, morsure | fruit rouge seul saturé, chronologie juste (entier puis croqué) | Ève et Adam sont de même taille et de même pose d'un plan à l'autre : varier l'échelle (macro, plongée) |
| 7,8-13,5 | lune, ciel rouge, serpent enroulé, œil → soleil rouge, épée, départ | la bascule rouge est belle ; l'œil qui devient soleil est un bon raccord | l'épée de feu est petite et lointaine ; le fruit qui tombe à 13 s se lit mal (petit, sombre) |
| 13,5-15,5 | symboles en or (sablier, roues aux yeux, arbre de vie, triangle du feu) | net, rythmé au demi-temps | les roues aux yeux sont confuses (yeux minuscules) ; les symboles apparaissent déjà dessinés alors que le prompt demande un tracé en éclair |
| 15,5-16,0 | tache d'encre qui avale l'écran | lobes arrondis, conformes ; noir complet dès 15,87 s | ensuite, alternance noir → papier + point (16,0) → noir (16,3-16,7) → papier + graine (16,8) : un double clignotement. Faire un seul geste : le noir se referme en un point, sans retour au noir |
| 16-20 | point → graine incandescente → racines et arbre | très fort (graine, racines symétriques) | — |
| 20-22 | ouroboros gravé qui tourne | gravure réelle, or sur noir | il occupe le quart du cadre sans rien autour : ajouter profondeur et micro-vie (poussière d'or) ; vérifier que la gueule avale la queue |
| 22-25 | méandres → amphore labyrinthe → Discobole | enchaînement Hilbert très réussi | la ligne d'or qui trace le Discobole est hésitante et fine ; le Discobole gravé apparaît en fondu plutôt que tracé |
| 25-26 | disque → soleil | raccord de forme | soleil vide, sans gravure (anneaux concentriques absents) |
| 26-27 | David en contre-plongée | gravé, bien cadré | la voûte du musée est presque invisible |
| 27-28 | Création (mains de Michel-Ange) | modelé réel, étincelle | — |
| 28-29 | Atlas + sphère céleste | lisible | le globe doré est peu visible ; hommes minuscules à peine perceptibles |
| 29-30 | foudre sur les colonnes | — | colonnes en barreaux plats (lit comme une grille ou une clôture) : il faut des colonnes grecques gravées |
| 30-31 | Prométhée gravit l'escalier en spirale | — | figure minuscule, escalier en tirets : peu lisible |
| 31-32 | torche tendue vers le soleil | — | **bras en « tube » blanc + poing dessiné par code : interdit** (règles « pas de bras en tube », « mains d'une source réelle ») |
| 32-33,4 | statue du dessin de l'auteur, puis tournée | le trait d'or sur l'œil, pas de halo | — |
| 34,3-36,9 | caverne : ombres de presse, locomotive, ampoule, écran | — | **à repenser** (jugé grossier, anachronique, statique) : question posée à l'auteur |
| 36,9-38,7 | deux poings passent la flamme | — | poings et bras dessinés par code, bras en bâtons : même problème que 31 s |
| 38,7-40,4 | Discobole figure noire → figure rouge | la bascule est claire et historiquement juste | — |
| 40,4-43,9 | réseau, porteurs de torches, profil de l'auteur, forge, soufflet, foudre | profil de l'auteur en contre-jour doré (fort) | la foudre sur les colonnes revient une 2e fois, sans élément nouveau ; porteurs de torches en rang parfait, identiques |
| 43,9-50 | le réseau de feu recule jusqu'à l'embrasement | continu, pas de flash répété | l'or final est un aplat plat : ajouter la gravure et la texture de papier |

## Constats d'ensemble (à corriger en priorité, section 5 ter)
1. **« Succession d'images »** : les plans se suivent sans ligne commune. Seuls le hook et 16-25 s ont une vraie continuité de trait. La ligne d'or (9.0) doit passer d'un plan à l'autre partout, surtout à 25-40 s.
2. **Intensité** : aucun effet sur les temps forts (pas de flash, de punch, d'étincelles calées). Même 40-50 s reste sage. Appliquer la boîte à effets 6 bis, dosée par l'énergie mesurée.
3. **Échelle des personnages** : trop souvent petits et au centre (escalier, porteurs, Atlas). Il faut plus de macro et de contre-plongée.
4. **Bras, poings et mains dessinés par code** (31 s, 37 s) : à remplacer par des mains réelles détourées, ou à laisser hors champ.
