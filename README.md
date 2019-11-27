# Mode d'emploi

# Qu'est-ce que c'est

Le script présenté ici a deux fonctions :
1) Suivre l'évolution des prix de supermarché au moment du loggage d'une nouvelle appro en créant un fichier récapitulant ces changements, de façon à pouvoir informer la section de ces changements de prix sans que le respo appro n'ait à y consacrer son temps et son énergie.
2) Optimiser la productivité du respo appro dans le loggage pour accélérer cette opération fastidieuse et répétitive, en lui retirant la charge de la plupart des actions (allers-retours de la souris entre facture et Chocapix, interruptions régulières par les nouveaux aliments qui mettent plus de temps à logguer, vérification au cas par cas des changements de prix des aliments) qu'il a toujours dû faire pour logguer une appro.

Toutefois, ce script n'a pas pour vocation :
1) De remplacer le respo appro. Le script n'est pas capable d'effectuer tout seul l'appro, certaines actions restent à la charge du respo appro.
2) D'aider dans les inventaires. Cette tâche n'a rien à voir avec ce qui est pris en charge par ce script.

# Prérequis

Le script a été testé avec succès sur Windows 10, MacOS, Ubuntu, et un WSL Ubuntu. Rien n'est garanti pour d'autres systèmes d'exploitation.

Pour logguer une appro avec ce script il faut au préalable avoir la facture PDF originale (pas un scan) et un interpréteur Python 3.6 ou plus récent. Il sera aussi utile d'avoir le plus de factures possible venant des anciennes appros. Renommer éventuellement les factures pour qu'il n'y ait pas d'espaces dans leurs noms. Télécharger le fichier be.py et le ranger dans un dossier qui contiendra aussi les factures. Créer un sous-dossier, l'appeler "archive", et y ranger toutes les factures qui ont déjà été logguées par le passé.

Il faudra éventuellement installer les modules Python suivants, s'ils provoquent des erreurs d'imports : time, tika, sys et pyperclip ; sur Windows seulement : msvcrt ; sur les autres OS seulement : termios, atexit et select
  
Pour installer un module Python, il faut taper dans un invite de commande :

pip install nom_du_module

Ou plus simplement, si votre interpréteur est anaconda, taper directement dans un shell Python :

\>\>\> conda install nom_du_module

Si cela ne marche pas, c'est probablement que la version utilisée de Python est antérieure à 3.4 ou que plusieurs versions de Python sont installées. Dans tous les cas, https://docs.python.org/3/installing/index.html est une ressource utile.

L'exécution du script peut provoquer quelques bugs plus exotiques, certains sont décrits dans la dernière section du README.


# Utilisation pour la première fois

Ouvrir un invite de commande dans le dossier qui contient le fichier Python, le dossier archive et éventuellement les factures pas encore logguées.

Taper dans l'invite de commande :

python be.py archive
  
Si un message contenant "[MainThread  ] [WARNI]  Failed to see startup log message; retrying..." s'affiche, l'ignorer, ça devrait terminer au bout de quelques secondes.

A l'issue, s'il n'y a pas d'appro à faire tout de suite, l'invite de commande peut être fermé. Un fichier du nom de "prix_marque.txt" a été ajouté pour chaque marque représentée par au moins une facture (Carrefour, Picard...) : il fait office de base de données des prix pour cette marque, et le script l'utilise pour comparer les prix des futures appros. Il est à ne pas modifier ni supprimer. En revanche il est à votre charge de le copier quelque part (en faire une sauvegarde) pour vous prémunir d'une utilisation erronée du script qui viendrait à modifier de manière non souhaitée ce fichier.

_Dans des versions précédentes, il fallait lancer la commande une fois pour chaque ancienne facture et veiller à faire cela dans l'ordre chronologique des factures. Il fallait aussi fournir en argument le nom du supermarché d'où venait chaque facture. Aujourd'hui, le script détecte tout seul la marque et la date, c'est pourquoi il suffit de tout mettre dans un dossier "archive". Le script triera tout seul les factures par date pour avoir dans la base de données finale les prix les plus actuels de chaque aliment._

# Utilisation pour une appro

Lire toute la section avant de commencer à effectuer les opérations décrites.

Ouvrir un invite de commande dans le dossier qui contient le fichier Python et la facture. Ouvrir Chocapix. Diviser l'écran en mosaïque de façon à voir à la fois l'invite de commande (pas besoin de plus d'un tiers de l'écran) et Chocapix. Etre prêt à logguer l'appro en s'assurant que la case pour rentrer le code du premier aliment et la case pour la quantité sont à portée de souris.

Pour lancer le script sur une facture qui s'appelle "facture.pdf", taper :

python be.py facture.pdf appro

Si un message contenant "[MainThread  ] [WARNI]  Failed to see startup log message; retrying..." s'affiche, l'ignorer.

