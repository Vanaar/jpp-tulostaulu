# live.py
"""
Livetulostaulun datamallinnus.

Muodostaa pesistulokset-API:n kahdesta vastauksesta (match + match-live-result)
näkymämallin, jolla on samat kenttänimet kuin manuaalitaulun Otteludata-mallilla.
Näin sama tulostaulu.html toimii molemmille eikä livetaulu tarvitse tietokantaa.

API:n kentät pähkinänkuoressa (ks. esimerkit dokumentaatiosta):

    match-live-result:
        periods           {"home": 2, "away": 0}   jaksovoitot
        runs              lista jaksoja, kussakin {"home": [...], "away": [...]}
                          jokainen alkio on yhden vuoroparin juoksut tai null
        outCount          palot
        currentPeriod     menossa oleva jakso, 0-pohjainen
        currentInning     menossa oleva vuoropari jakson sisällä, 0-pohjainen
        batTurn           0 = aloittava, 1 = lopettava
        batTurnTeamKey    "home" tai "away" = lyömässä oleva joukkue
        finished          onko ottelu päättynyt
        isPeriodMatch     false = junioriottelu, ei jaksoja

    match:
        home/away         joukkueiden nimet ja id:t
        meta.first_bat_turns  jaksoittain sen joukkueen id, joka aloittaa lyönnin
        canceled/started  ottelun tila
"""

from app.functions import jakso_into_to_str, parsi_x_palot, debug_message

import constants


# Joukkueen koko nimi näytetään, jos se on korkeintaan näin pitkä.
# Muuten käytetään lyhennettä (shorthand).
NIMEN_MAKSIMIPITUUS = 25

# Montako jaksosaraketta tulostaulussa on: 1. jakso, 2. jakso, supervuoro, kotari
JAKSOJA = 4


class LiveOttelu:
    """Tulostaulun näkymämalli. Vastaa kentiltään Otteludata-mallia."""

    def __init__(self, ottelunumero):
        self.ottelunumero = ottelunumero
        # Säilytetään kenttä yhteensopivuuden vuoksi: 1 = data tulee API:sta
        self.pesistulokset = 1
        self.kotijoukkue = "Koti"
        self.vierasjoukkue = "Vieras"
        self.koti_jaksovoitot = None
        self.vieras_jaksovoitot = None
        self.jakso_1_koti_juoksut = None
        self.jakso_1_vieras_juoksut = None
        self.jakso_2_koti_juoksut = None
        self.jakso_2_vieras_juoksut = None
        self.jakso_3_koti_juoksut = None
        self.jakso_3_vieras_juoksut = None
        self.jakso_4_koti_juoksut = None
        self.jakso_4_vieras_juoksut = None
        self.nykyinen_lyontivuoro = "-"
        self.jakso_nro = 0
        self.jakso_txt = ""
        self.vuoropari_nro = 0
        self.vuoropari_txt = ""
        self.palot = ""
        self.otteluinfo = ""

    def aseta_jakson_juoksut(self, jakso_indeksi, koti, vieras):
        setattr(self, f"jakso_{jakso_indeksi + 1}_koti_juoksut", koti)
        setattr(self, f"jakso_{jakso_indeksi + 1}_vieras_juoksut", vieras)


def joukkueen_nimi(joukkue, oletus):
    """Koko nimi jos se on tarpeeksi lyhyt, muuten lyhenne."""
    if not joukkue:
        return oletus

    nimi = (joukkue.get("name") or "").strip()
    lyhenne = (joukkue.get("shorthand") or "").strip()

    if nimi and len(nimi) <= NIMEN_MAKSIMIPITUUS:
        return nimi
    if lyhenne:
        return lyhenne
    return nimi or oletus


def _summaa(vuoroparit):
    """Vuoroparien juoksut yhteen. Palauttaa None, jos yhtään ei ole kirjattu."""
    if not vuoroparit:
        return None
    luvut = [v for v in vuoroparit if v is not None]
    if not luvut:
        return None
    return sum(luvut)


def vuoroparin_teksti(jakso_nro, vuoropari_indeksi, bat_turn):
    """Esim. "3. aloittava". Supervuorossa ja kotarissa vain "aloittava"."""
    puoli = "aloittava" if bat_turn == 0 else "lopettava"

    # Supervuoro (3) ja kotiutuskisa (4): jakson nimi kertoo jo kaiken
    if jakso_nro >= 3:
        if vuoropari_indeksi and vuoropari_indeksi > 0:
            return f"{vuoropari_indeksi + 1}. {puoli}"
        return puoli

    return f"{(vuoropari_indeksi or 0) + 1}. {puoli}"


