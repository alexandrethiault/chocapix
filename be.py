#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import os, sys
import re
import logging
from time import time, sleep

from getpass import getpass
from tika import parser, tika
logging.getLogger('tika.tika').setLevel(logging.FATAL)

import selenium
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
if os.name == 'nt':
    import subprocess
    import winreg
    from msedge.selenium_tools import Edge, EdgeOptions

repository = "https://github.com/alexandrethiault/chocapix"

brands = ["carrefour", "auchan", "houra",]

### Parsing

# Mot qui donne fiablement l'origine de la facture si on le trouve dedans
keyword = {
    "carrefour": "I ROUTE DE PARIS",
    "auchan": "Auchan Direct",
    "houra": "houra.fr",
}

# Emplacement de la date dans le raw parse de la facture
finddate = {
    "carrefour": (lambda s: s[s.find("Date de commande : ")+19:s.find("Date de commande : ")+29]),
    "auchan": (lambda s: s[s.find("FACTURE N° ")+32:s.find("FACTURE N° ")+42]),
    "houra": (lambda s: s[s.find("Réf. p")-45:s.find("Réf. p")-35]),
}

# Indicateurs préliminaire qu'un article commence peut-être à cette ligne
def article_with_code(length, line):
    return len(line) >= length and line[:length].isdigit()

is_article = {
    "carrefour": (lambda line: article_with_code(13, line)),
    "auchan": (lambda line: article_with_code(13, line)),
    "houra": (lambda line: line.find(" ")>=4 and line[:line.find(" ")].isdigit()),
}

def new_parsing(filename):
    # Pour apprendre à parser des nouvelles marques dont la facture est en pdf
    raw = parser.from_file(filename)
    string = raw['content']
    for line in string.splitlines():
        line = line.split(' ')
        print(line)
    return string

