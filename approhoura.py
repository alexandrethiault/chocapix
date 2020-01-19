# coding: utf-8

import urllib.request
from time import sleep, time
from webbot import Browser
from requests_html import AsyncHTMLSession

def find(string, substring):
    #find("abaab", "ab") = [0, 3]
    assert substring[0] not in substring[1:] # de quoi éviter de coder un KMP
    ans = []
    i = 0
    cursub = 0
    while i < len(string):
        if string[i] == substring[cursub]:
            cursub+=1
            if cursub == len(substring):
                ans.append(i-len(substring)+1)
                cursub = 0
        else:
            cursub = 0
        i += 1
    return ans

def links(string, substring):
    #avec  substring = '<div class="marque">' ça trouve les liens
    #cachés dans le code-source html de la page houra avec la liste d'achat
    ans = []
    for i in find(string, substring):
        mini = string[i+29:i+300]
        ans.append(mini[:mini.index('"')])
    return ans

def get_sernum(source):
    #trouve le numéro de série dans le code-source html d'une page d'aliment
    return source[source.index("https://media")+40:source.index("https://media")+53]

url = 'https://www.houra.fr/'
auth = {'Email': '...', 'Pass': '...', "CPClient": "91120"}

def get_links(auth):
    #récupère les liens de tous les articles dans la liste donnée par le lien
    web = Browser()

    web.go_to('houra.fr')
    for key,value in auth.items():
        web.type(value , id=key)
    web.press(web.Key.ENTER)
    sleep(1)
    web.press(web.Key.ESCAPE)
    web.go_to('https://www.houra.fr/cpt/index.php?c=liste&idListe=54395664')
    s=web.get_page_source()
    web.close_current_tab()
    return links(s,'<div class="marque">')

import asyncio
import aiohttp
from aiohttp import web
import json

WEBSITES = ['https://www.houra.fr/nutella-pate-a-tartiner-750g/1367878/1451168/TO_MEMOLISTE/', 'https://www.houra.fr/delifrance-10-pains-au-chocolat-pur-beurre-pret-a-cuire-10x60g/1405213/1508030/TO_MEMOLISTE/']

async def fetch(session, url):
    async with session.get(url) as response:
        return await response.text()

async def main():
    async with aiohttp.ClientSession() as session:
        # Faire les requêtes en parallèle
        coroutines = [fetch(session, website) for website in WEBSITES]

        # Attendre que tlm a fini
        results = await asyncio.gather(*coroutines, return_exceptions=True)

    # Obtenir les numéros de série de tout le monde avec ces résultats
    response_data = [
        (website, get_sernum(result))
        for website, result in zip(WEBSITES, results)
    ]

    print(response_data)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())

#http://www.houra.fr/catalogue/?id_article=
#ids -> 1405213, 1367878
#faux ids, qui sont dans la facture -> 1508030, 1451168