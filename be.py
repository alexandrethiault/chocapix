#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import pyautogui

from tika import parser
from time import time, sleep

### Variables globales

pyautogui.PAUSE = 0.2  #0.05  # Temps entre chaque action du mode full auto

brands = ["carrefour", "auchan", "cora_f", "cora_r", "houra", "picard"]
fullauto = ["carrefour", "auchan"]

### Parsing

#  Mot qui donne fiablement l'origine de la facture si on le trouve dedans
keyword = {
    "carrefour": "OOSHOP",
    "auchan": "Auchan Direct",
    "cora_f": "Facture coradrive",
    "cora_r": "Récapitulatif de commande coradrive",
    "houra": "client@houra.fr",
    "picard": "SIRET : 78493968805071"
}

#  Emplacement de la date dans le raw parse de la facture
finddate = {
    "carrefour": (lambda s: s[s.find("Date de commande : ")+19:s.find("Date de commande : ")+29]),
    "auchan": (lambda s: s[s.find("FACTURE N° ")+32:s.find("FACTURE N° ")+42]),
    "cora_f": (lambda s: s[s.find(", le ")+5:s.find(", le ")+15]),
    "cora_r": (lambda s: s[s.find("Livraison ")+13:s.find("Livraison ")+23]),
    "houra": (lambda s: s[s.find("Réf. ")-12:s.find("Réf. ")-2]),
    "picard": (lambda s: s[s.find("DATE : ")+7:s.find("DATE : ")+17])
}

#  Indicateur (pas forcément 100% fiable) qu'un article commence à cette ligne
def article_with_code(length, line):
    return len(line) >= length and line[:length].isdigit()

def article_cora_f(line):
    if not line: return False
    if "Frais de " in line: return False
    if "Code TVA" in line: return False
    if "3 5.50 % " in line: return False
    if "7 20.00 % " in line: return False
    if "Cora - Siège Social" in line: return False
    return True

def article_cora_r(line):
    if not line: return False
    if "Qté Remise Total TTC" in line: return False
    if "Récapitulatif" in line: return False
    if "Total articles :" in line: return False
    return article_cora_f(line)

is_article = {
    "carrefour": (lambda line: article_with_code(13, line)),
    "auchan": (lambda line: article_with_code(13, line)),
    "cora_f": article_cora_f,
    "cora_r": article_cora_r,
    "houra": (lambda line: line.isdigit() or " " in line and line[:line.index(" ")].isdigit()),
    "picard": (lambda line: article_with_code(6, line))
}

def new_parsing(filename):
    # Pour apprendre à parser des nouvelles marques
    raw = parser.from_file(filename)
    string = raw['content']
    for line in string.splitlines():
        line = line.split(' ')
        print(line)
    return string