def new_parsing_html(filename):
    string=""
    with open(filename) as f:
        for line in f.readlines():
            string+=line
            print(line.split(' '))
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
        self.price = le prix unité TTC (float)
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
        s[0] est un faux code-barres. Tout est TTC.
        Subtilité : certains articles sont offerts, ce qui affecte le parsing.

        Pour découvrir à quoi ressemblent ces lignes parsées pour un nouveau
        magasin, utiliser la fonction new_parsing("nom_facture.pdf")
        Il faut comparer les lignes imprimées à celles de la facture avec
        attention car l'ordre des colonnes de la facture n'est pas conservé !

        Plein de lignes de la facture parsée ne se rapportent pas à un article
        (destinataire, date d'émission de la facture...), il faut aussi savoir
        les ignorer. Utiliser pour ça des assert. AssertionError, ValueError
        et IndexError sont rattrapées par la fonction get_from_pdf qui est la
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
            elif date < "20210800":
                self.sernumber = line[0]
                self.name = " ".join(line[1:-4])
                self.qty = int(line[-4])
                self.price = float(line[-1])
                self.TVA = float(line[-2])
            else:
                self.sernumber = line[0]
                self.name = " ".join(line[1:-3])
                self.qty = int(line[-3])
                stm2 = line[-2][line[-2].index('.')+3:]
                if stm2.count('.') == 3:  # Il y a une remise sur cet article
                    stm2 = stm2[stm2.index('.')+3:]
                self.price = float(stm2[:stm2.index('.')+3])
                self.TVA = float(stm2[stm2.index('.')+3:])

        elif brand == "auchan":
            assert line[0] != "2007984000383"  # Frais de livraison
            self.sernumber = line[0]
            self.name = " ".join(line[1:-6])
            self.qty = int(line[-6])
            self.TVA = float(line[-2])
            self.price = round(float(line[-5]) * (1. + self.TVA*0.01), 2)
        elif brand == "houra_html":
            j=line.index('alt="') # alt="0123456789012 - MARQUE - Nom" title=...
            k=line.index('" title="')
            self.sernumber = line[j+5:j+18]
            self.name = line[j+21:k].replace("&#39;","'").replace("&amp;","&")
            j=line.index('<div class="contenant">') + 23
            self.name += " "+line[j:line.find('<',j)]
            j=line.index('class="prix">')+13 # beaucoup plus loin dans le html
            try:self.price = float(line[j:line.find('€', j)].replace(',', '.'))
            except:self.price = float(line[j:line.find('&', j)].replace(',', '.'))
            self.qty = None
            qty_pattern='<input type="text" class="btnQuantite" name="quantite"'
            if "RUPTURE" not in line[:100]:
                j=line.find(qty_pattern)
                if j != -1:
                    j=line.find("value=", j)
                    k=line.find(" ", j)
                    self.qty = line[j+7:k-1]
        elif brand == "houra":
            self.name = ' '.join(line[1:-5])
            self.qty = float(line[-5].replace(',','.'))
            self.price = float(line[-2].replace(',','.'))
            self.TVA = float(line[-3].replace(',','.'))
        else:
            raise NotImplementedError(brand)

    def __repr__(self):
        return f"{self.sernumber} {self.name} - Qté : {self.qty} - Prix : {self.price}"  # Si cette ligne cause une SyntaxError, c'est que la version de Python utilisée n'est pas >= 3.6 !

def stddate(jjmmaaaa):
    # Récupérer une date qui s'ordonne bien (aaaammjj) à partir de jj/mm/aaaa
    jj = jjmmaaaa[:2]
    mm = jjmmaaaa[3:5]
    aaaa = jjmmaaaa[6:]
    return f"{aaaa}{mm}{jj}"

def get_from_pdf(filename):
    # Récupérer la date, la marque et tous les articles de la facture filename
    print("\nParsing du PDF en cours...")
    raw = parser.from_file(filename)
    string = raw["content"]
    for br in brands:
        if keyword[br].lower() in string.lower():
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
            if i+1 < len(lines) and lines[i+1].split(" ") != ['']:
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
    print("Succès")
    return date, brand, articles

def get_from_html(htmlname):
    string=""
    with open(htmlname) as f:
        for line in f.readlines():
            string+=line
    for br in brands:
        if keyword[br].lower() in string.lower():
            brand = br
            break
    else:
        raise NotImplementedError(htmlname)
    articles=[]
    if brand=="houra":
        article_pattern='<div class="row no-padding">\n    \n        <div'
        for m in re.finditer(article_pattern, string):
            i=m.start() + 42
            line=string[i-100:string.find(article_pattern[:28],i)]
            article = Article(line, "houra_html")
            article.brand = "houra"
            articles.append(article)
    else:
        raise NotImplementedError(htmlname)
    return brand, articles

def merge(dir, parsedpdf, parsedhtml):
    date, brand, ap = parsedpdf
    _, ah = parsedhtml
    assert brand == "houra"
    details = []
    def match(article):
        hname = article.name
        hprice = article.price
        def strip(s): return s.strip(", '").lower().replace("é", "e").replace("è", "e").replace("ê", "e").replace("ë", "e").replace("à", "a").replace("â", "a").replace("î", "i").replace("ï", "i").replace("û", "u").replace("ô", "o").replace("%vol", "°").replace(".", ",").replace("'", "")
        hwords = {strip(i) for i in hname.split(" ") if i[2:] or not i.isalpha()}
        hwords = {(i[:-1] if i.endswith("s") else i) for i in hwords}
        hwords = {(i[i.find("x")+1:] if "x" in i and i[:i.find("x")].isdigit() else i) for i in hwords}

        scores = {a: min(a.price/hprice, hprice/a.price)**4 + (hprice==a.price) for a in ap}
        similarity = []
        for a in scores:
            pwords = {strip(i) for i in a.name.split(" ") if i[2:] or not i.isalpha()}
            pwords = {(i[:-1] if i.endswith("s") else i) for i in pwords}
            pwords = {(i[i.find("x")+1:] if "x" in i and i[:i.find("x")].isdigit() else i) for i in pwords}
            if "b#uf" in pwords: pwords.add("boeuf")
            if "grinbergen" in pwords: pwords.add("grimbergen") # Oui réellement
            scores[a] *= len(pwords&hwords)
        ans = max(scores.keys(), key=(lambda key: scores[key]))
        details.append(["", str(round(scores[ans],4)), hname, ans.name])
        return ans

    for a in ah:
        #if a.qty is None: # Je ne fais pas confiance aux quantités html
        a_in_ap = match(a)
        a.qty = a_in_ap.qty
        a.price = a_in_ap.price # Le prix PDF change jamais, sur HTML si...

    ah.sort(key=lambda a:a.name)
    with open(os.path.join(dir,"facture_parsee.txt"), 'w') as f:
        f.write("--- Fichier généré automatiquement ---\n\n")
        for a in ah:
            f.write(str(a)+"\n")

    details.sort(key=lambda a:a[2])
    with open(os.path.join(dir,"detail_association_noms.txt"), 'w') as f:
        f.write("--- Fichier généré automatiquement ---\n\nUne étape du loggage des factures Houra est la fusion des attributs de deux factures.\nLa seule clé primaire utilisable est le nom, et il y a des différences dans les noms des deux factures.\nPour associer les paires de noms ensembles, le script fait des suppositions pas toujours sures.\nVoici le détail des associations faites.\n\nLes paires de noms sont précédées d'un indice de ressemblance.\nLes bas indices (4 ou moins) sont ceux qui doivent retenir l'attention.\nSi une association se révèle en effet fautive, la quantité et le prix loggés peuvent être faux.\nVérifiez alors sur la facture PDF pour récupérer les vraies valeurs.\n\n")
        for detail in details:
            f.write("\n".join(detail)+"\n")

    return date, brand, ah

### Navigateur robot, loggage d'un aliment dans chocapix

def init_driver_edge_windows():
    edge_options = EdgeOptions()
    edge_options.use_chromium = True
    #edge_options.add_argument('headless')
    #edge_options.add_argument('disable-gpu')
    try:
        return Edge(executable_path=r"./driver/msedgedriver", options=edge_options)
    except:
        if os.path.isdir("driver"):
            subprocess.call(["rd" "/s" "/q", "driver"], shell=True)
        os.mkdir("driver")
        try:
            keyPath = r"Software\Microsoft\Edge\BLBeacon"
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, keyPath, 0, winreg.KEY_READ)
            edge_version = winreg.QueryValueEx(key, "version")[0]
            OS = "64" if 'PROGRAMFILES(X86)' in os.environ else "32"
            subprocess.call(["curl", "-o", "tmp.zip",  f"https://msedgedriver.azureedge.net/{edge_version}/edgedriver_win{OS}.zip"])
            subprocess.call(["tar", "-xf", "tmp.zip"])
            subprocess.call(["del", "tmp.zip"], shell=True)
            subprocess.call(["move", "msedgedriver.exe", "driver"], shell=True)
            subprocess.call(["rd" "/s" "/q", "Driver_Notes"], shell=True)
            return Edge(executable_path=r".\driver\msedgedriver.exe", options=edge_options)
        except:
            os.rmdir("driver")
            raise NotImplementedError('Une erreur a été rencontrée. Cela peut avoir été causé par une version de Edge obsolète. Mettez le navigateur à jour.')

