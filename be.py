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


time_1 = 1.25 # temps pour une quantité 1
time_2 = 3 # temps pour une quantité 2
time_more = 0.5 # temps supplémentaire pour chaque +1 en quantité
time_max = 5 # temps max

def paste_time(quantity):
    if quantity == 1:
        return time_1
    elif quantity in [2, 3, 4, 5]:
        return time_2 + (quantity-2) * time_more
    else: # > 5 mais aussi nombres à virgule (légumes vendus au poids...)
        return time_max

brands = ["carrefour", "picard"]
pasdappro = ["picard"]
keyword = {"carrefour": "OOSHOP", "picard": "SIRET : 78493968805071"}
finddate = {
    "picard": (lambda s: s[s.find("DATE : ")+7:s.find("DATE : ")+17]),
    "carrefour" : (lambda s: s[s.find("Date de commande : ")+19:s.find("Date de commande : ")+29])
}

## Parsing

class Article:
    def __init__(self, string, brand):
        self.brand = brand
        if brand == "carrefour":
            if len(string[0]) != 13:
                raise ValueError
            self.sernumber = string[0]
            self.name = " ".join(string[1:-3])
            self.qty = int(string[-3])
            stm2 = string[-2][string[-2].index('.')+3:]
            if stm2.count('.') == 2:
                stm2 = stm2[stm2.index('.')+3:]
            self.price = float(stm2[:stm2.index('.')+3])
            self.TVA = float(string[-1])
        elif brand == "picard":
            if len(string[0]) != 6:
                raise ValueError
            self.sernumber = string[0]
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
            raise NotImplementedError(brand)

    def __repr__(self):
        return f"{self.sernumber} {self.name} - Qté : {self.qty} - Prix : {self.price}"

def stddate(jjmmaaaa):
    jj = jjmmaaaa[:2]
    mm = jjmmaaaa[3:5]
    aaaa = jjmmaaaa[6:]
    return f"{aaaa}{mm}{jj}"

def get_from_file(filename):
    raw = parser.from_file(filename,)
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
    for line in string.splitlines():
        line = line.split(' ')
        try:
            articles.append(Article(line, brand))
        except (ValueError, IndexError) as e:
            pass
    return date, brand, articles

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
            preparation()

def preparation(qty = 0):
    if qty == 1:
        print("Les quantités sont maintenant toutes 1. Ca va aller plus vite.")
    print("Début dans ", end="", flush=True)
    for i in range(12):
        print(3-i//4 if i%4 == 0 else ".", end='', flush=True)
        sleep(0.25)
    print()

def show_and_copy(article):
    pyperclip.copy(article.sernumber)
    print(f"{article.sernumber} - {article.qty}\t{article.name}")
    let_user_pause(paste_time(article.qty))

## Lecture de la facture parsée, mise à jour des prix, compte-rendu

def group_by_sernum(articles):
    ans = {}
    for article in articles:
        if article.sernumber in ans:
            ans[article.sernumber].qty += article.qty
            ans[article.sernumber].qty = round(ans[article.sernumber].qty, 5)
        else:
            ans[article.sernumber] = article
    return list(ans.values())

def update_prices(parsedfile):
    date, brand, articles = parsedfile

    prices = {}
    try:
        with open(f"prix_{brand}.txt", 'r') as former:
            lines = [line.split(' ') for line in former.readlines()]
            for [key, value] in lines:
                prices[key] = float(value)
    except:
        pass

    appro_started = False
    unique_started = False
    newarticles = []
    newprices = []
    articles = group_by_sernum(articles)
    articles.sort(key=lambda a:100 if a.qty%1 else a.qty, reverse=True)
    for article in articles:
        if article.qty == 0:
            break
        if article.sernumber in prices:
            former_price = prices[article.sernumber]
            if appro:
                if article.qty == 1 and not unique_started:
                    unique_started = True
                    preparation(1)
                elif not appro_started:
                    appro_started = True
                    preparation()
                show_and_copy(article)
            if article.price != former_price:
                newprices.append((former_price, article))
        else:
            newarticles.append(article)
        prices[article.sernumber] = article.price

    if not archive:
        with open(f"compte-rendu_{brand}_{date}.txt", 'w') as cr:
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
        lines = []
        for key, value in prices.items():
            lines.append(f"{key} {value}\n")
        lines.sort() #ça sert qu'à aider le débug
        for line in lines:
            newfile.write(line)

## Recueil des arguments donnés dans le shell, gestion des erreurs

if __name__ == "__main__":
    def main():
        global appro, archive, time_1, time_2, time_more, time_max, kb
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
            elif opt in ["pause_set", "set_pause"]:
                try:
                    time_1 = float(sys.argv[2].replace(',', '.'))
                    sys.argv.pop(2)
                    time_2 = float(sys.argv[2].replace(',', '.'))
                    sys.argv.pop(2)
                    time_more = float(sys.argv[2].replace(',', '.'))
                    sys.argv.pop(2)
                    time_max = float(sys.argv[2].replace(',', '.'))
                    sys.argv.pop(2)
                except:
                    print(f"La commande {opt} demande 4 nombres après. Ces 2 nombres doivent être entiers ou à virgule.")
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
            if archive and not files:
                for filename in os.listdir("archive"):
                    if filename.endswith(".pdf"):
                        files.append("./archive/"+filename)
            kb = KBHit()
            parsedfiles = [get_from_file(filename) for filename in files]
            parsedfiles.sort()
            for parsedfile in parsedfiles:
                entrypoint(parsedfile)
            print("\nBase de données des prix mise à jour." + ("" if archive else " Ecriture du compte-rendu des évolutions de prix terminée."))
        except KeyboardInterrupt:
            print("\nScript interrompu définitivement")
        except UnboundLocalError:
            print("\nMauvaise syntaxe. Exemples de syntaxe :\npython be.py 21.10_facture.pdf appro set_pause 2 4 0.5 6\npython be.py archive")
        except FileNotFoundError:
            print("\nLa facture ou la base de données est introuvable. Il faut qu'elles soient dans le même dossier que le script. Vérifier le nom exact de la facture.")
        except (KeyError, NotImplementedError) as brand:
            if brand in brands:
                print(f"\nLa façon de parser les factures de {brand} n'a pas encore été codée.")
            else:
                print(f"\nLa marque n'a pas pu être reconnue. Il peut s'agir d'une nouvelle marque (parsing pas encore implémenté) ou alors la forme de la facture a changé (parsing à refaire).")
        end_time = time()

        print(f"\nTemps écoulé : {end_time-start_time} secondes\n")

    main()
