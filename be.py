#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import re
#import webbot  # Utile que pour la fonctionnalité abandonnée get_from_web
import pyautogui as gui

from time import time, sleep
from tika import parser

### Variables globales

gui.PAUSE = 0.02  # Temps entre chaque action du mode auto (>=0.02!)

brands = ["carrefour", "auchan", "cora_f", "cora_r", "houra", "picard"]
fullauto = ["carrefour", "auchan", "houra"]

### Parsing

#  Mot qui donne fiablement l'origine de la facture si on le trouve dedans
keyword = {
    "carrefour": "OOSHOP",
    "auchan": "Auchan Direct",
    "cora_f": "Facture coradrive",
    "cora_r": "Récapitulatif de commande coradrive",
    "houra": "www.houra.fr",
    "picard": "SIRET : 78493968805071"
}

#  Emplacement de la date dans le raw parse de la facture
finddate = {
    "carrefour": (lambda s: s[s.find("Date de commande : ")+19:s.find("Date de commande : ")+29]),
    "auchan": (lambda s: s[s.find("FACTURE N° ")+32:s.find("FACTURE N° ")+42]),
    "cora_f": (lambda s: s[s.find(", le ")+5:s.find(", le ")+15]),
    "cora_r": (lambda s: s[s.find("Livraison ")+13:s.find("Livraison ")+23]),
    "houra": (lambda s: s[s.find("Ma commande du ")+15:s.find("Ma commande du ")+25]),
    "picard": (lambda s: s[s.find("DATE : ")+7:s.find("DATE : ")+17])
}

# Indicateurs préliminaire qu'un article commence peut-être à cette ligne
def article_with_code(length, line):
    return len(line) >= length and line[:length].isdigit()

def article_cora_r(line):
    if not line: return False
    if "Qté Remise Total TTC" in line: return False
    if "Récapitulatif" in line: return False
    if "Total articles :" in line: return False
    if "Frais de " in line: return False
    return True

is_article = {
    "carrefour": (lambda line: article_with_code(13, line)),
    "auchan": (lambda line: article_with_code(13, line)),
    "cora_f": (lambda line: line and "Frais de " not in line),
    "cora_r": article_cora_r,
    "picard": (lambda line: article_with_code(6, line))
}

"""
def log_in(brand, web, auth):
    if brand == "houra":
        web.go_to('houra.fr')
        for key,value in auth.items():
            web.type(value , id=key)
        web.press(web.Key.ENTER)
        sleep(1)
        web.press(web.Key.ESCAPE)
    else:
        raise NotImplementedError(brand)
"""

def new_parsing(filename):
    # Pour apprendre à parser des nouvelles marques dont la facture est en pdf
    raw = parser.from_file(filename)
    string = raw['content']
    for line in string.splitlines():
        line = line.split(' ')
        print(line)
    return string