def init_driver_firefox():
    try:
        return webdriver.Firefox(executable_path="./driver/geckodriver", service_log_path=os.devnull)
    except selenium.common.exceptions.WebDriverException:
        raise Exception('Firefox ou geckodriver manquant ou obsolète. Si Firefox est installé, mettez-le à jour, installez le dernier geckodriver à https://github.com/mozilla/geckodriver/releases et rangez-le dans un dossier nommé "driver"')

def init_driver_opera():
    options = selenium.webdriver.opera.options.Options()
    options.add_argument('log-level=3')
    try:
        return webdriver.Opera(options=options,executable_path="./driver/operadriver")
    except selenium.common.exceptions.WebDriverException:
        raise Exception('Opera ou son driver est manquant ou obsolète. Si Opera est installé, mettez-le à jour, installez son dernier driver à https://github.com/operasoftware/operachromiumdriver/releases et rangez-le dans un dossier nommé "driver"')

def init_driver_chrome():
    try:
        return webdriver.Chrome(executable_path="./driver/chromedriver")
    except selenium.common.exceptions.WebDriverException:
        raise Exception('Chrome ou son driver est manquant ou obsolète. Si Chrome est installé, mettez-le à jour, installez son dernier driver à https://chromedriver.chromium.org/downloads et rangez-le dans un dossier nommé "driver"')

