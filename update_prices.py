#! /usr/bin/env python
# -*- coding: utf-8 -*-

from tika import parser
from time import time, sleep

import sys
import msvcrt
import pyperclip

appro = False #si False, l'assistance à l'appro ne se déclenche pas

magasins = ["carrefour", "picard", "efiester"]
pasdappro = ["picard"] #remettre de force appro à False

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

def let_user_pause(timeout):
    t0 = time()
    while time() - t0 < timeout:
        if msvcrt.kbhit(): # à tes souhaits
            print("\nScript mis en pause. Appuyer sur Entrer pour le poursuivre.")
            sleep(3)
            input()

def show_and_copy(article):
    pyperclip.copy(str(article.sernumber))
    print(str(article.sernumber), end = '', flush=True)
    let_user_pause(1)
    pyperclip.copy(str(article.qty))
    print(f" {article.qty}")
    let_user_pause(3 if article.qty==1 else 4)

## Lecture de la facture parsée, mise à jour des prix, compte-rendu

def update_prices(filename, brand, appro=True):
    prices = {}
    newarticlesindex = {}
    newarticles = []
    newprices = []
    with open(f"prix_{brand}.txt", 'r') as former:
        lines = [line.split(' ') for line in former.readlines()]
        for [key, value] in lines:
            prices[int(key)] = float(value)

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

    with open(f"compte-rendu_{filename[:-4]}.txt", 'w') as cr:
        if newprices:
            print("\nEvolutions de prix :")
        for (former_price, article) in newprices:
            print(f"{article.name} : évolution de {former_price} à {article.price}")
            cr.write(f"{article.name} : évolution de {former_price} à {article.price}\n")
    if newarticles:
        print("\nNouveaux articles :")
    for article in newarticles:
        print(article)

    with open(f"prix_{brand}.txt", 'w') as newfile:
        for key, value in prices.items():
            newfile.write(f"{key} {value}\n")

## Recueil des arguments donnée dans le shell, gestion des erreurs

if __name__ == "__main__":
    def main():
        global start_time, appro
        entrypoint = update_prices
        while len(sys.argv) > 1:
            opt = sys.argv[1]
            if opt[-4:] == ".pdf":
                filename = opt
            elif opt.lower() in magasins:
                brand = opt.lower()
                if brand in pasdappro:
                    appro = False
            elif opt == "appro":
                appro = True
            else:
                print(f"Option inconnue \"{sys.argv[1]}\".")
                sys.exit(1)
            sys.argv.pop(1)

        start_time = time()
        try:
            entrypoint(filename, brand, appro)
            print("\nBase de données des prix mise à jour. Ecriture du compte-rendu des évolutions de prix terminée.")
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