class Article:
    def __init__(self, line, brand, date=None):
        """

        Définit les propriétés d'un article à partir d'une ligne de la
        facture que le parsing a déjà permis de récupérer dans "line":
        self.brand = la marque (string)
        self.sernumber = le code-article présent sur la facture (string)
        self.name = le nom de l'article affiché sur la facture (string)
        self.qty = la quantité livrée (int ou float)
        self.price = le prix unité (float)
        self.TVA = la taux de TVA (%) (float)

        Pour Carrefour un line typique ressemble à :
        ['7613032779566', 'Céréales', '', 'CHOCAPIC', '2', '9.224.612', '5.5']
        s[0] est le code barres, s[-1] la TVA, s[-2] regroupe le prix
        total (9.22), le prix unité (4.61), la quantité commandée (2).
        s[-3] est la quantité livrée : c'est tout ce qui compte pour l'appro.
        Le reste est le nom de l'article.
        Subtilité : des remises peuvent s'insérer entre le 9.22 et le 4.61

        Pour Auchan un line typique ressemble à :
        ['5038862366502', 'Innocent', '3', '3.12', '', '9.36', '5.50', '9.87']
        s[0] est le code barres, s[-1] est le prix total TTC, s[-2] la TVA,
        s[-3] le prix total HT, s[-4] les remises éventuelles, s[-5] le prix
        unitaire HT, s[-6] la quantité livrée.

        Pour Cora (factures) un line typique ressemble à :
        ['Cora', 'camembert', 'au', 'lait', 'pasteurisé', '250', 'g', '1.32', '€', '3', '3', '3.75', '€', '3.96', '€']
        ou pour les articles qui ont un prix au poids :
        ['Citron', 'jaune', '(Origine:', 'Espagne)', '740g', 'à', '2.89', '€/kg', '1.99', '€', '1', '3', '1.89', '€', '1.99', '€']
        s[-5] est un code TVA (3 pour 5.5%, 7 pour 20%)

        Pour Picard un line typique ressemble à :
        ['012949', '300G', 'GIROLLES', '2', '7,95', '€', '15,90', '€', '5,50%']
        ou ['082109', '2', 'VACHERIN', 'VANILLE/FRAMB', '1', 'OFFERT']
        s[0] est un faux code-barres : écrire self.sernumber="-". Tout est TTC.
        Subtilité : certains articles sont offerts, ce qui affecte le parsing.

        Pour découvrir à quoi ressemblent ces lignes parsées pour un nouveau
        magasin, utiliser la fonction new_parsing("nom_facture.pdf")
        Il faut comparer les lignes imprimées à celles de la facture avec
        attention car l'ordre des colonnes de la facture n'est pas conservé !

        Plein de lignes de la facture parsée ne se rapportent pas à un article
        (destinataire, date d'émission de la facture...), il faut aussi savoir
        les ignorer. Utiliser pour ça des assert. AssertionError, ValueError
        et IndexError sont rattrapées par la fonction get_from_file qui est la
        fonction qui crée les instances de Article.

        """
        self.brand = brand
        if brand == "carrefour":
            if date < "20191210":
                self.sernumber = line[0]
                self.name = " ".join(line[1:-3])
                self.qty = int(line[-3])
                stm2 = line[-2][line[-2].index('.')+3:]
                if stm2.count('.') == 2:  # Il y a une remise sur cet article
                    stm2 = stm2[stm2.index('.')+3:]
                self.price = float(stm2[:stm2.index('.')+3])
                self.TVA = float(line[-1])
            else:
                self.sernumber = line[0]
                self.name = " ".join(line[1:-4])
                self.qty = int(line[-4])
                self.price = float(line[-1])
                self.TVA = float(line[-2])
        elif brand == "auchan":
            assert line[0] != "2007984000383"  # Frais de livraison
            self.sernumber = line[0]
            self.name = " ".join(line[1:-6])
            self.qty = int(line[-6])
            self.TVA = float(line[-2])
            self.price = round(float(line[-5]) * (1. + self.TVA*0.01), 2)
        elif brand == "cora_f":
            shift = -2 if line[-6] == "€" else 0
            assert line[-1] == "€" and line[-3] == "€"
            TVAcode = line[-5]
            self.TVA = 5.50 if TVAcode == "3" else 20.00
            if "€/kg" in line:
                i = line.index("€/kg")
                self.name = " ".join(line[:i-3])
                self.price = float(line[i-1])
                qty = line[i-3]
                assert qty.endswith("g")
                if qty.endswith("kg"):
                    self.qty = float(qty[:-2])
                else:
                    self.qty = round(float(qty[:-1])*0.001, 3)
            else:
                self.name = " ".join(line[:-8 + shift])
                self.price = float(line[-8 + shift])
                self.qty = int(line[-6 + shift])
        elif brand == "cora_r":
            shift = -2 if line[-6] == "€" else 0 # remise
            assert line[-1] == "€" and line[-4 + shift] == "€"
            if "€/kg" in line:
                i = line.index("€/kg")
                self.name = " ".join([wrd for wrd in line[:i-3] if wrd])
                self.price = float(line[i-1])
                qty = line[i-3]
                assert qty.endswith("g")
                if qty.endswith("kg"):
                    self.qty = float(qty[:-2])
                else:
                    self.qty = round(float(qty[:-1])*0.001, 3)
            else:
                self.qty = int(line[-3 + shift])
                self.price = float(line[-5 + shift])
                self.name = " ".join([wrd for wrd in line[:-7 + shift] if wrd])
        elif brand == "houra":
            sn = line[line.index('alt="')+5:line.index('" title="')]
            line = line[line.index('<div class="contenant">') + 23:]
            sn += f" ({line[:line.index('<')]})"
            self.sernumber = sn[:13]
            assert self.sernumber.isdigit()
            self.name = sn[16:]
            line = line[line.index('class="prix">') + 13:]
            try:self.price = float(line[:line.index('€')].replace(',', '.'))
            except:self.price = float(line[:line.index('&')].replace(',', '.'))
            line = line[line.index('size="2" maxlength="3" value="') + 30:]
            self.qty = float(line[:line.index('"')].replace(',', '.'))
        elif brand == "picard":
            # line[0] n'est pas le code-barres
            if line[-1] == "OFFERT":
                line[-1:] = ["0,00", "€", "0,00", "€", "0,00%"]
            assert line[-2] == "€" and line[-4] == "€"
            self.name = " ".join([wrd for wrd in line[1:-6] if wrd])
            if ',' in line[-6]:
                self.qty = float(line[-6].replace(',', '.'))
            else:
                self.qty = int(line[-6])
            self.price = float(line[-5].replace(',', '.'))
            self.TVA = float(line[-1][:-1].replace(',', '.'))
        else:
            raise NotImplementedError(brand)
        if brand in fullauto:
            self.ref = self.sernumber
        else:
            self.sernumber = "-"
            self.ref = self.name[:30]

    def __repr__(self):
        return f"{self.sernumber} {self.name} - Qté : {self.qty} - Prix : {self.price}"  # Si cette ligne cause une SyntaxError, c'est que la version de Python utilisée n'est pas >= 3.6 !