def init_driver():
    try:
        print("\nLancement d'un driver Firefox...")
        return init_driver_firefox()
    except Exception as e:
        print("Echec du lancement de Firefox, message d'erreur :\n", e)
        try:
            print("Lancement d'un driver Opera...")
            return init_driver_opera()
        except Exception as e:
            print("Echec du lancement de Opera, message d'erreur :\n", e)
        if os.name == 'nt':
            try:
                print("Lancement d'un driver Edge...")
                return init_driver_edge_windows()
            except Exception as e:
                print("Echec du lancement de Edge, message d'erreur :\n", e)
        try:
            print("Lancement d'un driver Chrome...")
            return init_driver_chrome()
        except Exception as e:
            print("Echec du lancement de Chrome, message d'erreur :\n", e)
    raise NotImplementedError(f"Echec de toutes les tentatives de lancement de driver. Réglez les problèmes pour au moins un de ces navigateurs : Opera, Firefox{', Edge' if os.name == 'nt' else ''} ou Chrome")

def log_in(driver, name, pw):
    name_box = '/html/body/div[1]/div/div[1]/div/nav/div/div/div[3]/div/form/input[1]'
    pw_box = '/html/body/div[1]/div/div[1]/div/nav/div/div/div[3]/div/form/input[2]'
    login_button = '/html/body/div[1]/div/div[1]/div/nav/div/div/div[3]/div/form/button'
    driver.find_element_by_xpath(name_box).clear()
    driver.find_element_by_xpath(pw_box).clear()
    driver.find_element_by_xpath(name_box).send_keys(name)
    driver.find_element_by_xpath(pw_box).send_keys(pw)
    driver.find_element_by_xpath(pw_box).send_keys(Keys.RETURN)

def start_appro(driver):
    appro_button = '/html/body/div[1]/div/div[3]/div[2]/div/div/div/div/div[2]/div/div[4]/div/div[1]/span/a'
    driver.find_element_by_xpath(appro_button).click()

def launch_appro_and_parse_bills(pdfbills):
    global driver
    # Lancer un navigateur robot et y lancer une appro
    try:
        print("\nRécupération des identifiants dans login.txt...")
        f = open("login.txt", "r")
        name, pw = f.read().rstrip("\n").split()[:2]
        f.close()
        print("Succès")
    except FileNotFoundError as e:
        print("Echec : aucun login.txt présent. Connexion manuelle.")
        name, pw = input("Nom d'utilisateur : "), getpass("Mot de passe : ")
    except:
        f.close()
        print("Echec : problème de lecture de login.txt. Connexion manuelle.")
        name, pw = input("Nom d'utilisateur : "), getpass("Mot de passe : ")

    if name != "debug":
        driver = init_driver()
        print("Succès")
        try:
            driver.implicitly_wait(15)
            driver.get("https://chocapix.binets.fr/#/badmintonrouje")
            # Lancer chocapix est très lent donc on parse les PDF en attendant
            parsedbills = [get_from_pdf(filename) for filename in pdfbills]
            log_in(driver, name, pw)
        except:
            driver.quit()
            raise selenium.common.exceptions.NoSuchElementException("Impossible d'accéder à chocapix. Peut-être un problème de connexion à eduroam ?")
        try:
            driver.implicitly_wait(2)
            start_appro(driver)
        except:
            driver.quit()
            raise selenium.common.exceptions.NoSuchElementException(f"Impossible d'accéder au menu de l'appro. Peut-être un mauvais mot de passe ou un problème de droits pour l'utilisateur {name} ?")
    else:
        parsedbills = [get_from_pdf(filename) for filename in pdfbills]
    return parsedbills

