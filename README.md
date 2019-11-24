# Mode d'emploi

# Qu'est-ce que c'est

Le script présenté ici a deux fonctions :
1) Suivre l'évolution des prix du supermarché au moment du loggage d'une nouvelle appro en créant un fichier récapitulant ces changements, de façon à pouvoir informer la section de ces changements de prix sans que le respo appro n'ait à y consacrer son énergie.
2) Optimiser la productivité du respo appro dans le loggage pour accélérer cette opération fastidieuse et répétitive, en lui retirant la charge de la plupart des actions (allers-retours de la souris entre facture et Chocapix, interruptions régulières par les nouveaux aliments qui mettent plus de temps à logguer, vérification au cas par cas des changements de prix des aliments) qu'il a toujours dû faire pour logguer une appro.

Toutefois, ce script n'a pas pour vocation :
1) De remplacer le respo appro. Le script n'est pas capable d'effectuer tout seul l'appro, certaines actions restent à la charge du respo appro.
2) D'aider dans les inventaires. Cette tâche n'a rien à voir avec ce qui est pris en charge par ce script.

# Prérequis

Le script a été testé avec succès sur Windows 10, MacOS, Ubuntu, et un WSL Ubuntu. Rien n'est garanti pour d'autres systèmes d'exploitation.

Pour logguer une appro avec ce script il faut au préalable avoir la facture originale (pas un scan) au format .pdf et avoir un interpréteur Python 3.6 ou plus récent. Il sera aussi utile d'avoir le plus de factures possible venant des anciennes appros. Télécharger le fichier update_prices.py et le ranger dans un dossier qui contiendra aussi les factures.

Il faudra éventuellement installer les modules Python suivants, s'ils provoquent des erreurs d'imports : time, tika, sys et pyperclip ; sur Windows seulement : msvcrt ; sur les autres OS seulement : termios, atexit et select
  
Pour installer un module Python, il faut taper dans un invite de commande :

pip install nom_du_module

Ou plus simplement, si votre interpréteur est anaconda, taper directement dans un shell Python :

\>\>\> conda install nom_du_module

Si cela ne marche pas, c'est probablement que la version utilisée de Python est antérieure à 3.4 ou que plusieurs versions de Python sont installées. Dans tous les cas, https://docs.python.org/3/installing/index.html est une ressource utile.

L'exécition du script peut provoquer quelques bugs plus exotiques, certains sont décrits dans la dernière section du README.


# Utilisation pour la première fois

Ouvrir un invite de commande dans le dossier qui contient le fichier Python et toutes les anciennes factures.

Taper successivement dans l'invite de commande, pour toutes les anciennes factures (sans inclure la dernière si elle n'a pas encoré été logguée), dans un ordre chronologique :

python update_prices.py facture.pdf marque archive

où facture.pdf est à remplacer par le nom d'un fichier contenant une facture, et marque est à remplacer par la marque (Carrefour, Picard...) du supermarché ayant envoyé la facture. Il faut inclure le .pdf dans le nom de la facture.
  
Si un message contenant "[MainThread  ] [WARNI]  Failed to see startup log message; retrying..." s'affiche, l'ignorer, ça devrait durer moins de 5 secondes.

A l'issue, s'il n'y a pas d'appro à faire tout de suite, l'invite de commande peut être fermé. Un fichier du nom de "prix_marque.txt" a été ajouté au dossier du script et des factures : il fait office de base de données des prix pour cette marque, et le script l'utilise pour comparer les prix des futures appros. Il est à ne pas modifier ni supprimer. En revanche il est à votre charge de le copier quelque part (en faire une sauvegarde) pour vous prémunir d'une utilisation erronée du script qui viendrait à modifier de manière non souhaitée ce fichier.

# Utilisation pour une appro

Lire toute la section avant de commencer à effectuer les opérations décrites.

Ouvrir un invite de commande dans le dossier qui contient le fichier Python et la facture. Ouvrir Chocapix. Diviser l'écran en mosaïque de façon à voir à la fois l'invite de commande (pas besoin de plus d'un tiers de l'écran) et Chocapix. Etre prêt à logguer l'appro en s'assurant que la case pour rentrer le code du premier aliment et la case pour la quantité sont à portée de souris.