def stddate(jjmmaaaa):
    # Récupérer une date qui s'ordonne bien (aaaammjj) à partir de jj/mm/aaaa
    jj = jjmmaaaa[:2]
    mm = jjmmaaaa[3:5]
    aaaa = jjmmaaaa[6:]
    return f"{aaaa}{mm}{jj}"

def get_from_file(filename):
    # Récupérer la date, la marque et tous les articles de la facture filename
    raw = parser.from_file(filename)
    string = raw["content"]
    for br in brands:
        if keyword[br] in string:
            brand = br
            break
    else:
        raise NotImplementedError(filename)
    try:
        date = stddate(finddate[brand](string))
    except:
        raise NotImplementedError(filename)
    articles = []
    lines = string.splitlines()
    i = 0
    while i < len(lines):
        if is_article[brand](lines[i]):
            line = lines[i].split(" ")
            # Seuls les articles cora_r sont sur des lignes consécutives
            tcr = (line[-1] != "€")
            tno = (i+1 < len(lines) and lines[i+1].split(" ") != [''])
            if (brand == "cora_r" and tcr) or (brand != "cora_r" and tno):
                # Certains articles sont sur plusieurs lignes
                while i+1 < len(lines) and lines[i+1].split(" ") != ['']:
                    i += 1
                    line.extend(lines[i].split(" "))
                    # Je ne garantis pas l'exactitude du nom pour Auchan
                    # et Cora qui peuvent écrire des noms sur 2 PAGES
                i += 2 # Ca a l'air spécifique mais en fait non
                if i >= len(lines):
                    break
                line.extend(lines[i].split(" "))
            try:
                articles.append(Article(line, brand, date))
            except (ValueError, IndexError, AssertionError) as e:
                pass
        i += 1
    return date, brand, articles

def get_from_source(string):
    for br in brands:
        if keyword[br] in string:
            brand = br
            break
    else:
        raise NotImplementedError(filename)
    try:
        date = stddate(finddate[brand](string))
    except:
        raise NotImplementedError(filename)
    articles = []
    if brand == "houra":
        for m in re.finditer('<div class="zonePhoto">', string):
            articles.append(Article(string[m.start():m.start()+5000], "houra"))
    else:
        raise NotImplementedError(filename)
    return date, brand, articles

def get_from_sourcefile(filename):
    lines = []
    with open(filename, "r", encoding="utf-8") as f:
        for line in f.readlines(): lines.append(line)
    return get_from_source('\n'.join(lines))

"""
def get_from_web(idPanier): #articles = get_from_web(55006015)
    auth = {'Email': input("Email ? "), 'Pass': input("Mot de passe ? "), "CPClient": "91120"}
    web = webbot.Browser()
    log_in("houra", web, auth)
    web.go_to(f"https://www.houra.fr/cpt/index.php?c=ancienne-commande&idPanier={idPanier}")
    page_source = web.get_page_source()
    web.close_current_tab()
    return get_from_source(page_source)
"""

### Affichages et prise de contrôle du clavier pour loguer, que si appro = True

