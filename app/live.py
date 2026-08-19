# live.py
"""
Tulostaulun datamallinnus.

Muodostaa pesistulokset-API:n kahdesta vastauksesta (match + match-live-result)
näkymämallin, jonka tulostaulu.html piirtää sellaisenaan.

API:n kentät pähkinänkuoressa (ks. esimerkit dokumentaatiosta):

    match-live-result:
        periods           {"home": 2, "away": 0}   jaksovoitot
        runs              lista jaksoja, kussakin {"home": [...], "away": [...]}
                          jokainen alkio on yhden vuoroparin juoksut tai null
        outCount          palot
        currentPeriod     viimeksi PÄÄTTYNEEN jakson 0-pohjainen indeksi, ei
                          menossa olevaa: 1. jaksossa -1, 2. jaksossa 0,
                          päättyneessä kaksijaksoisessa ottelussa 1. Menossa
                          oleva jakso on siis currentPeriod + 1 (0-pohjaisena).
        currentInning     menossa oleva vuoropari jakson sisällä, 0-pohjainen.
                          Huom: eri logiikka kuin currentPeriodilla, vaikka
                          kentät ovat samassa vastauksessa. Todennettu
                          8.8.2026 vertaamalla /online/<id>/events -paate-
                          pisteeseen: sen period on 0-pohjainen menossa oleva
                          jakso ja inning identtinen currentInningin kanssa.
        batTurn           0 = aloittava, 1 = lopettava
        batTurnTeamKey    "home" tai "away" = lyömässä oleva joukkue
        finished          onko ottelu päättynyt
        isPeriodMatch     false = vuoroparipeli, ei jaksoja eikä jaksovoittoja

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

# Montako jaksosaraketta jaksopelissä on vähintään: 1. jakso, 2. jakso,
# supervuoro, kotiutuskisa. Todellinen määrä luetaan runs-taulukosta, mutta
# tätä vähemmäksi ei mennä: S-saraketta ei piiloteta, koska pudotuspeleissä
# supervuoro on käytössä eikä API kerro luotettavasti onko ottelu pudotuspeli.
JAKSOJA = 4

# Jaksosarakkeiden otsikot järjestyksessä. Ylimenevät saraketta numeroidaan.
JAKSOJEN_OTSIKOT = ("1", "2", "S", "K")

# Montako vuoroparisaraketta vuoroparipelissä on vähintään. Todellinen määrä
# luetaan runs-taulukosta, mutta kirjaamisen alussa se voi olla tyhjä, eikä
# taulua saa silloin piirtää jaksopelin sarakkeilla. Kahdella mennään, koska
# se on ainoa todennettu muoto (ottelu 146447, junnusuper).
VUOROPAREJA = 2


def _jakson_otsikko(indeksi):
    if indeksi < len(JAKSOJEN_OTSIKOT):
        return JAKSOJEN_OTSIKOT[indeksi]
    return str(indeksi + 1)


def _sarake(otsikko, koti, vieras, aktiivinen=False):
    """Yksi tulostaulun pistesarake.

    aktiivinen = tässä sarakkeessa pelataan juuri nyt. Sisävuoron korostus
    vaatii lisäksi, että joukkue on lyömässä; sen ratkaisee template.
    """
    return {
        "otsikko": otsikko,
        "koti": koti,
        "vieras": vieras,
        "aktiivinen": aktiivinen,
    }


class Ottelu:
    """Tulostaulun näkymämalli."""

    def __init__(self, ottelunumero):
        self.ottelunumero = ottelunumero
        self.kotijoukkue = "Koti"
        self.vierasjoukkue = "Vieras"
        self.koti_jaksovoitot = None
        self.vieras_jaksovoitot = None
        # Pistesarakkeet sellaisina kuin ne piirretään. Jaksopelissä jaksot,
        # vuoroparipelissä vuoroparit.
        self.on_jaksopeli = True
        # Oletusmuoto on jaksopelin tyhjä taulu, jotta peruttu ja alkamaton
        # ottelu piirtyvät samannäköisinä kuin alkava jaksopeli.
        self.sarakkeet = [
            _sarake(_jakson_otsikko(i), None, None) for i in range(JAKSOJA)
        ]
        # Lihavoidun sarakkeen luvut: jaksopelissä jaksovoitot, vuoropari-
        # pelissä juoksut yhteensä.
        self.paapisteet_koti = None
        self.paapisteet_vieras = None
        # Kumpi joukkue on sisävuorossa: "koti", "vieras" tai None. Template
        # korostaa tämän perusteella sekä aktiivisen solun että palorivin.
        self.sisavuoro = None
        self.jakso_nro = 0
        self.jakso_txt = ""
        self.vuoropari_nro = 0
        self.vuoropari_txt = ""
        self.palot = ""
        self.otteluinfo = ""


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


def _jakso_alkanut(juoksut, jakso_idx):
    """Onko jaksossa kirjattu yhtään vuoroparin tulosta kummallekaan."""
    if jakso_idx < 0 or jakso_idx >= len(juoksut):
        return False
    jakso = juoksut[jakso_idx] or {}
    for puoli in ("home", "away"):
        if any(x is not None for x in (jakso.get(puoli) or [])):
            return True
    return False


def _summaa(vuoroparit):
    """Vuoroparien juoksut yhteen. Palauttaa None, jos yhtään ei ole kirjattu."""
    if not vuoroparit:
        return None
    luvut = [v for v in vuoroparit if v is not None]
    if not luvut:
        return None
    return sum(luvut)


def _jaksosarakkeet(juoksut, nykyinen_jakso_idx):
    """Jaksopelin sarakkeet: yksi sarake per jakso, arvona jakson juoksut.

    Sarakkeita on vähintään JAKSOJA, eli S ja K piirretään silloinkin kun
    niitä ei ole pelattu.
    """
    sarakkeet = []

    for i in range(max(JAKSOJA, len(juoksut))):
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

        sarakkeet.append(
            _sarake(_jakson_otsikko(i), koti, vieras, i == nykyinen_jakso_idx)
        )

    return sarakkeet


def _vuoroparisarakkeet(juoksut, nykyinen_vuoropari_idx, vuoro_kaynnissa):
    """Vuoroparipelin sarakkeet: yksi sarake per vuoropari.

    Jaksoja ei ole, joten runs-taulukossa on vain yksi alkio ja sarakkeiden
    määrä luetaan sen pituudesta. `details.inning_count` ei kelpaa tähän:
    ottelussa 146447 se on 4, vaikka vuoropareja pelattiin kaksi.

    Pelaamaton vuoropari jää tyhjäksi, mutta menossa oleva näytetään nollana
    heti kun se alkaa. Muuten sisävuoron korostus osuisi tyhjään soluun siihen
    asti kunnes ensimmäinen juoksu kirjataan. Jaksopelissä sama tehdään
    jaksotasolla `_jaksosarakkeet`issa.
    """
    jakso = (juoksut[0] if juoksut else None) or {}
    koti_juoksut = jakso.get("home") or []
    vieras_juoksut = jakso.get("away") or []

    sarakkeet = []
    for i in range(max(VUOROPAREJA, len(koti_juoksut), len(vieras_juoksut))):
        koti = koti_juoksut[i] if i < len(koti_juoksut) else None
        vieras = vieras_juoksut[i] if i < len(vieras_juoksut) else None

        aktiivinen = i == nykyinen_vuoropari_idx
        if vuoro_kaynnissa and aktiivinen:
            koti = 0 if koti is None else koti
            vieras = 0 if vieras is None else vieras

        sarakkeet.append(_sarake(str(i + 1), koti, vieras, aktiivinen))

    return sarakkeet


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

    Lyöntijärjestys vaihtuu jaksoittain (pelisäännöt 30 §: toisen jakson
    aloittaa sisävuorolla se joukkue, joka aloitti 1. jakson ulkovuorolla).
    Siksi oikea jakso on luettava listasta täsmälleen oikeasta kohdasta:
    väärä indeksi ei anna sinne päin vaan systemaattisesti väärän joukkueen.
    """
    if not tulos:
        return None

    avain = tulos.get("batTurnTeamKey")
    if avain in ("home", "away"):
        return avain

    bat_turn = tulos.get("batTurn")
    paattynyt_jakso_idx = tulos.get("currentPeriod")
    if bat_turn is None or paattynyt_jakso_idx is None or not ottelu_data:
        return None

    # currentPeriod on viimeksi päättyneen jakson indeksi, joten menossa oleva
    # jakso on yhtä suurempi. Ilman tätä 1. jakson arvo -1 indeksoisi listaa
    # lopusta ja 2. jaksossa luettaisiin 1. jakson aloittaja.
    jakso_indeksi = paattynyt_jakso_idx + 1

    first_bat_turns = (ottelu_data.get("meta") or {}).get("first_bat_turns") or []
    if jakso_indeksi < 0 or jakso_indeksi >= len(first_bat_turns):
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
    """Rakentaa Ottelu-olion API-vastauksista.

    ottelu_data = /public/match -vastaus (pakollinen)
    tulos       = /public/match-live-result -vastauksen result-osa tai None
    """
    ottelu = Ottelu(ottelunumero)

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
    # currentPeriod kertoo viimeksi päättyneen jakson, currentInning menossa
    # olevan vuoroparin. Eri logiikka samassa vastauksessa; älä yhtenäistä
    # ilman että todennat sen oikealla käynnissä olevalla ottelulla.
    paattynyt_jakso_idx = tulos.get("currentPeriod")
    if paattynyt_jakso_idx is None:
        paattynyt_jakso_idx = -1

    # Käynnissä olevassa ottelussa menossa on viimeksi päättynyttä seuraava
    # jakso. Päättyneessä ottelussa seuraavaa ei ole: viimeksi päättynyt on
    # myös viimeinen pelattu, eikä pelaamatta jäänyttä supervuoroa saa
    # merkitä alkaneeksi.
    if paattynyt:
        nykyinen_jakso_idx = paattynyt_jakso_idx
    else:
        nykyinen_jakso_idx = paattynyt_jakso_idx + 1

    nykyinen_vuoropari_idx = tulos.get("currentInning") or 0

    # Jaksotauko: edellinen jakso on ratkennut, seuraava ei ole vielä alkanut.
    # currentInning ei nollaudu tauon ajaksi vaan jää edellisen jakson
    # viimeiseen vuoropariin, joten vuoroparia ei voi näyttää. Nollautuu vasta
    # kun uuden jakson ensimmäinen juoksu kirjataan (todennettu ottelussa
    # 130446: inning 3 -> 0 jakson 2 alkaessa).
    jaksotauko = (
        not paattynyt
        and paattynyt_jakso_idx >= 0
        and not _jakso_alkanut(tulos.get("runs") or [], nykyinen_jakso_idx)
    )

    # Onko jollakulla vuoro juuri nyt. Päättyneessä ottelussa ja jaksotauolla
    # ei ole. Tarvitaan jo sarakkeita rakennettaessa, jotta menossa oleva
    # vuoropari osataan erottaa pelaamattomasta.
    vuoro_kaynnissa = not paattynyt and not jaksotauko

    # --- Pistesarakkeet --------------------------------------------------
    # Taulun muoto luetaan datasta: jaksopelissä sarakkeina ovat jaksot,
    # muuten yksittäiset vuoroparit.
    ottelu.on_jaksopeli = on_jaksopeli
    juoksut = tulos.get("runs") or []

    if on_jaksopeli:
        jaksovoitot = tulos.get("periods") or {}
        ottelu.koti_jaksovoitot = jaksovoitot.get("home")
        ottelu.vieras_jaksovoitot = jaksovoitot.get("away")
        ottelu.paapisteet_koti = ottelu.koti_jaksovoitot
        ottelu.paapisteet_vieras = ottelu.vieras_jaksovoitot
        ottelu.sarakkeet = _jaksosarakkeet(juoksut, nykyinen_jakso_idx)
    else:
        # Ei jaksoja eikä jaksovoittoja, joten lihavoituun sarakkeeseen tulee
        # juoksut yhteensä. Se on tässä pelimuodossa ottelun lopputulos.
        ottelu.otteluinfo = "Vuoroparipeli"
        ottelu.sarakkeet = _vuoroparisarakkeet(
            juoksut, nykyinen_vuoropari_idx, vuoro_kaynnissa
        )
        ottelu.paapisteet_koti = _summaa([s["koti"] for s in ottelu.sarakkeet])
        ottelu.paapisteet_vieras = _summaa([s["vieras"] for s in ottelu.sarakkeet])

    # --- Palot ----------------------------------------------------------
    # outCount jää viimeiseen tilaansa, kun vuoro ei ole käynnissä. Päättyneessä
    # ottelussa ja jaksotauolla paloja ei siis näytetä.
    ottelu.palot = parsi_x_palot(tulos.get("outCount") or 0) if vuoro_kaynnissa else ""

    # --- Lyömässä oleva joukkue -----------------------------------------
    # Sama koskee sisävuoroa: päättyneessä ottelussa ja jaksotauolla kukaan ei
    # ole lyömässä, joten korostusta ei näytetä.
    lyova = paattele_lyova_joukkue(tulos, ottelu_data) if vuoro_kaynnissa else None
    if lyova == "home":
        ottelu.sisavuoro = "koti"
    elif lyova == "away":
        ottelu.sisavuoro = "vieras"
    else:
        ottelu.sisavuoro = None
        if vuoro_kaynnissa:
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
    elif not on_jaksopeli:
        # Vuoroparipelissä ei ole jaksoa, jota näyttää: pelkkä vuoropari
        ottelu.jakso_txt = ""
        ottelu.vuoropari_txt = vuoroparin_teksti(
            1, nykyinen_vuoropari_idx, tulos.get("batTurn")
        )
    elif jaksotauko:
        # Alkava jakso näytetään, mutta vuoroparia ei ole vielä olemassa
        ottelu.jakso_txt = jakso_into_to_str(ottelu.jakso_nro)
        ottelu.vuoropari_txt = ""
    else:
        ottelu.jakso_txt = jakso_into_to_str(ottelu.jakso_nro)
        ottelu.vuoropari_txt = vuoroparin_teksti(
            ottelu.jakso_nro, nykyinen_vuoropari_idx, tulos.get("batTurn")
        )

    return ottelu