class Article:
    def __init__(self, line, brand):
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
        les ignorer. L'exception à utiliser est ValueError. Cette exception et
        IndexError sont rattrapées par la fonction get_from_file qui est la
        fonction qui crée les instances de Article.

        """
        self.brand = brand
        if brand == "carrefour":
            self.sernumber = line[0]
            self.name = " ".join(line[1:-3])
            self.qty = int(line[-3])
            stm2 = line[-2][line[-2].index('.')+3:]
            if stm2.count('.') == 2:  # Il y a une remise sur cet article
                stm2 = stm2[stm2.index('.')+3:]
            self.price = float(stm2[:stm2.index('.')+3])
            self.TVA = float(line[-1])
            self.ref = self.sernumber
        elif brand == "auchan":
            if line[0] == "2007984000383":
                raise ValueError # '2007984000383' est le frais de livraison
            self.sernumber = line[0]
            self.name = " ".join(line[1:-6])
            self.qty = int(line[-6])
            self.TVA = float(line[-2])
            self.price = round(float(line[-5]) * (1. + self.TVA*0.01), 2)
            self.ref = self.sernumber
        elif brand == "cora_f":
            if line[-1] != "€" or line[-3] != "€":
                raise ValueError
            TVAcode = line[-5]
            if TVAcode == "3":
                self.TVA = 5.50
            else:
                self.TVA = 20.00
            if "€/kg" in line:
                i = line.index("€/kg")
                self.name = " ".join(line[:i-3])
                self.price = float(line[i-1])
                qty = line[i-3]
                if "kg" in qty:
                    self.qty = float(qty[:-2])
                elif "g" in qty:
                    self.qty = round(float(qty[:-1])*0.001, 3)
                else:
                    raise ValueError
            else:
                shift = -2 if line[-6] == "€" else 0
                self.name = " ".join(line[:-8 + shift])
                self.price = float(line[-8 + shift])
                self.qty = int(line[-6 + shift])
            self.ref = self.name
        elif brand == "cora_r":
            shift = -2 if line[-6] == "€" else 0 # remise
            if line[-1] != "€" or line[-4 + shift] != "€":
                raise ValueError
            if "€/kg" in line:
                i = line.index("€/kg")
                self.name = " ".join([wrd for wrd in line[:i-3] if wrd])
                self.price = float(line[i-1])
                qty = line[i-3]
                if "kg" in qty:
                    self.qty = float(qty[:-2])
                elif "g" in qty:
                    self.qty = round(float(qty[:-1])*0.001, 3)
                else:
                    raise ValueError
            else:
                self.qty = int(line[-3 + shift])
                self.price = float(line[-5 + shift])
                self.name = " ".join([wrd for wrd in line[:-7 + shift] if wrd])
            self.ref = self.name
        elif brand == "houra":
            if "Echantillon Offert" in " ".join(line):
                raise ValueError
            # line[0] n'est pas le code-barres
            self.name = " ".join([wrd for wrd in line[1:-5] if wrd])
            if ',' in line[-5]:
                self.qty = float(line[-5].replace(',', '.'))
            else:
                self.qty = int(line[-5])
            self.price = float(line[-2].replace(',', '.'))
            self.TVA = float(line[-3].replace(',', '.'))
            self.ref = self.name
        elif brand == "picard":
            # line[0] n'est pas le code-barres
            if line[-1] == "OFFERT":
                line[-1:] = ["0,00", "€", "0,00", "€", "0,00%"]
            if line[-2] != "€" or line[-4] != "€":
                raise ValueError
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
            self.ref = self.name

    def __repr__(self):
        return f"{self.sernumber} {self.name} - Qté : {self.qty} - Prix : {self.price}"

def stddate(jjmmaaaa):
    # Récupérer une date qui s'ordonne bien (aaaammjj) à partir de jj/mm/aaaa
    jj = jjmmaaaa[:2]
    mm = jjmmaaaa[3:5]
    aaaa = jjmmaaaa[6:]
    return f"{aaaa}{mm}{jj}"

def get_from_file(filename):
    # Récupérer la date, la marque et tous les articles de la facture filename
    raw = parser.from_file(filename)
    string = raw['content']
    for br in brands:
        if keyword[br] in string:
            brand = br
            break
    else:
        raise NotImplementedError("")
    try:
        date = stddate(finddate[brand](string))
    except:
        raise NotImplementedError("")
    articles = []
    lines = string.splitlines()
    if brand in ["cora_r"]:
        # Les articles sont sur des lignes consécutives. Si un article prend
        # plusieurs lignes, il y a un saut de ligne avant et après les prix,
        # sinon tout est sur une ligne et il n'y a pas de saut avant la suite.
        phase_articles = False
        i = 0
        while i < len(lines):
            if is_article[brand](lines[i]):
                line = lines[i].split(' ')
                if line[-1] != "€":
                    while i+1 < len(lines) and lines[i+1].split(' ') != ['']:
                        i += 1
                        line.extend(lines[i].split(' '))
                    i += 2 # Ca a l'air spécifique mais en fait non
                    if i >= len(lines):
                        break
                    line.extend(lines[i].split(' '))
                try:
                    articles.append(Article(line, brand))
                except (ValueError, IndexError) as e:
                    pass
            i += 1
    else:
        i = 0
        while i < len(lines):
            if is_article[brand](lines[i]):
                line = lines[i].split(' ')
                if i+1 < len(lines) and lines[i+1].split(' ') != ['']:
                    # Certains articles sont sur plusieurs lignes
                    while i+1 < len(lines) and lines[i+1].split(' ') != ['']:
                        i += 1
                        line.extend(lines[i].split(' '))
                        # Je ne garantis pas l'exactitude du nom pour Auchan
                        # Ces fdp peuvent écrire des articles sur 2 PAGES
                    i += 2 # Ca a l'air spécifique mais en fait non
                    if i >= len(lines):
                        break
                    line.extend(lines[i].split(' '))
                try:
                    articles.append(Article(line, brand))
                except (ValueError, IndexError) as e:
                    pass
            i += 1
    return date, brand, articles

### Affichages et prise de contrôle du clavier pour loguer, que si appro = True

def preparation():
    # Prévenir du début imminent de l'appro
    # Afficher dans l'invite de commande "Début dans 3...2...1..."
    pyautogui.alert("A partir du moment où vous fermerez cette fenêtre, vous aurez 3 secondes pour cliquer dans la case du nom d'aliment dans le menu appro, et l'appro commencera.", "Début de l'appro")
    print("\nDébut dans ", end="", flush=True)
    for i in range(12):
        print(3-i//4 if i % 4 == 0 else ".", end="", flush=True)
        sleep(0.25)
    print()

def show_and_log(article, pricechange=False):
    # Afficher un article dans l'invite de commande, et en fullauto, le loguer
    if article.brand in fullauto:
        print(f"{article.sernumber} - {article.qty}\t{article.name}")
        pos = pyautogui.position()
        pyautogui.typewrite(article.ref)
        pyautogui.doubleClick()
        pyautogui.press('return')
        pyautogui.press('tab')
        if pricechange:
            pyautogui.press('tab')
            pyautogui.typewrite(str(article.price).replace('.', ','))
            pyautogui.hotkey('shift', 'tab')
        pyautogui.typewrite(str(article.qty).replace('.', ','))
        pyautogui.hotkey('shift', 'tab')
        pyautogui.press('esc')
        pyautogui.press('backspace')
        if pyautogui.position() != pos:
            msg = pyautogui.confirm(text="Pause invoquée par mouvement de la souris\nOK pour continuer l'exécution du script\nCancel pour l'interrompre définitivement.")
            if msg == "OK":
                sleep(0.5)
                pyautogui.moveTo(pos[0], pos[1])
            else:
                raise KeyboardInterrupt
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
    date, brand, articles = parsedfile
    if brand[-2] == '_':  # "cora_f", "cora_r"...
        brand = brand[:-2]

    # Récupérer les données de la base de données des prix si elle existe
    global prices, hidden
    codes = {}
    prices = {}
    names = {}
    hidden = set()
    try:
        with open(f"prix_{brand}.txt", 'r') as former:
            lines = [line.split() for line in former.readlines()]
            for line in lines:
                wl, code, value = line[:3]
                name = " ".join(line[3:])
                key = code if code != "-" else name
                prices[key] = float(value)
                names[key] = name
                codes[key] = code
                if wl == "1":
                    hidden.add(key)
    except:
        pass

    # Scanner tous les articles, les confronter avec la base de données
    if appro and brand in fullauto:
        preparation(brand in fullauto)
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

    # Lister et créer un compte rendu des changements de prix...
    if not archive:
        with open(f"compte-rendu_{brand}_{date}.txt", 'w') as cr:
            if newprices:
                print("\nEvolutions de prix :")
            for (former_price, article) in newprices:
                print(f"{article.name} : évolution de {former_price} à {article.price}")
                cr.write(f"{article.name} : évolution de {former_price} à {article.price}\n")
        if appro:  # ... et lister les nouveaux articles
            if newarticles:
                print("\nNouveaux articles :")
            for article in newarticles:
                print(article)
    # Réécrire une base de données des prix à la place de l'ancienne
    with open(f"prix_{brand}.txt", 'w') as newfile:
        lines = []
        for key, value in prices.items():
            lines.append(f"{1*(key in hidden)} {codes[key]} {value} {names[key]}\n")
        lines.sort(key=lambda st: st[2:])  # ça sert qu'à aider le débug
        for line in lines:
            newfile.write(line)

### Recueil des arguments donnés dans le shell, gestion des erreurs

if __name__ == "__main__":
    def main():
        global appro, archive
        appro = False
        archive = False
        entrypoint = update_prices
        files = []
        while len(sys.argv) > 1:
            opt = sys.argv[1]
            if opt.endswith(".pdf"):
                files.append(opt)
            elif opt == "appro":
                appro = True
            elif opt == "archive":
                archive = True
            else:
                print(f"Option inconnue \"{sys.argv[1]}\".")
                sys.exit(1)
            sys.argv.pop(1)
        if appro and archive:
            print("Les mots-clé appro et archive ne peuvent être utilisés en même temps")
            sys.exit(1)

        start_time = time()
        try:
            if archive and not files:
                for filename in os.listdir("archive"):
                    if filename.endswith(".pdf"):
                        files.append("./archive/"+filename)
            parsedfiles = [get_from_file(filename) for filename in files]
            parsedfiles.sort()
            for parsedfile in parsedfiles:
                entrypoint(parsedfile)
            print("\nBase de données des prix mise à jour." + ("" if archive else " Ecriture du compte-rendu des évolutions de prix terminée."))
        except KeyboardInterrupt:
            print("\nScript interrompu définitivement.")
        except UnboundLocalError:
            print("\nMauvaise syntaxe. Exemples de syntaxe :\npython be.py archive\npython be.py 21.10_facture.pdf appro set_pause 1.25 3 0.5 5")
        except FileNotFoundError:
            print("\nLa facture est introuvable. Il faut qu'elle soit dans le même dossier que le script. Vérifier le nom exact de la facture.")
        except (KeyError, NotImplementedError) as brand:
            if brand in brands:
                print(f"\nLa façon de parser les factures de {brand} n'a pas encore été codée.")
            else:
                print(f"\nLa marque n'a pas pu être reconnue. Il peut s'agir d'une nouvelle marque (parsing pas encore implémenté) ou alors la forme de la facture a changé (parsing à refaire).")
        end_time = time()

        print(f"\nTemps écoulé : {end_time-start_time} secondes\n")

    main()