def alert_start():
    # Prévenir du début imminent de l'appro
    gui.alert("A partir du moment où vous fermerez cette fenêtre, vous aurez 3 secondes pour aller dans le menu appro, scroll en haut, cliquer au milieu de la case du nom d'aliment, en évitant de faire sortir la souris en dehors de la case juste après. Au bout des 3 secondes, l'appro commencera.\nPour rappel, le script s'arrête par mouvement de la souris.", "Début de l'appro")
    sleep(3)

def confirm_end():
    # Prévenir de la fin de la partie automatique de l'appro
    return "OK" == gui.confirm("L'auto-appro est terminée, l'invite de commande peut être fermé.\nLes nouveaux prix ont déjà été changés sur Chocapix, et seront enregistrés dans la base de données du script avec le bouton OK.\nIl reste encore à ajouter manuellement les nouveaux articles. Ils sont listés dans le compte-rendu de l'appro.\nPour annuler les modifications, appuyer sur Annuler.", "Fin de l'auto-appro")

def pause_script(newpos, posref):
    if newpos != posref:
        msg = gui.confirm(text="Pause invoquée par mouvement de la souris\nOK pour continuer l'exécution du script\nCancel pour l'interrompre définitivement.")
        if msg == "OK":
            gui.press('pageup')
            sleep(0.5)
            gui.moveTo(posref[0], posref[1])
            gui.click()
            sleep(0.5)
        else:
            raise KeyboardInterrupt

def show_and_log(article, pricechange=False):
    # Afficher un article dans l'invite de commande, et en fullauto, le loguer
    if article.brand in fullauto:
        print(f"{article.sernumber} - {article.qty}\t{article.name}")
        pos = gui.position()
        gui.typewrite(article.ref)
        pause_script(gui.position(), pos)
        gui.press('return')
        sleep(gui.PAUSE*10)  # Laisser l'overlay arriver
        pause_script(gui.position(), pos)
        gui.click()
        gui.press('tab')
        if pricechange:
            gui.press('tab')
            gui.typewrite(str(article.price).replace('.', ','))
            gui.hotkey('shift', 'tab')
        gui.press('return')
        sleep(gui.PAUSE*5)  # Laisser l'encart rouge partir
        gui.typewrite(str(article.qty).replace('.', ','))
        pause_script(gui.position(), pos)
        gui.click()
        gui.press('esc')
        sleep(gui.PAUSE*10)  # Laisser l'overlay partir
        gui.press('backspace', len(article.ref), gui.PAUSE)
        pause_script(gui.position(), pos)
    else:
        print(f"{article.qty}\t{article.name}")

### Lecture de la facture parsée, mise à jour des prix, compte-rendu

def group_by_sernum(articles):
    # Plusieurs articles d'une facture peuvent concerner un même aliment
    ans = {}
    for article in articles:
        if article.ref in ans:
            ans[article.ref].qty += article.qty
            ans[article.ref].qty = round(ans[article.ref].qty, 3)
        else:
            ans[article.ref] = article
    return list(ans.values())

def update_prices(parsedfile):
    global edit
    date, brand, articles = parsedfile
    if not articles:
        raise NotImplementedError(brand+"0")
    if len(brand) >= 2 and brand[-2] == '_':  # "cora_f", "cora_r"...
        brand = brand[:-2]

    # Récupérer les données de la base de données des prix si elle existe
    codes = {}
    prices = {}
    names = {}
    hidden = set()
    try:
        with open(f"prix_{brand}.txt", "r", encoding="utf-8") as former:
            lines = [line.split() for line in former.readlines()]
            for line in lines:
                wl, code, price = line[:3]
                name = " ".join(line[3:])
                key = code if code != "-" else name[:30]
                prices[key] = float(price)
                names[key] = name
                codes[key] = code
                if wl >= "1":
                    hidden.add(key)
    except:
        pass

    # Scanner tous les articles, les confronter avec la base de données
    if appro and brand in fullauto:
        alert_start()
    newarticles = []
    newprices = []
    articles = group_by_sernum(articles)
    for article in articles:
        if article.qty == 0:
            continue
        if article.ref in prices:
            if article.ref not in hidden:
                former_price = prices[article.ref]
                if appro:
                    show_and_log(article, article.price != former_price)
                if article.price != former_price:
                    newprices.append((former_price, article))
        else:
            newarticles.append(article)
        codes[article.ref] = article.sernumber
        prices[article.ref] = article.price
        names[article.ref] = article.name
    if appro and brand in fullauto and not confirm_end():
        edit = False

    # Lister et créer un compte rendu des changements de prix...
    if not archive:
        with open(f"compte-rendu_{brand}_{date}.txt", "w") as cr:
            cr.write("--- Fichier généré automatiquement ---\n")
            if brand == "houra":
                cr.write("\nRappel : pour Houra, les prix sont donnés à la quantité reçue, jamais au kg ou au L.\n")
            if newprices:
                cr.write("\nEvolutions de prix :\n")
            for (former_price, article) in newprices:
                cr.write(f"{article.name} : évolution de {former_price} à {article.price}\n")
            if newarticles:
                cr.write("\nNouveaux articles :\n")
            for article in newarticles:
                cr.write(f"{article}\n")

    # Réécrire une base de données des prix à la place de l'ancienne
    if edit:
        with open(f"prix_{brand}.txt", "w", encoding="utf-8") as newfile:
            lines = []
            for ref, price in prices.items():
                lines.append(f"{1*(ref in hidden)} {codes[ref]} {price} {names[ref]}\n")
            lines.sort(key=lambda st: st[2:])  # ça sert qu'à aider le débug
            for line in lines:
                newfile.write(line)

