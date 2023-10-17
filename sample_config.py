import logging

loglevel = logging.WARNING
max_number_of_open_notes = 100
upload_to_osm = False
press_enter_to_continue = True
username = ""
password = ""
note_text = """
Här ska finnas en badplats enligt Topo50 från Lantmäteriet. Tyvärr finns varken namn eller beständigt id från Lantmäteriet i dagsläget.
Badplatsen hör hemma i OSM om den är skyltad på något sätt, se https://wiki.openstreetmap.org/wiki/Tag:leisure%3Dbathing_place
Kolla ev med kommunen om vad denna badplats heter och om de är beredda att släppa öppna data om sina (skyltade) badplatser.
Tips: du kan hitta vilken kommun genom att söka på objekt i närheten på openstreetmap.org (pil med frågatecken i kartmenyn)
Deltag i diskussion om denna notimport på forumet: https://community.openstreetmap.org/t/import-av-badplatser-fran-lm-topografi-50/102458/23
#topo50
#badplatsnotimport
#scriptcreatednote
"""
debug = False
user_agent = "geojson2osmnotes by pangoSE, see https://github.com/dpriskorn/geojson2osmnotes"