# hardcode for now
import logging

loglevel = logging.WARNING
upload_to_osm = False
press_enter_to_continue = True
username = ""
password = ""
note_text = """
Här ska finnas en badplats enligt Topo50 från Lantmäteriet. Tyvärr finns varken namn eller beständigt id från Lantmäteriet i dagsläget.
Badplatsen hör hemma i OSM om den är skyltad på något sätt, se https://wiki.openstreetmap.org/wiki/Tag:leisure%3Dbathing_place
Kolla ev med kommunen om vad denna badplats heter och om de är beredda att släppa öppna data om sina (skyltade) badplatser.
Om en badplats med skyltning upphittas så får ni gärna skapa en issue här https://github.com/salgo60/Svenskabadplatser så vi kan lägga till den i Wikidata också
"""