### Recueil des arguments donnés dans le shell, gestion des erreurs

if __name__ == "__main__":
    def main():
        global appro, archive, edit
        appro = False
        archive = False
        edit = True

        entrypoint = update_prices
        pdffiles = []
        txtfiles = []
        while len(sys.argv) > 1:
            opt = sys.argv[1]
            if opt.endswith(".pdf"):
                pdffiles.append(opt)
            elif opt.endswith(".txt"):
                if opt.startswith("prix_"):
                    sys.exit("Les noms de la forme prix_xxx.txt sont réservés et ne peuvent pas être donnés en argument. Si c'était le nom du fichier contenant le code-source HTML de la liste des articles achetés, merci de renommer ce fichier.")
                txtfiles.append(opt)
            elif opt == "appro":
                appro = True
            elif opt == "archive":
                archive = True
            elif opt == "noedit":
                edit = False
            elif opt.startswith("pause="):
                gui.PAUSE = float(opt[6:].replace(",", "."))
                if gui.PAUSE < 0.02 or gui.PAUSE > 0.1:
                    sys.exit("Il est recommandé de choisir une pause entre 0.02 et 0.1 seconde.")
            else:
                sys.exit(f"Option \"{sys.argv[1]}\" inconnue.")
            sys.argv.pop(1)
        if appro and archive:
            sys.exit("appro et archive ne peuvent être utilisés en même temps")

        try:
            start_time = time()
            if archive and not pdffiles+txtfiles:
                for filename in os.listdir("archive"):
                    if filename.endswith(".pdf"):
                        pdffiles.append("./archive/"+filename)
                    elif filename.endswith(".txt"):
                        txtfiles.append("./archive/"+filename)
            parsedfiles = [get_from_file(filename) for filename in pdffiles]
            parsedfiles += [get_from_sourcefile(filename) for filename in txtfiles]
            parsedfiles.sort()
            for parsedfile in parsedfiles:
                entrypoint(parsedfile)
            if pdffiles+txtfiles:
                print("\n" + ("Base de données des prix mise à jour. " if edit else "") + ("" if archive else "Ecriture du compte-rendu des évolutions de prix terminée."))
            else:
                print("\nAucune facture n'a été donnée en argument.")
        except KeyboardInterrupt:
            sys.exit("\nScript interrompu définitivement.")
        except FileNotFoundError:
            sys.exit("\nLa facture est introuvable. Il faut qu'elle soit dans le même dossier que be.py. Vérifier le nom exact de la facture.")
        except (KeyError, NotImplementedError) as brand:
            if brand in brands:
                sys.exit(f"\nLa façon de parser les factures de {brand} n'a pas encore été codée.")
            elif brand and brand[:-1] in brands and brand[-1] == "0":
                sys.exit(f"\nAucun article n'a pu être reconnu. Il semble que {brand[:-1]} a légèrement modifié la forme de ses factures.")
            else:
                sys.exit(f"\nLa marque de {brand} n'a pas pu être reconnue. Il peut s'agir d'une nouvelle marque (parsing pas encore implémenté) ou alors la forme de la facture a beaucoup changé (parsing à refaire).")
        finally:
            end_time = time()
            print(f"\nTemps écoulé : {end_time-start_time} secondes.")
        #sys.exit(0)

    main()
