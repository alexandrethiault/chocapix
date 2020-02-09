# Mode d'emploi

# Qu'est-ce que c'est

Le script présenté ici a deux fonctions :
1) Accélérer lors du loggage d'une appro la mise à jour des prix Chocapix en faisant lire au script la facture de l'appro pour pouvoir donner au respo appro une liste des prix qui ont changé.
2) De manière plus générale, mais seulement pour Carrefour, Auchan et Houra, automatiser l'intégralité du processus de loggage d'appro (à part le loggage de nouveaux aliments, qui nécessite la création à la main d'une nouvelle fiche d'aliment).

Toutefois, ce script n'a pas pour vocation :
1) De faciliter le changement d'approvisionneur pour une section. Le script n'est d'aucune aide pour le loggage des nouveaux aliments, si ce n'est de prévenir à l'avance quels articles sont nouveaux et quels articles ont déjà été commandés.
2) D'aider dans les inventaires, et en particulier la vérification que les quantités livrées sont bien les quantités écrites sur les factures. Ce script est dédié uniquement au loggage des appros, et vouloir faire l'inventaire en même temps que l'appro va contre le principe de ce script, qui demande de séparer ces deux tâches.

# Prérequis

Le script a été testé avec succès sur Windows 10, MacOS, Ubuntu, et un WSL Ubuntu. Rien n'est garanti pour d'autres systèmes d'exploitation.

Pour loguer une appro avec ce script, il faut selon les marques (voir détail plus bas) avoir la facture PDF originale ou un fichier .txt contenant le code-source HTML de la page web contenant la liste des aliments achetés. Dans le reste du README, je ferai référence à ces deux types de documents sous le même nom "facture".

Dans tous les navigateurs, le code-source HTML d'une page s'ouvre en appuyant sur Ctrl+U sur PC et Cmd+U ou Option+Cmd+U selon le navigateur sur Mac (Pro-tip : Ctrl+A puis Ctrl+C ou Cmd+A puis Cmd+C est une bonne façon de copier tout le code-source rapidement). 

Si votre BE n'a pas commencé à utiliser ce script dès la première appro, il sera aussi utile d'avoir le plus de factures possible venant des anciennes appros.

