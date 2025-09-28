# Model steps

Ongoing work, French only!

Source : https://github.com/mobility-team/mobility/issues/145#issuecomment-3228039287


Le fonctionnement actuel est le suivant :

Initialisation :
- G�n�ration des s�quences de motifs de d�placement dans chaque zone de transport, selon le profil de la population r�sidente (CSP, nombre de voitures du m�nage, type de cat�gorie urbaine de la commune), et des besoins en heures d'activit� pour chaque �tape des s�quences.
- Calcul des opportunit�s disponibles (=heures d'activit�s disponibles) par motif, pour chaque zone de transport.

Boucle :
- Calcul des co�ts g�n�ralis�s de transport pour chaque couple motif - origine - destination (sans congestion pour la premi�re it�ration).
- Calcul des probabilit�s de choisir une destination en fonction du motif et de l'origine du d�placement ainsi que du lieu de r�sidence des personnes.
- Echantillonnage d'une s�quence de destinations pour chaque s�quence de motifs, zone de transport de r�sidence et CSP.
- Recherche des top k s�quences de modes disponibles pour r�aliser ces s�quences de d�placements (k<=10)
- Calcul des flux r�sultants par OD et par mode, puis recalcul des co�ts g�n�ralis�s.
- Calcul d'une part de personnes qui vont changer d'assignation s�quence de motifs + modes (en fonction de la saturation des opportunit�s � destination, de possibilit�s d'optimisation comparatives, et d'une part de changements al�atoires).
- Calcul des opportunit�s restantes � destination.
- Recommencement de la proc�dure avec cette part de personnes non assign�es.
