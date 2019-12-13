# Mode d'emploi

# Qu'est-ce que c'est

Le script présenté ici a deux fonctions :
1) Accélérer lors du loggage d'une appro la mise à jour des prix Chocapix en faisant lire au script la facture de l'appro pour pouvoir donner au respo appro une liste des prix qui ont changé.
2) De manière plus générale, mais seulement pour Carrefour et Auchan, automatiser l'intégralité du processus de loggage d'appro (à part le loggage de nouveaux aliments, qui nécessite la création à la main d'une nouvelle fiche d'aliment).

Toutefois, ce script n'a pas pour vocation :
1) De faciliter le changement d'approvisionneur pour une section. Le script n'est d'aucune aide pour le logguage des nouveaux aliments, si ce n'est de prévenir à l'avance quels articles sont nouveaux et quels articles ont déjà été commandés.
2) D'aider dans les inventaires, et en particulier la vérification que les quantités livrées sont bien les quantités écrites sur les factures. Ce script est dédié uniquement au loggage des appros, et vouloir faire l'inventaire en même temps que l'appro va contre le principe de ce script, qui demande de séparer ces deux tâches.

# Prérequis

Le script a été testé avec succès sur Windows 10, MacOS, Ubuntu, et un WSL Ubuntu. Rien n'est garanti pour d'autres systèmes d'exploitation.

Pour loguer une appro avec ce script il faut au préalable avoir la facture PDF originale (pas un scan) et un interpréteur Python 3.6 ou plus récent. Il sera aussi utile d'avoir le plus de factures possible venant des anciennes appros. Renommer éventuellement les factures pour qu'il n'y ait pas d'espaces dans leurs noms. Télécharger le fichier be.py et le ranger dans un dossier qui contiendra aussi les factures. Créer un sous-dossier, l'appeler "archive", et y ranger toutes les factures qui ont déjà été loguées par le passé.

Pour l'instant les factures suivantes sont prises en charge :
- Carrefour
- Auchan
- Picard
- Cora (factures)
- Cora (récapitulatifs de commande)
- Houra

Il faudra éventuellement installer les modules Python suivants, s'ils provoquent des erreurs d'imports : os, sys, time, tika et pyautogui
  
Sauf pour pyautogui, pour installer un module Python, il faut taper dans un invite de commande, en remplaçant éventuellement pip par pip3 :

pip install nom_du_module

Ou plus simplement, si votre interpréteur est anaconda, taper directement dans un shell Python :

\>\>\> conda install nom_du_module

Si cela ne marche pas, c'est probablement que la version utilisée de Python est antérieure à 3.4 ou que plusieurs versions de Python sont installées. Dans tous les cas, https://docs.python.org/3/installing/index.html est une ressource utile.

Pyautogui s'installe aussi de cette manière sur Windows mais demande un soin supplémentaire pour les autres OS, ce qui sont est bien détaillé ici : https://pyautogui.readthedocs.io/en/latest/install.html.

Pour les utilisateurs de Windows les plus mal à l'aise avec les installations, une application (54Mo) directement exécutable sans rien télécharger d'autre est disponible ici : [[[TODO]]]. En cas d'utilisation de ce script, il faudra remplacer dans le reste de ce mode d'emploi tous les "python be.py" par des "./be"

L'exécution du script peut provoquer quelques bugs plus exotiques, certains sont décrits dans la dernière section du README.

# Utilisation pour la première fois

Ouvrir un invite de commande dans le dossier qui contient le fichier Python, le dossier archive et éventuellement les factures pas encore loguées.

Taper dans l'invite de commande :

python be.py archive
  
Si un message contenant "[MainThread  ] [WARNI]  Failed to see startup log message; retrying..." s'affiche, l'ignorer, ça devrait terminer au bout de quelques secondes.

A l'issue, s'il n'y a pas d'appro à faire tout de suite, l'invite de commande peut être fermé. Un fichier du nom de "prix_marque.txt" a été ajouté pour chaque marque représentée par au moins une facture (Carrefour, Picard...) : il fait office de base de données des prix pour cette marque, et le script l'utilise pour comparer les prix des futures appros.