Pour l'instant les marques suivantes sont prises en charge :
- Carrefour (facture .pdf)
- Auchan (factures .pdf)
- Houra (code-source HTML de https://www.houra.fr/cpt/index.php?c=ancienne-commande&idPanier=xxxxxxxx collé dans un fichier .txt)
- Cora (factures .pdf et récapitulatifs de commande .pdf)
- Picard (factures .pdf)

Télécharger le fichier be.py et le ranger dans un dossier qui contiendra aussi les factures. Créer un sous-dossier, l'appeler "archive", et y ranger toutes les factures qui ont déjà été loguées par le passé s'il y en a.

Pour exécuter ce script il faut au préalable un interpréteur Python 3.6 ou plus récent. Il faudra éventuellement installer les modules Python suivants, s'ils provoquent des erreurs d'imports : os, sys, re, time, tika et pyautogui
  
Sauf pour pyautogui, pour installer un module Python, il faut taper dans un invite de commande, en remplaçant éventuellement pip par pip3 :

pip install nom_du_module

Ou plus simplement, si votre interpréteur est anaconda, taper directement dans un shell Python :

\>\>\> conda install nom_du_module

Si cela ne marche pas, c'est probablement que la version utilisée de Python est antérieure à 3.4 ou que plusieurs versions de Python sont installées. Dans tous les cas, https://docs.python.org/3/installing/index.html est une ressource utile.

Le module pyautogui s'installe aussi de cette manière sur Windows et MacOS mais demande un soin supplémentaire pour les autres OS, ce qui est bien détaillé ici : https://pyautogui.readthedocs.io/en/latest/install.html

Enfin, le script, ou plutôt le module tika qui extrait le contenu des pdf, a besoin pour fonctionner d'une connexion internet.

L'exécution du script peut provoquer quelques bugs plus exotiques, certains sont décrits dans la dernière section du README.

# Utilisation pour la première fois

Ouvrir un invite de commande dans le dossier qui contient le fichier Python, le dossier archive et éventuellement les factures pas encore loguées.

Taper dans l'invite de commande :

python be.py archive
  
Si un message du type "\[MainThread  \] \[WARNI\]  Failed to see startup log message; retrying..." s'affiche, l'ignorer, ça devrait terminer au bout de quelques secondes si la connexion internet est correcte.

A l'issue, s'il n'y a pas d'appro à faire tout de suite, l'invite de commande peut être fermé. Un fichier du nom de "prix_marque.txt" a été ajouté pour chaque marque représentée par au moins une facture : il fait office de base de données des prix pour cette marque, indépendante de celle de Chocapix, et le script l'utilise pour comparer les prix des futures appros.

Ouvrir ces fichiers texte. Les articles y sont listés avec à chaque ligne, un 0, puis le code-barres s'il est présent dans les factures (ou juste "-" sinon), puis le prix unité ou prix au kilogramme, puis le nom de l'article. Parcourir rapidement cette liste d'articles et remplacer les 0 en début de ligne par des 1 pour tous les articles que vous ne souhaitez pas logguer lors d'une appro (des produits en open, par exemple, produit d'entretien, papier cuisson, sel, épices...). Cela permettra au script d'ignorer ces articles à l'avenir.

A part pour le premier caractère de chaque ligne, ces fichiers ne doivent pas être modifiés.

Dans le cas de Carrefour, Auchan et Houra, l'auto-appro est rendue possible mais logue les articles grâce à leurs codes-barres. Si ce n'est pas déjà fait, il faudra donc faire connaître à Chocapix tous les codes-barres des articles que vous avez logués pour ces marques. Comme Chocapix ne permet pas d'ajouter un code-barres pour un article déjà logué, il faudra créer autant de nouveaux articles et faire autant de regroupements que de code-barres manquant. Pour aider dans cette tâche, on pourra utiliser le fichier texte associé à la marque, qui liste justement tous les articles que vous avez commandés auprès de cet approvisionneur.

# Utilisation pour une auto-appro Carrefour, Auchan ou Houra

Les auto-appros sont encore en stade expérimental. Elles ont été testées avec succès sous Chrome et Opera, ne fonctionnent pour l'instant que partiellement sous Safari et Firefox (il faut être sûr d'avoir remplacé le 0 par un 1 pour tous les articles "cachés" par Chocapix) et ne marche pas du tout avec Edge.

Ouvrir un invite de commande dans le dossier qui contient le fichier Python et la facture. Ouvrir Chocapix et cliquer sur "loguer une appro".

Pour lancer le script sur une facture qui s'appelle "facture.pdf" (ou .txt pour Houra), taper :

python be.py facture.pdf appro

Si un message du type "\[MainThread  \] \[WARNI\]  Failed to see startup log message; retrying..." s'affiche, l'ignorer, ça devrait terminer au bout de quelques secondes si la connexion internet est correcte.

Quelques instants après le lancement de la commande une fenêtre va apparaître vous demandant de cliquer sur la case pour les noms d'aliments du menu loggage. C'est parce que ce script n'accède pas directement à Chocapix, et se contente de prendre le contrôle de votre clavier et souris pour faire toutes les opérations d'un loggage habituel, mais beaucoup plus rapidement. Et pour savoir où se trouve la case pour les noms d'article, une bonne façon est de vous demander d'amener la souris dessus et de cliquer.

A ce moment, il faut laisser le script remplir automatiquement les codes-barres, quantités, et prix si ils ont changé. Au cas où quelque chose ne tourne pas bien au cours de cette phase (scrolls, sélection de beaucoup de texte de la page, ou même déconnexion en sont des symptômes), vous pouvez l'arrêter simplement en bougeant la souris. Une fenêtre s'ouvre alors pour confirmer si le mouvement de la souris était volontaire, et si oui le script s'arrête. A noter qu'une brève apparition (puis disparition) de la fenêtre de création d'une fiche d'aliment ou de l'encart rouge signalant une tentative de loguer un article caché ne constitue PAS un comportement inattendu du script, puisque le script exploite ces particularités pour détourner les quantité et prix des aliments non loguables ailleurs, pour éviter de loguer ces articles. Les astuces employées pour cela dépendent fortement de la taille de la fenêtre du navigateur dans lequel Chocapix est ouvert. Ainsi il est recommandé de choisir le zoom standard et d'ouvrir son navigateur en plein écran pour éviter les problèmes.

Si après plusieurs essais (au moins 3) l'auto-appro continue de produire des comportements bizarres, c'est peut-être que votre navigateur ou votre connexion internet ne permet pas à Chocapix de suivre les instructions envoyées par le script. Par défaut une instruction est envoyée toutes les 0.02 secondes. Pour augmenter ce temps selon vos besoins, vous pouvez par exemple saisir la commande "python be.py facture.pdf appro pause=0.025". Pour modifier ce temps de façon permanente, vous pouvez aussi modifier directement le script be.py : ce temps y est défini par la ligne "gui.PAUSE = 0.02" dans les premières lignes après les imports.

A l'issue de cette phase de remplissage automatique, l'invite de commande peut être fermé et la facture peut être rangée dans le dossier "archive". Un compte-rendu au format .txt est créé, listant tous les changements de prix, à l'exception des articles signalés comme non loggables, ainsi que les articles achetés pour la première fois (en tout cas première fois parmi les factures que le script a vues). Dans ce cas, il n'a pas été logué plus tôt par le script et il va falloir le loguer à la main maintenant. Il n'y a aucun danger à modifier ou supprimer ce compte-rendu, après la fin de l'appro sa vocation est purement informative. Le respo news peut par exemple recopier les changements importants dans l'onglet des nouvelles afin d'informer les membres de sa section sur les bonnes ou mauvaises surprises qui peuvent les attendre en loggant leurs aliments préférés.

# Utilisation lors d'une appro Cora ou Picard

Dans le cas de Cora et Picard, il n'y a pas de codes-barres dans les factures. Comme les noms connus par Chocapix ne correspondent pas exactement aux noms des articles dans les factures, la première suggestion de Chocapix peut ne pas être la bonne, donc le script ne peut vraiment rien remplir pour la case du nom de l'article. Le script n'est donc d'aucune aide pour la majorité du loggage de l'appro. En revanche il reste capable de donner la liste des articles qui ont changé de prix, ce qui peut déjà faire gagner un peu de temps.

La meilleure chose à faire est de scanner les codes-barres de tous les articles livrés (sans scanner, il va falloir faire chauffer les touches Ctrl C et V, comme d'habitude), sans regarder si les prix ont changé, puis une fois que c'est fini, lancer le script sur la facture pour obtenir la liste des prix qui ont changé, et mettre à jour à la main ces prix dans Chocapix.

Pour obtenir la liste de tous les articles qui ont changé de prix dans une facture qui s'appelle "facture.pdf", ouvrir un invite de commande et taper :

python be.py facture.pdf

C'est à dire la même chose qu'à la section précédente mais sans le mot-clé "appro". Si un message contenant "[MainThread  ] [WARNI]  Failed to see startup log message; retrying..." s'affiche, l'ignorer.

Juste après, un fichier .txt est créé avec un nom du type "compte-rendu_marque_date.txt". C'est là que sont listés les changements de prix.

# Utilisation non attendue du script
Plusieurs utilisations qui ne rentrent dans aucun des deux cadres cités plus haut (mise à niveau avec l'archive, et appro) peuvent être faites de ce script. Fidèle à la philisophie de Python, "we are all consenting adults here", la plupart de ces cas de figure ne mènent pas à une erreur et peuvent être explorés par un utilisateur curieux. En voici quelques exemples.

Pour lancer le script en mode appro sur une facture qui se trouve dans le dossier archive, il suffit de faire précéder le nom de la facture par "./archive/", comme on pourrait s'y attendre. Rien n'empêche non plus de chercher des fichiers .pdf qui sont en dehors du dossier contenant le script. Il reste donc possible de lancer le script sur une vieille facture, ce qui aura pour conséquence probable de remplacer des prix actuels dans les bases de données de prix par des valeurs dépassées. Aussi, l'éventuel compte-rendu créé n'aura aucun sens puisqu'il montrera les "évolutions" de prix de cette remontée dans le temps. A utiliser avec modération, donc. Pour faire rentrer les choses dans l'ordre, on peut lancer le script sur toutes les factures de la même marque entre celle-là et la plus récente dans l'ordre chronologique, ce qui peut être fait avec la seule commande "python be.py archive".

Il est possible d'actualiser les prix et de produire un compte-rendu en dehors du mode appro. Il suffit pour cela de ne fournir aucun des deux mots-clés appro ou archive. Ainsi, au lieu de suivre le paragraphe "Utilisation pour la première fois" à la lettre, on pourra ne mettre dans le dossier archive que les factures de plus d'un mois, et après avoir tapé "python be.py archive", on pourra appeler "python be.py facture.pdf" pour toutes ces factures passées mais récentes, que l'on n'a pas mises dans le dossier archive, et le script produira alors tous les compte-rendus des appros récentes. Le script triera ici aussi les factures par date avant de calculer les évolutions.

Il est même possible d'actualiser les prix avec une facture en particulier sans compte-rendu ni appro. Pour ça, il faut utiliser le mot-clé "archive" et écrire le nom de la facture. Dans le code du script, mettre le mot-clé archive vérifie d'abord si une facture a été donnée en argument et sinon traite toutes les factures du dossier archive.

Il existe un dernier mot-clé, "noedit", utile si au contraire vous souhaitez produire un compte-rendu sans modifier la base de données, dans un contexte de débug par exemple, ou si quelqu'un qui n'a pas les droits de respo appro veut forcer le respo appro à se bouger en lui mettant sous le nez la longue liste des prix qui changent avec cette appro.

Donner en argument le nom de la facture sert à dire au script quel fichier regarder pour mettre à jour sa base de données des prix. Le mode archive ne fait que lancer la fonction principale du script sur la facture donnée en argument, ou à défaut sur la liste de toutes les factures du dossier "archive". Suivant ce principe, il est possible de donner en arguments plusieurs factures à la fois. Elles seront alors toutes traitées les unes à la suite des autres, triées par ordre chronologique.

Attention à ne pas renommer le dossier "archive" en autre chose et espérer que remplacer le mot-clé "archive" par le nouveau nom de dossier suffira. Le mot-clé n'est pas nommé d'après le dossier, et le nom du dossier que le script tentera d'explorer est hard-codé comme devant être "archive".

Bouger la souris en mode appro avec Carrefour ou Auchan ou appuyer sur Ctrl+C dans l'invite de commande arrête totalement le script. Comme les changements de prix ne sont enregistrés dans une base de donnée qu'au dernier moment à la fin de l'exécution du script, ces changements ne seront pas encore enregistrés au moment de l'arrêt. Donc si Chocapix plante en plein milieu de l'appro, on peut sans crainte relancer le script, les changements de prix seront encore signalés et les nouveaux articles seront encore considérés nouveaux.

# Quelques bugs ou messages d'erreur exotiques
- RuntimeError: Unable to start Tika server. (après un traceback et un message d'erreur contenant Unable to run java; is it installed?) Ce problème rencontré avec un WSL Ubuntu a été résolu en installant Java. Pour plus de détails, voir https://stackoverflow.com/questions/36478741/installing-oracle-jdk-on-windows-subsystem-for-linux. Sur un Windows 10 où le même problème a été rencontré et où Java était déjà installé, la solution était d'ajouter le dossier bin de Java au PATH.
- AttributeError: 'bytes' object has no attribute 'close'. Ce problème rencontré avec Windows 10 a été résolu en cherchant directement la ligne du module tika pointée par le message d'erreur complet, et en la supprimant. Il s'agit d'une erreur du côté de tika qui a été corrigée depuis. Pour plus de détails, voir https://github.com/chrismattmann/tika-python/pull/253/files.
- Globalement, si un message d'erreur similaire au précédent se réfère au module tika, simplement supprimer la ligne ou la partie incriminée du module tika.py qui se trouve dans lib/site-packages/tika/ a tendance à résoudre le problème sans en causer d'autres, étonamment.
- L'ordinateur redémarre dès que le script commence à s'exécuter. Ce problème rencontré avec un MacOS 10.18 s'explique par le fait que l'autorisation de prendre le contrôle du clavier n'avait pas été donnée à Python. La fenêtre pour régler ces autorisations peut apparaître en tapant dans un shell python >>> import pyautogui as g; g.write("a")

# Fonctionnalités futures envisageables
- Prise en charge de Intermarché
- Prise en charge web de Carrefour
- Auto-appro Cora
