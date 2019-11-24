#! /usr/bin/env python
# -*- coding: utf-8 -*-

from tika import parser
from time import time, sleep

import sys
import pyperclip
import os

if os.name == 'nt':
    import msvcrt
else:
    import termios
    import atexit
    from select import select

after_series_number = 1 #temps donné pour coller le numéro de série (sec)
after_quantity = 4 #et pour coller la quantité puis changer d'aliment

appro = False # valeur par défaut, ne pas modifier ici
archive = False # valeur par défaut, ne pas modifier ici

brands = ["carrefour", "picard", "efiester"]
pasdappro = ["picard"]

## Parsing

class Article:
    def __init__(self, string, brand):
        self.brand = brand
        if brand == "carrefour":
            if len(string[0]) != 13:
                raise ValueError
            self.sernumber = int(string[0])
            self.name = " ".join(string[1:-3])
            self.qty = int(string[-3])
            stm2 = string[-2][string[-2].index('.')+3:]
            if stm2[:4] == "0.00":
                stm2 = stm2[4:]
            self.price = float(stm2[:stm2.index('.')+3])
            self.TVA = float(string[-1])
        elif brand == "picard":
            if len(string[0]) != 6:
                raise ValueError
            self.sernumber = int(string[0])
            if string[-1] == "OFFERT":
                string[-1:] = ["0,00", "€", "0,00", "€", "0,00%"]
            if string[-2] != "€" or string[-4] != "€":
                raise ValueError
            self.name = " ".join(string[1:-6])
            if ',' in string[-6]:
                self.qty = float(string[-6].replace(',', '.'))
            else:
                self.qty = int(string[-6])
            self.price = float(string[-5].replace(',', '.'))
            self.TVA = float(string[-1][:-1].replace(',', '.'))
        else:
            raise NotImplementedError

    def __repr__(self):
        return f"{self.sernumber} {self.name} - Qté : {self.qty} - Prix : {self.price}"

def get_from_file(filename, brand):
    raw = parser.from_file(filename)
    string = raw['content']
    articles = []
    for line in string.splitlines():
        line = line.split(' ')
        try:
            articles.append(Article(line, brand))
        except (ValueError, IndexError) as e:
            pass
    return articles

## Interface pour l'assistance à l'appro, utilisé seulement si appro = True

class KBHit:
    def __init__(self):
        if os.name == 'nt':
            pass
        else:
            self.fd = sys.stdin.fileno()
            self.new_term = termios.tcgetattr(self.fd)
            self.old_term = termios.tcgetattr(self.fd)
            self.new_term[3] = (self.new_term[3] & ~termios.ICANON & ~termios.ECHO)
            termios.tcsetattr(self.fd, termios.TCSAFLUSH, self.new_term)
            atexit.register(self.set_normal_term)

    def set_normal_term(self):
        termios.tcsetattr(self.fd, termios.TCSAFLUSH, self.old_term)

    def kbhit(self):
        if os.name == 'nt':
            return msvcrt.kbhit()
        else:
            dr,dw,de = select([sys.stdin], [], [], 0)
            return dr != []

def let_user_pause(timeout):
    t0 = time()
    while time() - t0 < timeout:
        if kb.kbhit():
            print("\nScript mis en pause. Appuyer sur Entrer pour le poursuivre.")
            sleep(3)
            input()

def show_and_copy(article):
    pyperclip.copy(str(article.sernumber))
    print(str(article.sernumber), end = '', flush=True)
    let_user_pause(after_series_number)
    pyperclip.copy(str(article.qty))
    print(f" {article.qty}")
    let_user_pause(after_quantity)

## Lecture de la facture parsée, mise à jour des prix, compte-rendu

def update_prices(filename, brand):
    prices = {}
    newarticlesindex = {}
    newarticles = []
    newprices = []
    try:
        with open(f"prix_{brand}.txt", 'r') as former:
            lines = [line.split(' ') for line in former.readlines()]
            for [key, value] in lines:
                prices[int(key)] = float(value)
    except:
        pass
    for article in get_from_file(filename, brand):
        if article.sernumber in prices:
            if article.sernumber not in newarticlesindex:
                former_price = prices[article.sernumber]
                if appro and article.qty > 0:
                    show_and_copy(article)
                if article.price != former_price:
                    newprices.append((former_price, article))
            else:
                indx = newarticlesindex[article.sernumber]
                newarticles[indx].qty += article.qty
                newarticles[indx].qty = round(newarticles[indx].qty, 5)
        else:
            newarticlesindex[article.sernumber] = len(newarticles)
            newarticles.append(article)
        prices[article.sernumber] = article.price

    if not archive:
        with open(f"compte-rendu_{filename[:-4]}.txt", 'w') as cr:
            if newprices:
                print("\nEvolutions de prix :")
            for (former_price, article) in newprices:
                print(f"{article.name} : évolution de {former_price} à {article.price}")
                cr.write(f"{article.name} : évolution de {former_price} à {article.price}\n")
        if appro:
            if newarticles:
                print("\nNouveaux articles :")
            for article in newarticles:
                print(article)

    with open(f"prix_{brand}.txt", 'w') as newfile:
        for key, value in prices.items():
            newfile.write(f"{key} {value}\n")

    print("\nBase de données des prix mise à jour." + ("" if archive else " Ecriture du compte-rendu des évolutions de prix terminée."))

## Recueil des arguments donnés dans le shell, gestion des erreurs

if __name__ == "__main__":
    def main():
        global appro, archive, after_series_number, after_quantity, kb
        entrypoint = update_prices
        while len(sys.argv) > 1:
            opt = sys.argv[1]
            if opt[-4:] == ".pdf":
                filename = opt
            elif opt.lower() in brands:
                brand = opt.lower()
            elif opt == "appro":
                appro = True
            elif opt == "archive":
                archive = True
            elif opt in ["pause_set", "set_pause"]:
                try:
                    after_series_number = float(sys.argv[2].replace(',', '.'))
                    sys.argv.pop(2)
                    after_quantity = float(sys.argv[2].replace(',', '.'))
                    sys.argv.pop(2)
                except:
                    print(f"La commande {opt} demande 2 nombres après. Ces 2 nombres doivent être entiers ou à virgule.")
                    sys.exit(1)
            else:
                print(f"Option inconnue \"{sys.argv[1]}\".")
                sys.exit(1)
            if appro and archive:
                print("Les mots-clé appro et archive ne peuvent être utilisés en même temps")
                sys.exit(1)
            sys.argv.pop(1)

        start_time = time()
        try:
            if brand in pasdappro:
                appro = False
                print(f"Le mode appro n'est pas disponible pour {brand}. Les codes de chaque aliments écrits dans la facture ne correspondent pas au code-barre que Chocapix connait. Ce script n'est donc capable que de surveiller l'évolution des prix de {brand}.")
            kb = KBHit()
            entrypoint(filename, brand)
        except KeyboardInterrupt:
            print("\nScript interrompu définitivement")
        except UnboundLocalError:
            print("\nIl faut donner en argument le nom du fichier qui contient la facture sous format pdf (sans oublier le '.pdf'), puis le nom du magasin (Carrefour, Picard...)\nExemple de syntaxe :\npython update_prices.py 21.10_facture.pdf Carrefour")
        except FileNotFoundError:
            print("\nLa facture ou la base de données est introuvable. Il faut qu'elles soient dans le même dossier que le script. Vérifier le nom exact de la facture.")
        except NotImplementedError:
            print(f"\nLa façon de parser les factures de {brand} n'a pas encore été codée.")
        end_time = time()

        print(f"\nTemps écoulé : {end_time-start_time} secondes\n")

    main()
