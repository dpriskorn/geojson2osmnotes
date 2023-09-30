"""
Läs in alla badplatser från Topo50
Läs in alla badplatser via overpass som geojson
För varje badplats i Topo50
  Kolla om badplats finns inom 100m i OSM
  Om badplats inte finns:
     Kolla om not finns i närheten 100m via APIn
     Om not finns:
        Skriv ut Länk till noten
        Vänta på user input
      Om inte finns:
        Logga in/autentisera
        Skapa not med innehållet nedan
        Debug: vänta på input och kolla manuellt att allt blev rätt

Fråga chatgpt hur jag bäst beräknar närheten
av badplatser i osm för varje punkt i topo50 dataframen.
Min gissning är att göra en ny dataframe med distanskolumn
 för varje topo50 punkt och beräkna distansen till alla
  badplatser i osm och filtrera bort allt över 100 m.
Är det feasible?
"""
import logging

import config
from models.GeojsonHandler import GeojsonHandler

logging.basicConfig(level=config.loglevel)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Starting")
    ls = GeojsonHandler()
    ls.start()