def log(article, driver, last_escape):
    barcode, qty, price = article.sernumber, article.qty, article.price
    barcode_box = '//*[@id="addApproItemInput"]'
    blocked_test = '/html/body/div[1]/div/div[3]/div[2]/div/div/div/div/ui-view/div/div/div[1]/div/span'
    qty_box = '/html/body/div[1]/div/div[3]/div[2]/div/div/div/div/ui-view/div/div/div/table/tbody/tr[2]/td[2]/input'
    price_box = '/html/body/div[1]/div/div[3]/div[2]/div/div/div/div/ui-view/div/div/div/table/tbody/tr[2]/td[3]/input'

    # Rentrer le prochain code-barres
    driver.find_element_by_xpath(barcode_box).clear()
    driver.find_element_by_xpath(barcode_box).send_keys(barcode)
    driver.find_element_by_xpath(barcode_box).send_keys(Keys.RETURN)
    # Appuyer sur echap au cas où une fenêtre de nouvel aliment est apparue
    sleep(max(0, 0.35 - (time() - last_escape)))
    webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
    last_escape = time()
    # Tester si c'est un nouvel aliment
    if driver.find_element_by_xpath(barcode_box).get_attribute('value'):
        driver.find_element_by_xpath(barcode_box).clear()
        return -1, last_escape
    # Tester si c'est un aliment bloqué
    driver.implicitly_wait(0.2) # Changer le timeout des fonctions find_...
    try:
        driver.find_element_by_xpath(blocked_test).click()
        return -2, last_escape
    except:
        pass
    driver.implicitly_wait(2)
    # Remplir les champs de quantité et prix
    former_price = driver.find_element_by_xpath(price_box).get_attribute('value')
    former_price = float(former_price.replace(",","."))
    driver.find_element_by_xpath(price_box).clear()
    driver.find_element_by_xpath(price_box).send_keys(str(price).replace(".",","))
    driver.find_element_by_xpath(qty_box).clear()
    driver.find_element_by_xpath(qty_box).send_keys(qty)
    # Attendre que ces champs aient obtenu leurs valeurs
    while str(qty) != driver.find_element_by_xpath(qty_box).get_attribute('value'):
        sleep(0.01)
    return former_price, last_escape

### Lecture de la facture parsée, mise à jour de la base de données, compte-rendu

def group_by_sernum(articles):
    # Plusieurs articles d'une facture peuvent concerner un même aliment
    ans = {}
    for article in articles:
        if article.sernumber in ans:
            ans[article.sernumber].qty += article.qty
            ans[article.sernumber].qty = round(ans[article.sernumber].qty, 3)
        else:
            ans[article.sernumber] = article
    return list(ans.values())

def confirm_end():
    ok = ["y","o","yes","oui"]
    no = ["n","no","non"]
    ans = ""
    while ans not in ok+no:
        ans = input("\nEnregistrer les modifications de prix et nouveaux aliments dans la base de données du script ? Ceci n'est pas la même chose que valider l'appro sur chocapix.\n(y/n) : ").lower()
    return ans in ok

