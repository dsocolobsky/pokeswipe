#!/usr/bin/env python3
import requests
import json
import twitter
import threading
import pickle

scanned = []
index = 0

def makePokeURL(lat, lon):
    return "https://fastpokemap.se/#{},{}".format(lat, lon)


def makeTuple(lat, lon):
    return (('key', 'allow-all'), ('ts', '0'), ('lat', lat), ('lng', lon))


def generateAlert(pokemon, lugar, url):
    return "{} en {} {}".format(pokemon, lugar, url)


def removePokemon(tple):
    print("Removing {} {}".format(tple[0], tple[1]))
    scanned.remove(tple)

with open('twitter.json') as twitter_file:
    twitter_data = json.load(twitter_file)

with open('coordinates.json') as coords_file:
    coordinates = json.load(coords_file)

with open('pokemons.json') as poke_file:
    pokemon_json = json.load(poke_file)
    pokemon_list = pokemon_json['pokemons']

with open('index.pkl', 'rb') as index_file:
    index = pickle.load(index_file)
    index_file.close()

print("Index: {}".format(index))

headers = {
    'Origin': 'https://fastpokemap.se',
    'Dnt': '1',
    'Accept-Encoding': 'gzip, deflate, sdch, br',
    'Accept-Language': 'en-US,en;q=0.8,es;q=0.6',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.116 Safari/537.36',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Authority': 'api.fastpokemap.se'
}

twapi = twitter.Api(consumer_key=twitter_data['consumer_key'],
                    consumer_secret=twitter_data['consumer_secret'],
                    access_token_key=twitter_data['access_token_key'],
                    access_token_secret=twitter_data['access_token_secret'])


def scan(cor):
    parameters = makeTuple(cor['lat'], cor['lon'])

    r = requests.get("https://api.fastpokemap.se",
                     params=parameters, headers=headers)
    url = makePokeURL(cor['lat'], cor['lon'])
    print("Escaneando {}".format(cor['description']))

    while "overload" in r.text:
        r = requests.get("https://api.fastpokemap.se",
                         params=parameters, headers=headers)

    try:
        parsed = json.loads(r.text)
    except ValueError:
        pass

    desc = cor['description']

    if 'result' in parsed:
        for pokemon in parsed['result']:
            pokeid = pokemon['pokemon_id']
            print(pokeid)
            tple = (pokeid, desc)
            if pokeid in pokemon_list and tple not in scanned:
                scanned.append((pokeid, desc))
                threading.Timer(600, removePokemon, args=[tple]).start()
                update = "{}: {}".format(index, generateAlert(pokeid, desc, url))
                print(update)
                twapi.PostUpdate(update)
                index = index + 1

                with open('index.pkl', 'wb') as index_file:
                    pickle.dump(index, index_file)
                    index_file.close()

while True:
    for cor in coordinates['coordinates']:
        scan(cor)