Pour lancer le script sur une facture de la marque "marque" qui s'appelle "facture.pdf", taper :

python update_prices.py facture.pdf marque appro

Si un message contenant "[MainThread  ] [WARNI]  Failed to see startup log message; retrying..." s'affiche, l'ignorer.

Quelques instants après le lancement de la commande, des chiffres vont commencer à s'afficher dans l'invite de commande. Au bout de quelques secondes, cela peut ressembler à :

X:\Chemin\Du\Dossier> python update_prices.py 06.11_facture.pdf carrefour appro

3245390089854 2

3270190007050 2

3276650121533 
  
Chaque nouveau nombre qui s'affiche dans cet invite de commande, correspond à un code ou une quantité d'un ancien aliment (pas besoin de créer une nouvelle fiche d'aliment, donc).

Il n'y a pas besoin de les copier, c'est fait automatiquement par le script : il ne reste plus qu'à le coller dans la bonne case. Il faut simplement le faire avant que le prochain nombre s'affiche, sinon ce nouveau nombre prend sa place dans le presse-papier.

Que faire si je rate un ou plusieurs nombres ? Pas de panique, le script peut être mis en pause en tapant n'importe quelle lettre de l'alphabet dans l'invite de commande. Ne pas taper Ctrl+C sinon le script sera arrêté définitivement et il faudra recommencer du début. Cela doit vous laisser autant de temps que nécessaire pour récupérer le nombre manqué, le copier coller manuellement vers Chocapix. Quand le retard est rattrapé, appuyer sur Entrer dans l'invite de commande et le script continue. Cela peut ressembler à :

D:\Alexandre\Chocapix>python update_prices.py 06.11_facture.pdf carrefour appro

2019-11-24 14:45:23,856 [MainThread  ] [WARNI]  Failed to see startup log message; retrying...

3245390089854 2

3270190007050 2

3276650121533 1

5601019001030                 // <- Les nombres affichés ne sont pas effacés au fur et à mesure.

Script mis en pause. Appuyer sur Entrer pour le poursuivre. // Cela permet de copier coller à la main ce qu'on a manqué

g                             // <- la lettre tapée pour mettre en pause le script peut s'afficher. Cela n'a aucune importance.

1                             // <- Aucun nombre ne sera affiché deux fois, ce 1 correspond donc au code barre 5601019001030

3166291458405 1

...
 
Par défaut le temps donné pour coller un nombre avant que le prochain prenne sa place est :

- 1 seconde après un numéro de série (puisqu'il suffit de coller et déplacer la souris vers la quantité)

- 4 secondes après une quantité (parce que cette fois il faut coller puis ouvrir une nouvelle fiche de loggage)

Pour changer ces temps de manière ponctuelle pour une seule appro, on pourra à la place de la commande vue plus haut écrire :

python update_prices.py 06.11_facture.pdf carrefour appro pause_set x y

Où x et y (entiers ou à virgule) remplaceront respectivement le 1 et le 4. Choisissez les temps idéaux pour terminer l'appro le plus rapidement possible sans avoir à pauser régulièrement le script. 

Ces paramètres peuvent aussi être changés définitivement en modifiant le code du fichier Python : les deux valeurs y sont définies dans les premières lignes après les imports de modules.

A la fin de cette première phase, le script affiche dans l'invite de commandes une liste d'articles dont le prix a changé. Ces articles ont déjà été loggués, il suffit de modifier leur prix manuellement.

Enfin, le script affiche dans l'invite de commandes la liste des nouveaux articles, jamais rencontrés. Par "jamais rencontré" il faut comprendre "jamais rencontré par le script". En effet si la section "Usage pour la première fois" n'a pas été suivie ou si des factures sont manquantes, le script peut ne pas connaître un article qui a bien été loggué dans Chocapix il y a longtemps. Dans ce cas, il n'a pas été cité plus haut par le script et il va falloir le logguer à la main maintenant.

C'est terminé. L'invite de commande peut être fermé. A l'issue de l'appro, un compte-rendu au format .txt est créé, listant tous les changements de prix. Il n'y a aucun danger à modifier ou supprimer ce compte-rendu, sa vocation est purement informative. Il peut par exemple être recopié dans l'onglet des nouvelles par le respo news afin d'informer les membres de sa section sur les bonnes ou mauvaises surprises qui peuvent les attendre en logguant leurs aliments préférés.

# Détails sur les mots-clé "appro" et "archive"
Le mot-clé archive est, comme expliqué plus haut, à écrire pour faire connaître au script les anciennes factures, dont l'appro a déjà été faite. Quand "archive" est donné en paramètre au script, rien ne sera affiché dans l'invite de commande, le script construit et maintient sa base de données tout seul et il ne produit pas de compte-rendu des changements des prix. 

Au contraire, le mot-clé appro est fait pour être employé en situation réelle d'appro. Tous les aliments sont listés soit dans la partie où les codes barres et quantités sont copiées automatiquement, soit dans la liste finale des nouveaux aliments. Et tous les changements de prix sont signalés. Ce mode crée un compte-rendu des modifications des prix qui peut ensuite être recopié dans le section news de Chocapix.

Toutefois il est possible de produire un compte-rendu en dehors du mode appro. Il suffit pour ça de ne fournir aucun des deux mots-clés appro et archive. Cela peut être utile par exemple si on veut connaître les prix qui ont changé lors d'une récente appro, dont les prix sont toujours d'actualité.

Ainsi, au lieu de suivre le paragraphe "Utilisation pour la première fois" à la lettre, on pourra retirer le mot-clé "archive" des quelques dernières factures, sans pour autant y mettre le mot-clé appro, et le script produira alors tous les compte-rendus des appros récentes.

A l'inverse il n'est pas possible d'utiliser les mots clés appro et archive en même temps.

# Mauvaise utilisation du script
Il faudra bien prendre garde de :
- ne pas modifier le code du script, évidemment, sauf pour modifier définitivement une des variables définissant le temps de pause, ou si vous savez ce que vous faites.
- ne pas modifier à la main le contenu des fichiers prix_marque.txt
- ne pas utiliser le script en mode appro sur un magasin qui ne donne pas les codes-barres de ses aliments dans la facture. Par exemple Picard utilise dans ses factures des codes d'article qui ne correspondent pas au code-barre. Si Chocapix a été renseigné avec le code-barre, le script ne peut pas aider. C'est réparable uniquement en modifiant à la main tous les codes-barres Picard retenus par Chocapix pour les remplacer par les codes de la facture. En attendant, le script ne sera bon qu'à faire ses compte-rendus d'évolution de prix. Il est toujours possible de lancer le script avec le mot-clé "appro" mais le script l'ignorera.
- ne pas lancer le script sur une ancienne facture sans savoir ce qu'on fait. Cela modifiera le fichier prix_marque.txt et renseignera des prix obsolètes devant certains aliments, prix qui seront resignalés inutilement lors de la prochaine appro. Aussi, l'éventuel compte-rendu créé n'aura aucun sens puisqu'il montrera les "évolutions" de prix de cette remontée dans le temps. Pour faire rentrer les choses dans l'ordre, il faut lancer le script avec le mot-clé "archive" sur toutes les factures de la même marque entre celle-là et la plus récente dans l'ordre chronologique.

# Quelques messages d'erreur exotiques
- RuntimeError: Unable to start Tika server. (après un traceback et un message d'erreur contenant Unable to run java; is it installed?) Ce problème rencontré avec un WSL Ubuntu a été résolu en installant Java. Pour plus de détails, voir https://stackoverflow.com/questions/36478741/installing-oracle-jdk-on-windows-subsystem-for-linux
- Not Implemented Error: Pyperclip could not find a copy/paste mechanism for your system. Ce problème rencontré sous Ubuntu a été résolu en installant un mécanisme de copier/coller. Pour plus de détails, voir https://pyperclip.readthedocs.io/en/latest/introduction.html#not-implemented-error