def auto_appro(parsedfile, dir=None):
    global driver
    date, brand, articles = parsedfile
    if not articles:
        raise NotImplementedError(brand+"0")
    if len(brand) >= 2 and brand[-2] == '_':  # "cora_f", "cora_r"...
        brand = brand[:-2]

    # Lire la base de données des prix
    codes = set()
    prices = {}
    names = {}
    hidden = set()
    try:
        with open(f"prix_{brand}.txt", "r", encoding="utf-8") as former:
            lines = [line.split() for line in former.readlines()]
            for line in lines:
                wl, code, price = line[:3]
                name = " ".join(line[3:])
                codes.add(code)
                prices[code] = float(price)
                names[code] = name
                if wl > "0":
                    hidden.add(code)
    except:
        pass


    # Logger tous les articles
    newarticles = []
    newprices = []
    blocked = []
    nonloggable = []
    articles = group_by_sernum(articles)
    esc = 0
    for article in articles:
        # Ancien prix selon la base de données (ou -1 si article inconnu)
        if article.sernumber in prices:
            former_price = prices[article.sernumber]
        else:
            former_price = -1
        # Mise à jour de prices et names, pas encore de la base de données
        prices[article.sernumber] = article.price
        names[article.sernumber] = article.name
        # Quantité = 0 : on passe
        if article.qty == 0:
            continue
        # Article considéré comme non loggable : on passe mais ça va dans le compte rendu au cas où le respo appro veut quand même logger ça
        if article.sernumber in hidden:
            nonloggable.append(article)
            continue
        # Afficher l'article loggé dans la console, le logguer
        #print(f"{article.sernumber} - {article.qty}\t{article.name}")
        if driver is not None: # en mode debug, driver est None
            former_price, esc = log(article, driver, esc) # même si on connait le prix via la base de données, le prix de chocapix fait foi
        # Changement de prix : ça va dans le compte rendu
        if former_price >= 0 and article.price != former_price:
            newprices.append((former_price, article))
        # Nouvel article selon chocapix, pas forcément selon la base de données
        elif former_price == -1:
            if article.sernumber in codes: # Cet article a déjà été vu par le script mais pas loggé par le respo appro : considéré non loggable.
                hidden.add(article.sernumber)
                nonloggable.append(article)
            else: # Nouvel article pour chocapix et le script
                newarticles.append(article)
        # Article bloqué, pas loggable
        elif former_price == -2:
            blocked.append(article)

        codes.add(article.sernumber) # On peut le faire qu'à la fin pour permettre le test de l'article non loggable inconnu de chocapix mais déjà acheté

    # Lister et créer un compte rendu des changements de prix...
    crname = f"compte-rendu_{brand}_{date}.txt"
    if dir is not None: crname = os.path.join(dir, crname)
    with open(crname, "w") as cr:
        cr.write("--- Fichier généré automatiquement ---\n")
        if newprices:
            cr.write("\nEvolutions de prix, déjà notées dans Chocapix, à titre informatif :\n")
        for (former_price, article) in newprices:
            cr.write(f"{article.name} : évolution de {former_price} à {article.price}\n")
        if newarticles:
            cr.write("\nNouveaux articles, pas encore notés dans Chocapix, à logger à la main :\n")
        for article in newarticles:
            cr.write(f"{article}\n")
        if blocked:
            cr.write("\nArticles bloqués, impossibles à logger :\n")
        for article in blocked:
            cr.write(f"{article}\n")
        if nonloggable:
            cr.write("\nArticles que le script considère comme correspondant à des aliments non loggables, non loggés :\n")
        for article in nonloggable:
            cr.write(f"{article}\n")

    print("\nEcriture du compte-rendu de l'appro terminée.\nL'auto-appro est terminée.\nLes nouveaux prix ont déjà été changés sur Chocapix.\nIl reste encore à ajouter manuellement les nouveaux articles.\nIls sont listés dans le compte-rendu de l'auto-appro.")

    if not confirm_end():
        return

    # Ecrire une nouvelle base de données
    with open(f"prix_{brand}.txt", "w", encoding="utf-8") as newfile:
        lines = []
        for code, price in prices.items():
            lines.append(f"{1*(code in hidden)} {code} {price} {names[code]}\n")
        lines.sort(key=lambda st: st[2:]) # Trier par code-barres
        for line in lines:
            newfile.write(line)

### Recueil des arguments donnés dans le shell, gestion des erreurs