Ouvrir ces fichiers texte. Les articles y sont listés avec à chaque ligne, un 0, puis le code-barres s'il est présent dans les factures (ou juste "-" sinon), puis le prix unité ou prix au kilogramme, puis le nom de l'article. Parcourir rapidement cette liste d'articles et remplacer les 0 en début de ligne par des 1 pour tous les articles que vous ne souhaitez pas logguer lors d'une appro (des produits en open, par exemple, produit d'entretien, papier cuisson, sel, épices...). Cela permettra au script d'ignorer ces articles à l'avenir.

A part pour le premier caractère de chaque ligne, ces fichiers ne doivent pas être modifiés.

_Dans des versions précédentes, il fallait lancer la commande une fois pour chaque ancienne facture et veiller à faire cela dans l'ordre chronologique des factures. Il fallait aussi fournir en argument le nom du supermarché d'où venait chaque facture. Aujourd'hui, le script détecte tout seul la marque et la date, c'est pourquoi il suffit de tout mettre dans un dossier "archive". Le script triera tout seul les factures par date pour avoir dans la base de données finale les prix les plus actuels de chaque aliment._

# Utilisation pour une appro Carrefour ou Auchan

Ouvrir un invite de commande dans le dossier qui contient le fichier Python et la facture. Ouvrir Chocapix et cliquer sur "loguer une appro".

Pour lancer le script sur une facture qui s'appelle "facture.pdf", taper :

python be.py facture.pdf appro

Si un message contenant "[MainThread  ] [WARNI]  Failed to see startup log message; retrying..." s'affiche, l'ignorer.

Quelques instants après le lancement de la commande une fenêtre va apparaître vous demandant de cliquer sur la case pour les noms d'aliments du menu loggage. C'est parce que ce script n'accède pas directement à Chocapix, et se contente de prendre le contrôle de votre clavier et souris pour faire toutes les opérations d'un loggage habituel, mais beaucoup plus rapidement (par défaut 20 actions par secondes, modifiable dans les premières lignes du script si besoin). Et pour savoir où se trouve la case pour les noms d'article, une bonne façon est de vous demander d'amener la souris dessus.

A ce moment, il faut laisser le script remplir automatiquement les cases avec les chiffres pertinents de la facture. Au cas où quelque chose ne tourne pas bien au cours de cette phase, vous pouvez l'arrêter simplement en bougeant la souris. Une fenêtre s'ouvre alors pour vérifier si le mouvement de la souris était volontaire, et si oui le script s'arrête. A noter qu'une brève apparition (puis disparition) de la fenêtre de création d'une fiche d'aliment ne constitue PAS un comportement inattendu du script, puisque c'est en rentrant la quantité et le prix d'un aliment non loguable dans cette fenêtre, puis en la fermant, que le script évite de loguer les articles que vous avez oublié de lui signaler comme non loguables.

Pendant cette phase de remplissage automatique des cases du menu loggage d'appro, les articles lus dans la facture sont listés dans l'invite de commande, à titre informatif. A la fin, le script affiche dans l'invite de commande la liste des articles dont le prix a changé. Ces articles ont déjà été loggués et le prix a déjà été changé, c'est donc encore à titre informatif que ces changements sont affichés.

Enfin, le script affiche dans l'invite de commande la liste des nouveaux articles, jamais rencontrés, dont il faut créer une fiche. Par "jamais rencontré" il faut comprendre "jamais rencontré par le script". En effet si la section "Usage pour la première fois" n'a pas été suivie ou si des factures sont manquantes, le script peut ne pas connaître un article qui a bien été logué dans Chocapix il y a longtemps. Dans ce cas, il n'a pas été cité plus haut par le script et il va falloir le loguer à la main maintenant.

C'est terminé. L'invite de commande peut être fermé. A l'issue de l'appro, un compte-rendu au format .txt est créé, listant tous les changements de prix, à l'exception des articles signalés comme non loggables. Il n'y a aucun danger à modifier ou supprimer ce compte-rendu, sa vocation est purement informative. Le respo news peut par exemple recopier les changements importants dans l'onglet des nouvelles afin d'informer les membres de sa section sur les bonnes ou mauvaises surprises qui peuvent les attendre en loggant leurs aliments préférés.

# Utilisation pour une appro Cora, Houra ou Picard

Dans le cas de Cora, Houra ou Picard, il n'y a pas de codes-barres dans les factures. Comme les noms connus par Chocapix ne correspondent pas exactement aux noms des articles dans les factures, la première suggestion de Chocapix peut ne pas être la bonne, donc le script ne peut pas vraiment rien remplir pour la case du nom de l'article. Le script n'est donc d'aucune aide pour la majorité du loggage de l'appro. En revanche il reste capable de donner la liste des articles qui ont changé de prix, ce qui peut déjà faire gagner un peu de temps.

La meilleure chose à faire est de scanner les codes-barres de tous les articles livrés (sans scanner, il va falloir faire chauffer les touches Ctrl C et V, comme d'habitude), sans regarder si les prix ont changé, puis une fois que c'est fini, lancer le script sur la facture pour obtenir la liste des prix qui ont changé, et mettre à jour à la main ces prix dans Chocapix.

Pour obtenir la liste de tous les articles qui ont changé de prix dans une facture qui s'appelle "facture.pdf", ouvrir un invite de commande et taper :

python be.py facture.pdf

C'est à dire la même chose qu'à la section précédente mais sans le mot-clé "appro". Si un message contenant "[MainThread  ] [WARNI]  Failed to see startup log message; retrying..." s'affiche, l'ignorer.

Juste après, un fichier .txt est créé avec un nom du type "compte-rendu_marque_date.txt". C'est là que sont listés les changements de prix.

# Utilisation non attendue du script
Plusieurs utilisations qui ne rentrent dans aucun des deux cadres cités plus haut (mise à niveau avec l'archive, et appro) peuvent être faites de ce script. Fidèle à la philisophie de Python, "we are all consenting adults here", la plupart de ces cas de figure ne mènent pas à une erreur et peuvent être explorés par un utilisateur curieux. En voici quelques exemples.

Pour lancer le script en mode appro sur une facture qui se trouve dans le dossier archive, il suffit de faire précéder le nom de la facture par "./archive/", comme on pourrait s'y attendre. Rien n'empêche non plus de chercher des fichiers .pdf qui sont en dehors du dossier contenant le script. Il reste donc possible de lancer le script sur une vieille facture, ce qui aura pour conséquence probable de remplacer des prix actuels dans les bases de données de prix par des valeurs dépassées. Aussi, l'éventuel compte-rendu créé n'aura aucun sens puisqu'il montrera les "évolutions" de prix de cette remontée dans le temps. A utiliser avec modération, donc. Pour faire rentrer les choses dans l'ordre, on peut lancer le script sur toutes les factures de la même marque entre celle-là et la plus récente dans l'ordre chronologique, ce qui peut être fait avec la seule commande "python be.py archive".

Il est possible de surveiller les évolutions de prix et de produire un compte-rendu en dehors du mode appro. Il suffit pour cela de ne fournir aucun des deux mots-clés appro ou archive. Ainsi, au lieu de suivre le paragraphe "Utilisation pour la première fois" à la lettre, on pourra ne mettre dans le dossier archive que les factures de plus d'un mois, et après avoir tapé "python be.py archive", on pourra appeler "python be.py facture.pdf" pour toutes ces factures passées mais récentes, que l'on n'a pas mises dans le dossier archive, et le script produira alors tous les compte-rendus des appros récentes. Le script triera ici aussi les factures par date avant de calculer les évolutions.

Il est même possible de simplement surveiller les évolutions de prix sur une facture en particulier sans compte-rendu ni appro. Pour ça, il faut utiliser le mot-clé "archive" et écrire le nom de la facture. Dans le code du script, le mot-clé archive vérifie d'abord si une facture a été donnée en argument et sinon traite toutes les factures du dossier archive.

Donner en argument le nom de la facture sert à dire au script quel fichier regarder pour mettre à jour sa base de données des prix. Le mode archive ne fait que lancer la fonction principale du script sur la facture donnée en argument, ou à défaut sur la liste de toutes les factures du dossier "archive". Suivant ce principe, il est possible de donner en arguments plusieurs factures à la fois. Elles seront alors toutes traitées les unes à la suite des autres, triées par ordre chronologique.

Attention à ne pas renommer le dossier "archive" en autre chose et espérer que remplacer le mot-clé "archive" par le nouveau nom de dossier suffira. Le mot-clé n'est pas nommé d'après le dossier, et le nom du dossier que le script tentera d'explorer est hard-codé comme devant être "archive".

Bouger la souris en mode appro avec Carrefour ou Auchan ou appuyer sur Ctrl+C dans l'invite de commande arrête totalement le script. Comme les changements de prix ne sont enregistrés dans une base de donnée qu'au dernier moment à la fin de l'exécution du script, ces changements ne seront pas encore enregistrés au moment de l'arrêt. Donc si Chocapix plante en plein milieu de l'appro, on peut sans crainte relancer le script, les changements de prix seront encore signalés et les nouveaux articles seront encore considérés nouveaux.

# Quelques messages d'erreur exotiques
- RuntimeError: Unable to start Tika server. (après un traceback et un message d'erreur contenant Unable to run java; is it installed?) Ce problème rencontré avec un WSL Ubuntu a été résolu en installant Java. Pour plus de détails, voir https://stackoverflow.com/questions/36478741/installing-oracle-jdk-on-windows-subsystem-for-linux. Sur un Windows 10 où le même problème a été rencontré et où Java était déjà installé, la solution était d'ajouter le dossier bin de Java au PATH.
- AttributeError: 'bytes' object has no attribute 'close'. Ce problème rencontré avec Windows 10 a été résolu en cherchant directement la ligne du module tika pointée par le message d'erreur complet, et en la supprimant. Il s'agit d'une erreur du côté de tika qui a été corrigée depuis. Pour plus de détails, voir https://github.com/chrismattmann/tika-python/pull/253/files.

# Fonctionnalités à venir
- Prise en charge de Intermarché (?)
- Prise en charge des récapitulatifs de commande de Carrefour