Quelques instants après le lancement de la commande et juste après un compte à rebours, des nombres vont commencer à s'afficher dans l'invite de commande. Au bout de quelques secondes, cela peut ressembler à :

X:\Chemin\Du\Dossier> python be.py 06.11_facture.pdf appro

Début dans 3 . 2 . 1 .

3245390089854 2

3270190007050 2

3276650121533 
  
Chaque nouveau nombre qui s'affiche dans cet invite de commande, correspond à un code ou une quantité d'un aliment déjà rencontré dans l'archive de factures (pas besoin de créer une nouvelle fiche d'aliment, donc).

Il n'y a pas besoin de le copier, c'est fait automatiquement par le script : il ne reste plus qu'à coller chaque nombre dans la bonne case de Chocapix. Il faut simplement le faire avant que le prochain nombre s'affiche, sinon ce nouveau nombre prend sa place dans le presse-papier. De cette manière, avec un ordinateur à souris, la main gauche reste constamment au dessus de Ctrl et V, et la main droite contrôle une souris dont le pointeur ne sort jamais de Chocapix.

Que faire si je rate un ou plusieurs nombres ? Pas de panique, le script peut être mis en pause en tapant n'importe quelle lettre de l'alphabet dans l'invite de commande. Cela doit vous laisser autant de temps que nécessaire pour récupérer le nombre manqué, le copier coller manuellement vers Chocapix. Quand le retard est rattrapé, appuyer sur Entrer dans l'invite de commande et le script continue. Cela peut ressembler à :

D:\Alexandre\Chocapix> python be.py 06.11_facture.pdf appro

2019-11-24 14:45:23,856 [MainThread  ] [WARNI]  Failed to see startup log message; retrying...

Début dans 3 . 2 . 1 .

3245390089854 2

3270190007050 2

3276650121533 1

5601019001030                 // <- Les nombres affichés ne sont pas effacés au fur et à mesure.

Script mis en pause. Appuyer sur Entrer pour le poursuivre. // Cela permet de copier coller à la main ce qu'on a manqué

g                             // <- la lettre tapée pour mettre en pause le script peut s'afficher. Cela n'a aucune importance.

Début dans 3 . 2 . 1 .

 1                            // <- Aucun nombre ne sera affiché deux fois, ce 1 correspond donc au code barre 5601019001030

3166291458405 1

...
 
Par défaut le temps donné pour coller un nombre avant que le prochain prenne sa place est :

