# Mode d'emploi

# Qu'est-ce que c'est

Le script présenté ici a pour fonction d'automatiser tout le processus de loggage d'appro, à l'exception du loggage de nouveaux aliments, qui nécessite la création à la main d'une nouvelle fiche d'aliment.

Toutefois, ce script n'a pas pour vocation :
1) De faciliter le changement d'approvisionneur pour une section. Le script n'est d'aucune aide pour le loggage des nouveaux aliments, si ce n'est de prévenir à l'avance quels articles sont nouveaux et quels articles ont déjà été commandés.
2) D'aider dans les inventaires, et en particulier la vérification que les quantités livrées sont bien les quantités écrites sur les factures. Ce script est dédié uniquement au loggage des appros, et vouloir faire l'inventaire en même temps que l'appro va contre le principe de ce script, qui demande de séparer ces deux tâches.

# Prérequis

Avant tout, le script utilise les codes-barres pour logger les aliments. Une section qui aurait pris l'habitude pendant plusieurs mois de logger les aliments à partir de leurs noms au lieu de leurs codes-barres ne peut pas profiter de ce script sans un re-loggage de tous les aliments déjà connus, cette fois à partir des codes-barres.

Le script est prévu pour être compatible avec tous les systèmes d'exploitation, pourvu qu'ils supportent Python 3 et les modules utilisés par ce script (voir suite de la section). 

Pour logger une appro avec ce script, il faut selon les marques (voir détail plus bas) avoir la facture PDF originale et/ou un fichier .html contenant le code-source HTML de la page web contenant la liste des aliments achetés. Dans le reste du README, on fera référence à ces deux types de documents sous le même nom "facture".

Note à propos des factures HTML : dans tous les navigateurs, le code-source HTML d'une page s'ouvre en appuyant sur Ctrl+U sur PC et Cmd+U ou Option+Cmd+U selon le navigateur sur Mac (Pro-tip : Ctrl+A puis Ctrl+C ou Cmd+A puis Cmd+C est une bonne façon de copier tout le code-source rapidement. Certains navigateurs permettent aussi de construire un fichier html du code source directement avec Ctrl+S). 

Pour l'instant les marques suivantes sont prises en charge :
- Carrefour (facture .pdf)
- Auchan (factures .pdf)
- Houra (code-source HTML de https://www.houra.fr/cpt/index.php?c=ancienne-commande&idPanier=xxxxxxxx ou https://www.houra.fr/cpt/index.php?c=listefromcmd&s=c_1 ET facture pdf disponible sur https://www.houra.fr/cpt/index.php?c=anciennes-commandes )

Cora et Picard ne sont pas pris en charge car il n'y a pas de codes-barres dans leurs factures. Comme les noms connus par Chocapix ne correspondent pas exactement aux noms des articles dans les factures, la première suggestion de Chocapix peut ne pas être la bonne, donc le script ne peut vraiment rien remplir pour la case du nom de l'article.

Télécharger les fichiers `be.py` et `requirements.txt`.

Pour exécuter ce script il faut au préalable un interpréteur Python 3.6 ou plus récent. Il a besoin des modules `tika 1.19`  et `selenium` (et `msedge.selenium_tools` pour les utilisateurs de Windows), qui peuvent être installés avec la commande

`pip install -r requirements.txt`

Après ceci, `requirements.txt` peut être supprimé.

Le module `tika` qui extrait le contenu des pdf, a besoin de Java pour fonctionner. Dans le cas de Windows, ça signifie donc notamment d'ajouter le dossier bin de Java au PATH si ça n'a pas déjà été fait en INF361/371.

Les auto-appros sont effectuées par un navigateur robot ouvert par le script. Firefox, Opera, Edge pour Windows 10, et Chrome sont supportés : il faut avoir au moins l'un de ces navigateurs et avoir téléchargé le driver adapté. Par défaut les utilisateurs de Windows n'ont rien à préparer, un navigateur Edge sera piloté par un driver téléchargé automatiquement par le script. Pour les autres OS, et les utilisateurs de Windows qui ont désinstallé ou n'aiment pas Edge, il faut télécharger manuellement le driver adapté à votre navigateur préféré parmi Firefox, Opera, Chrome. Voir https://github.com/mozilla/geckodriver/releases pour Firefox, sinon https://github.com/operasoftware/operachromiumdriver/releases pour Opera, sinon https://chromedriver.chromium.org/downloads pour Chrome. Placer le driver téléchargé (`geckodriver.exe`, `operadriver.exe` ou `chromedriver.exe`) dans un dossier nommé `driver`.

# Utilisation

Ouvrir une invite de commande dans le dossier qui contient le fichier Python et la facture.

Pour lancer le script sur une facture qui s'appelle `facture.pdf` (resp. un dossier `dir` contenant les deux types de factures pour Houra), taper :

`python be.py facture.pdf`          (resp. `python be.py dir`)

Après s'être connecté au serveur de tika pour parser les PDF, le script va tenter de récupérer vos identifiants pour se connecter à chocapix. Pour cela, il y a deux façons. Dans la façon manuelle, il faut retaper son nom d'utilisateur et son mot de passe dans l'invite de commande à chaque utilisation du script. Dans la façon automatique, le script va chercher si un fichier `login.txt` existe et interprétera le texte écrit dedans comme le nom d'utilisateur puis le mot de passe, à séparer par un espace.

Après cette connexion, il faut laisser le script remplir automatiquement les codes-barres, quantités, et prix. En cas de problème, il est toujours possible d'interrompre le script en fermant le navigateur robot ou avec `Ctrl+C` dans l'invite de commande.

A l'issue de cette phase de remplissage automatique, taper `y` pour valider l'auto-appro du côté du script. L'invite de commande peut alors être fermée mais l'appro n'est pas encore validée sur chocapix. Vous devez encore cliquer sur le bouton de validation dans le navigateur robot avant de le fermer.

Un compte-rendu au format .txt est créé, listant tous les changements de prix, ainsi que les articles achetés pour la première fois. Dans ce cas, il n'a pas été loggé plus tôt par le script et il va falloir le logger à la main maintenant. La liste des changements de prix est purement informative puisque les prix sont déjà changés dans chocapix.

Le script crée également une liste des articles qu'il a rencontré, dans un fichier appelé `prix_\[marque\].txt`, par exemple `prix_carrefour.txt`. Cela sert au script à éviter de régulièrement donner les mêmes aliments non loggables dans la liste des nouveaux aliments. Il n'y a rien à faire à la main, le script décide lui-même des aliments non-loggables selon le critère suivant : si un article est inconnu de chocapix mais qu'il a déjà été rencontré par le script, c'est que le respo appro a délibérément choisi de ne pas l'ajouter à chocapix, et donc qu'il n'est pas loggable.

# Fonctionnalités futures envisagées

- Prise en charge web de Carrefour