def paattele_lyova_joukkue(tulos, ottelu_data):
    """Päättelee kumpi joukkue on lyömässä.

    Palauttaa "home", "away" tai None.

    Ensisijaisesti käytetään API:n valmista batTurnTeamKey-kenttää. Jos se
    puuttuu, päättely tehdään ottelun meta.first_bat_turns -listasta: se kertoo
    jaksoittain sen joukkueen id:n, joka aloittaa lyömisen. batTurn 0 tarkoittaa
    aloittavaa ja 1 lopettavaa vuoroparin puoliskoa.
    """
    if not tulos:
        return None

    avain = tulos.get("batTurnTeamKey")
    if avain in ("home", "away"):
        return avain

    bat_turn = tulos.get("batTurn")
    jakso_indeksi = tulos.get("currentPeriod")
    if bat_turn is None or jakso_indeksi is None or not ottelu_data:
        return None

    first_bat_turns = (ottelu_data.get("meta") or {}).get("first_bat_turns") or []
    if jakso_indeksi >= len(first_bat_turns):
        return None

    aloittavan_id = first_bat_turns[jakso_indeksi]
    if aloittavan_id is None:
        return None

    koti_id = (ottelu_data.get("home") or {}).get("id")
    vieras_id = (ottelu_data.get("away") or {}).get("id")

    if aloittavan_id == koti_id:
        aloittava = "home"
    elif aloittavan_id == vieras_id:
        aloittava = "away"
    else:
        return None

    if bat_turn == 0:
        return aloittava
    return "away" if aloittava == "home" else "home"


def rakenna_ottelu(ottelunumero, ottelu_data, tulos):
    """Rakentaa LiveOttelu-olion API-vastauksista.

    ottelu_data = /public/match -vastaus (pakollinen)
    tulos       = /public/match-live-result -vastauksen result-osa tai None
    """
    ottelu = LiveOttelu(ottelunumero)

    ottelu.kotijoukkue = joukkueen_nimi(ottelu_data.get("home"), "Koti")
    ottelu.vierasjoukkue = joukkueen_nimi(ottelu_data.get("away"), "Vieras")

    if ottelu_data.get("canceled"):
        ottelu.otteluinfo = "Ottelu peruttu"
        return ottelu

    if not tulos:
        # {"result": null} -> kirjaus ei ole alkanut
        ottelu.otteluinfo = "Ottelu ei ole alkanut"
        return ottelu

    on_jaksopeli = bool(tulos.get("isPeriodMatch"))
    paattynyt = bool(tulos.get("finished"))
    nykyinen_jakso_idx = tulos.get("currentPeriod") or 0
    nykyinen_vuoropari_idx = tulos.get("currentInning") or 0

    # --- Jaksovoitot ---------------------------------------------------
    if on_jaksopeli:
        jaksovoitot = tulos.get("periods") or {}
        ottelu.koti_jaksovoitot = jaksovoitot.get("home")
        ottelu.vieras_jaksovoitot = jaksovoitot.get("away")
    else:
        ottelu.otteluinfo = "Junioriottelu"

    # --- Jaksojen juoksut ----------------------------------------------
    juoksut = tulos.get("runs") or []

    for i in range(JAKSOJA):
        jakso = juoksut[i] if i < len(juoksut) else None
        koti = _summaa((jakso or {}).get("home"))
        vieras = _summaa((jakso or {}).get("away"))

        # Alkanut jakso näytetään nollana, vasta alkamaton jätetään tyhjäksi
        alkanut = i <= nykyinen_jakso_idx or koti is not None or vieras is not None
        if alkanut and jakso is not None:
            koti = 0 if koti is None else koti
            vieras = 0 if vieras is None else vieras
        elif not alkanut:
            koti = None
            vieras = None

        ottelu.aseta_jakson_juoksut(i, koti, vieras)

    # --- Palot ----------------------------------------------------------
    ottelu.palot = parsi_x_palot(tulos.get("outCount") or 0)

    # --- Lyömässä oleva joukkue -----------------------------------------
    lyova = paattele_lyova_joukkue(tulos, ottelu_data)
    if lyova == "home":
        ottelu.nykyinen_lyontivuoro = ottelu.kotijoukkue
    elif lyova == "away":
        ottelu.nykyinen_lyontivuoro = ottelu.vierasjoukkue
    else:
        ottelu.nykyinen_lyontivuoro = "-"
        debug_message(
            f"Lyömässä olevaa joukkuetta ei voitu päätellä (ottelu {ottelunumero})",
            constants.DEBUG_MESSAGE_LEVEL_WARN,
        )

    # --- Jakso ja vuoropari ----------------------------------------------
    ottelu.jakso_nro = nykyinen_jakso_idx + 1
    ottelu.vuoropari_nro = nykyinen_vuoropari_idx + 1

    if paattynyt:
        # Koko taulu näytetään, mutta tilateksti kertoo ottelun päättyneen
        ottelu.jakso_txt = "Ottelu on päättynyt"
        ottelu.vuoropari_txt = ""
    else:
        ottelu.jakso_txt = jakso_into_to_str(ottelu.jakso_nro)
        ottelu.vuoropari_txt = vuoroparin_teksti(
            ottelu.jakso_nro, nykyinen_vuoropari_idx, tulos.get("batTurn")
        )

    return ottelu