- 1.5 seconde après un numéro de série (puisqu'il suffit de coller et déplacer la souris vers la quantité)

- 4 secondes après une quantité (parce que cette fois il faut coller puis ouvrir une nouvelle fiche de loggage)

Pour changer ces temps de manière ponctuelle pour une seule appro, on pourra à la place de la commande vue plus haut écrire :

python be.py 06.11_facture.pdf appro set_pause x y

Où x et y (entiers ou à virgule) remplaceront respectivement le 1.5 et le 4. Choisissez les temps idéaux pour terminer l'appro le plus rapidement possible sans avoir à pauser régulièrement le script. 

_Ces paramètres peuvent aussi être changés définitivement en modifiant le code du fichier Python : les deux valeurs y sont définies dans les premières lignes après les imports de modules._

A la fin de cette première phase, le script affiche dans l'invite de commandes une liste d'articles dont le prix a changé. Ces articles ont déjà été loggués, il suffit de modifier leur prix manuellement.

Enfin, le script affiche dans l'invite de commandes la liste des nouveaux articles, jamais rencontrés. Par "jamais rencontré" il faut comprendre "jamais rencontré par le script". En effet si la section "Usage pour la première fois" n'a pas été suivie ou si des factures sont manquantes, le script peut ne pas connaître un article qui a bien été loggué dans Chocapix il y a longtemps. Dans ce cas, il n'a pas été cité plus haut par le script et il va falloir le logguer à la main maintenant.

C'est terminé. L'invite de commande peut être fermé. A l'issue de l'appro, un compte-rendu au format .txt est créé, listant tous les changements de prix. Il n'y a aucun danger à modifier ou supprimer ce compte-rendu, sa vocation est purement informative. Il peut par exemple être recopié dans l'onglet des nouvelles par le respo news afin d'informer les membres de sa section sur les bonnes ou mauvaises surprises qui peuvent les attendre en logguant leurs aliments préférés.

# Utilisation non attendue du script
Plusieurs utilisations qui ne rentrent dans aucun des deux cadres cités plus haut (mise à niveau avec l'archive, et appro) peuvent être faites de ce script. Fidèle à la philisophie de Python, "we are all consenting adults here", la plupart de ces cas de figure ne mènent pas à une erreur et peuvent être explorés par un utilisateur curieux. En voici quelques exemples.

Pour lancer le script en mode appro sur une facture qui se trouve dans le dossier archive, il suffit de faire précéder le nom de la facture par "./archive/", comme on pourrait s'y attendre. Rien n'empêche non plus de chercher des fichiers .pdf qui sont en dehors du dossier contenant le script. Il reste donc possible de lancer le script sur une vieille facture, ce qui aura pour conséquence probable de remplacer des prix actuels dans les bases de données de prix par des valeurs dépassées. Aussi, l'éventuel compte-rendu créé n'aura aucun sens puisqu'il montrera les "évolutions" de prix de cette remontée dans le temps. A utiliser avec modération, donc. Pour faire rentrer les choses dans l'ordre, on peut lancer le script sur toutes les factures de la même marque entre celle-là et la plus récente dans l'ordre chronologique, ce qui peut être fait avec la seule commande "python be.py archive".

On peut reproduire le comportement du mode appro sans avoir à attendre l'affichage des numéros de série et quantités grâce à "set_pause 0 0". Cela peut être utile pour du débug.

Il est possible de surveiller les évolutions de prix et de produire un compte-rendu en dehors du mode appro. Il suffit pour cela de ne fournir aucun des deux mots-clés appro ou archive. Ainsi, au lieu de suivre le paragraphe "Utilisation pour la première fois" à la lettre, on pourra ne mettre dans le dossier archive que les factures de plus d'un mois, et après avoir tapé "python be.py archive", on pourra appeler "python be.py facture.pdf" pour toutes ces factures passées mais récentes, que l'on n'a pas mises dans le dossier archive, et le script produira alors tous les compte-rendus des appros récentes. Le script triera ici aussi les factures par date avant de calculer les évolutions.

Il est même possible de simplement surveiller les évolutions de prix sur une facture en particulier sans compte-rendu ni appro. Pour ça, il faut utiliser le mot-clé "archive" et écrire le nom de la facture. Dans le code du script, le mot-clé archive vérifie d'abord si une facture a été donnée en argument et sinon traite toutes les factures du dossier archive.

Dans le mode appro, donner en argument le nom de la facture sert à dire au script quel fichier regarder pour mettre à jour sa base de données des prix. Le mode archive ne fait que lancer la fonction principale du script en retirant le baratin de l'appro, sur la facture donnée en argument, ou à défaut sur la liste de toutes les factures du dossier "archive". Suivant ce principe, il est possible de donner en arguments plusieurs factures à la fois. Elles seront alors toutes traitées les unes à la suite des autres.

Attention à ne pas renommer le dossier "archive" en autre chose et espérer que remplacer le mot-clé "archive" par le nouveau nom de dossier suffira. Le mot-clé n'est pas nommé d'après le dossier, et le nom du dossier que le script tentera d'explorer est hard-codé comme devant être "archive".

Appuyer sur Ctrl+C dans l'invite de commande arrête totalement le script. Mais comme les changements de prix ne sont enregistrés dans une base de donnée qu'au dernier moment à la fin de l'exécution du script, ces changements ne seront pas encore enregistrés au moment du Ctrl+C fautif. Il n'est donc pas primordial de finir sur le champ le loggage de l'appro quand elle a été commencée. De même, si Chocapix plante en plein milieu de l'appro, on peut sans crainte relancer le script après un Ctrl+C, les changements de prix seront encore signalés et les nouveaux articles seront encore considérés nouveaux. L'arrêt par Ctrl+C ne se produit que si aucun texte n'est sélectionné : cela ne concerne donc pas le fait de copier manuellement un nombre pendant une pause du script.

Utiliser le script en mode appro sur un magasin qui ne donne pas les codes-barres de ses aliments dans la facture fait perdre au script un de ses deux intérêts. Par exemple Picard utilise dans ses factures des codes d'article qui ne correspondent pas au code-barre. Si Chocapix a été renseigné avec le code-barre, le script ne peut pas aider à faire les appros. C'est réparable uniquement en modifiant à la main tous les codes-barres Picard retenus par Chocapix pour les remplacer par les codes de la facture. En attendant, le script ne sera bon qu'à faire ses compte-rendus d'évolution de prix. Il est toujours possible d'écrire le mot-clé "appro" avec ces marques mais le script l'ignorera.

# Quelques messages d'erreur exotiques
- RuntimeError: Unable to start Tika server. (après un traceback et un message d'erreur contenant Unable to run java; is it installed?) Ce problème rencontré avec un WSL Ubuntu a été résolu en installant Java. Pour plus de détails, voir https://stackoverflow.com/questions/36478741/installing-oracle-jdk-on-windows-subsystem-for-linux
- Not Implemented Error: Pyperclip could not find a copy/paste mechanism for your system. Ce problème rencontré sous Ubuntu a été résolu en installant un mécanisme de copier/coller. Pour plus de détails, voir https://pyperclip.readthedocs.io/en/latest/introduction.html#not-implemented-error