if __name__ == "__main__":
    def main():
        global driver
        driver = None

        pdfbills = []
        twobilldirs = []
        while len(sys.argv) > 1:
            opt = sys.argv[1]
            if opt.endswith(".pdf"):
                pdfbills.append(opt)
            elif os.path.isdir(opt):
                if len([i for i in os.listdir(opt) if i[-4:]==".pdf"]) != 1\
                or len([i for i in os.listdir(opt) if i[-5:]==".html"]) != 1:
                    sys.exit("Donner en argument un dossier sert à donner une facture PDF et une facture HTML de Houra. Vérifiez que le dossier contient ces deux factures et pas d'autres fichiers PDF ou HTML.")
                twobilldirs.append(opt)
            else:
                sys.exit(f"Option \"{sys.argv[1]}\" inconnue.")
            sys.argv.pop(1)

        try:
            start_time = time()
            print("\nDémarrage du serveur tika pour parser des PDF...")
            tika.TikaStartupMaxRetry = 0
            try:tika.checkTikaServer() # Ca VA foirer. Mais ça va lancer le serveur dès maintenant et donc il sera prêt à la fin de la connexion à chocapix
            except:pass
            print("Succès")
            tika.TikaStartupSleep = 0.3
            tika.TikaStartupMaxRetry = 50
            parsedbills = launch_appro_and_parse_bills(pdfbills)
            for dir in twobilldirs:
                bills = [os.path.join(dir,bill) for bill in os.listdir(dir) if bill[-4:]==".pdf" or bill[-5:]==".html"]
                if bills[1][-1]=="f": bills=bills[::-1]
                parsedpdf = get_from_pdf(bills[0])
                parsedhtml = get_from_html(bills[1])
                parsedbills.append(merge(dir, parsedpdf, parsedhtml))
            parsedbills.sort()
            for parsedbill in parsedbills:
                auto_appro(parsedbill)
            if not parsedbills:
                print("\nAucune facture n'a été donnée en argument.")
        except KeyboardInterrupt:
            sys.exit("\nScript interrompu définitivement.")
        except FileNotFoundError as e:
            sys.exit(f"\nLa facture {e} est introuvable. Vérifier le nom exact de la facture.")
        except (KeyError, NotImplementedError) as brand:
            brand = str(brand)
            if brand in brands:
                sys.exit(f"\nLa façon de parser les factures de {brand} n'a pas encore été codée.")
            elif brand and brand[:-1] in brands and brand[-1] == "0":
                sys.exit(f"\nAucun article n'a pu être reconnu. Il semble que {brand[:-1]} a légèrement modifié la forme de ses factures. Merci de prévenir une personne qui maintient le script pour mettre à jour la détection des articles {brand[:-1]} par ce script.")
            elif brand.endswith(".pdf") or brand.endswith(".html"):
                sys.exit(f"\nLa marque de {brand} n'a pas pu être reconnue. Il peut s'agir d'une nouvelle marque (parsing pas encore implémenté) ou alors la forme de la facture a beaucoup changé (parsing à refaire). Merci de prévenir une personne qui maintient le script pour mettre à jour ce script.")
            else:
                sys.exit(brand) # Aucun driver ne marche
        except selenium.common.exceptions.NoSuchElementException as e:
            sys.exit(str(e))
        except selenium.common.exceptions.WebDriverException:
            try:driver.quit()
            except:pass
            sys.exit("Le driver a été fermé. Script interrompu définitivement.")
        except RuntimeError:
            sys.exit("\nImpossible de démarrer le serveur tika pour parser des PDF. Tika a besoin de Java pour fonctionner."+" Le dossier bin du jdk de Java a-t-il été ajouté au PATH ?" if os.name == 'nt' else "")
        except:
            print(f"\nUne erreur inattendue a été rencontrée. Relisez le README sur {repository}. Si le problème persiste, merci de prévenir une personne qui maintient le script.")
            raise
        finally:
            end_time = time()
            print(f"\nTemps écoulé : {end_time-start_time} secondes.")
        sys.exit(0)

    main()
