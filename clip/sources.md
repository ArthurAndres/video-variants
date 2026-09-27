# Sources des références visuelles

Toutes viennent de Wikimedia Commons (domaine public ou licence ouverte), rangées dans `references/web/hd/` (hors git).
Usage : détourage, puis vectorisation et gravure (annexe A.3). Aucune image n'est collée telle quelle dans le clip.

| fichier local | œuvre | fichier Commons | auteur de la photo | licence | taille |
|---|---|---|---|---|---|
| creation_detail.jpg | Michel-Ange, *La Création d'Adam* (détail des mains) | File:Creation of Adam (Michelangelo) Detail.jpg | Michel-Ange (reproduction) | Domaine public | 1400×1047 |
| creation_adam.jpg | Michel-Ange, *La Création d'Adam* (scène entière) | File:Michelangelo - Creation of Adam (cropped).jpg | Michel-Ange (reproduction) | Domaine public | 3524×1599 |
| discobole_massimo.jpg | Myron, *Discobole* (copie Lancelotti), profil sur fond sombre uni | File:Discobolus in National Roman Museum Palazzo Massimo alle Terme.JPG | Livioandronico2013 | CC BY-SA 4.0 | 1920×3210 |
| discobole_pd.jpg | Myron, *Discobole* (copie Lancelotti), fond clair | File:Discobolus Lancelotti Massimo.jpg | Marie-Lan Nguyen | Domaine public | 1920×2931 |
| atlas_farnese.jpg | *Atlas Farnèse* (Naples), fond sombre | File:Atlas (Farnese Globe).jpg | Gabriel Seah | CC BY-SA 3.0 | 1200×1600 |
| atlas_farnese_face.jpg | *Atlas Farnèse*, de face, globe bien lisible | File:Atlante Farnese (fronte) - Museo Archeologico Nazionale di Napoli.jpg | Simon Burchell | CC BY-SA 4.0 | 1920×2560 |
| david_contreplongee.jpg | Michel-Ange, *David*, contre-plongée avec la voûte de l'Accademia | File:Michelangelo's David, Galleria dell'Accademia, Florence (26612184971).jpg | Dimitris Kamaras | CC BY 2.0 | 1920×2560 |
| ouroboros_jennis.jpg | Lucas Jennis, *De Lapide Philosophico* (1625), ouroboros gravé | File:Ouroboros 1.jpg | Lucas Jennis | Domaine public | 815×832 |

Fournies par l'auteur (licence non vérifiée, usage personnel) : `references/ouroboros_gravure.jpg` (gravure utilisée dans le test), `references/david_contreplongee.jpg` (480×640), planches de mains.
Les licences CC BY / BY-SA demandent de créditer l'auteur de la photo : à mettre dans la description de la vidéo si elle est diffusée.

## Retélécharger
```
cd references/web/hd
python3 ../../../tools/fetch_commons.py 0 "creation_adam:Michelangelo - Creation of Adam (cropped).jpg" "creation_detail:Creation of Adam (Michelangelo) Detail.jpg" "atlas_farnese:Atlas (Farnese Globe).jpg" "ouroboros_jennis:Ouroboros 1.jpg"
python3 ../../../tools/fetch_commons.py 1920 "discobole_massimo:Discobolus in National Roman Museum Palazzo Massimo alle Terme.JPG" "discobole_pd:Discobolus Lancelotti Massimo.jpg" "atlas_farnese_face:Atlante Farnese (fronte) - Museo Archeologico Nazionale di Napoli.jpg" "david_contreplongee:Michelangelo's David, Galleria dell'Accademia, Florence (26612184971).jpg"
```
Recherche : `python3 tools/commons.py "requête"`. Wikimedia bride les gros originaux et les tailles non standard (erreur 429) : utiliser 1920 ou 3840.
