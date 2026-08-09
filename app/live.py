# live.py
"""Livetaulu: pesistulokset-API -> Tulostaulu.

Tämä moduuli on livetaulun ainoa datamallinnus. Se ei tunne tietokantaa eikä
manuaalitaulua: sen ainoa syöte on API:n kaksi vastausta ja ainoa tuotos
`app.tulostaulu.Tulostaulu`.

API:n kentät pähkinänkuoressa:

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
        isPeriodMatch     false = junioriottelu, ei jaksoja

    match:
        home/away         joukkueiden nimet ja id:t
        meta.first_bat_turns  jaksoittain sen joukkueen id, joka aloittaa lyönnin
        canceled/started  ottelun tila
"""

from dataclasses import dataclass

from app.loki import DEBUG_MESSAGE_LEVEL_WARN, debug_message
from app.tulostaulu import (
    JAKSOJEN_OTSIKOT,
    JUNIORIN_OTSIKOT,
    KOTI,
    VIERAS,
    Jakso,
    Tulostaulu,
    tilannerivi,
    vuoroparin_nimi,
)


# Joukkueen koko nimi näytetään, jos se on korkeintaan näin pitkä.
# Muuten käytetään lyhennettä (shorthand).
NIMEN_MAKSIMIPITUUS = 25


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


@dataclass
class OttelunTila:
    """Ottelun etenemisestä pääteltävät asiat yhdessä paikassa.

    Nämä neljä ratkaisevat lähes kaiken muun, joten ne päätellään erillään
    kenttien täyttämisestä.
    """

    paattynyt: bool
    jaksotauko: bool
    jakso_idx: int
    vuoropari_idx: int

    @property
    def vuoro_kaynnissa(self):
        """Onko joku juuri nyt lyömässä.

        Päättyneessä ottelussa ja jaksotauolla ei ole: API jättää `batTurn`in
        ja `outCount`in viimeiseen tilaansa, joten niitä ei saa näyttää.
        """
        return not self.paattynyt and not self.jaksotauko


def paattele_tila(tulos):
    """Päättelee ottelun tilan live-result-vastauksesta."""
    paattynyt = bool(tulos.get("finished"))

    # currentPeriod kertoo viimeksi päättyneen jakson, currentInning menossa
    # olevan vuoroparin. Eri logiikka samassa vastauksessa; älä yhtenäistä
    # ilman että todennat sen oikealla käynnissä olevalla ottelulla.
    #
    # Molemmat luetaan eksplisiittisellä None-tarkistuksella, EI `or 0`
    # -kuviolla: currentPeriod on 1. jaksossa -1, ja `-1 or 0` antaa 0. Juuri
    # se virhe näytti aikanaan väärän jakson ja "ERROR: Jakso" -tekstin.
    paattynyt_jakso_idx = tulos.get("currentPeriod")
    if paattynyt_jakso_idx is None:
        paattynyt_jakso_idx = -1

    vuoropari_idx = tulos.get("currentInning")
    if vuoropari_idx is None:
        vuoropari_idx = 0

    # Käynnissä olevassa ottelussa menossa on viimeksi päättynyttä seuraava
    # jakso. Päättyneessä ottelussa seuraavaa ei ole: viimeksi päättynyt on
    # myös viimeinen pelattu, eikä pelaamatta jäänyttä supervuoroa saa
    # merkitä alkaneeksi.
    jakso_idx = paattynyt_jakso_idx if paattynyt else paattynyt_jakso_idx + 1

    # Jaksotauko: edellinen jakso on ratkennut, seuraava ei ole vielä alkanut.
    # currentInning ei nollaudu tauon ajaksi vaan jää edellisen jakson
    # viimeiseen vuoropariin, joten vuoroparia ei voi näyttää. Nollautuu vasta
    # kun uuden jakson ensimmäinen juoksu kirjataan (todennettu ottelussa
    # 130446: inning 3 -> 0 jakson 2 alkaessa).
    jaksotauko = (
        not paattynyt
        and paattynyt_jakso_idx >= 0
        and not _jakso_alkanut(tulos.get("runs") or [], jakso_idx)
    )

    return OttelunTila(
        paattynyt=paattynyt,
        jaksotauko=jaksotauko,
        jakso_idx=jakso_idx,
        vuoropari_idx=vuoropari_idx,
    )


def paattele_lyova_joukkue(tulos, ottelu_data):
    """Päättelee kumpi joukkue on lyömässä.

    Palauttaa KOTI, VIERAS tai None.

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
    if avain == "home":
        return KOTI
    if avain == "away":
        return VIERAS

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
        aloittava = KOTI
    elif aloittavan_id == vieras_id:
        aloittava = VIERAS
    else:
        return None

    if bat_turn == 0:
        return aloittava
    return VIERAS if aloittava == KOTI else KOTI


def _tyhjat_jaksot(otsikot=JAKSOJEN_OTSIKOT):
    """Jaksosarakkeet ilman tuloksia.

    Alkamaton ja peruttu ottelu näyttää saman levyisen taulun kuin käynnissä
    oleva, vain solut ovat tyhjiä.
    """
    return [Jakso(otsikko=otsikko) for otsikko in otsikot]


def _rakenna_jaksot(juoksut, otsikot, tila):
    """Jaksosarakkeet API:n runs-taulukosta."""
    jaksot = []

    for i, otsikko in enumerate(otsikot):
        jakso = juoksut[i] if i < len(juoksut) else None
        koti = _summaa((jakso or {}).get("home"))
        vieras = _summaa((jakso or {}).get("away"))

        # Alkanut jakso näytetään nollana, vasta alkamaton jätetään tyhjäksi.
        # Tasan mennyt supervuoro (0-0) ei ole sama asia kuin pelaamaton.
        alkanut = i <= tila.jakso_idx or koti is not None or vieras is not None
        if alkanut and jakso is not None:
            koti = 0 if koti is None else koti
            vieras = 0 if vieras is None else vieras
        elif not alkanut:
            koti = None
            vieras = None

        jaksot.append(
            Jakso(
                otsikko=otsikko,
                koti=koti,
                vieras=vieras,
                aktiivinen=(i == tila.jakso_idx),
            )
        )

    return jaksot


def rakenna_ottelu(ottelunumero, ottelu_data, tulos):
    """Rakentaa Tulostaulu-olion API-vastauksista.

    ottelu_data = /public/match -vastaus (pakollinen)
    tulos       = /public/match-live-result -vastauksen result-osa tai None
    """
    taulu = Tulostaulu(
        ottelunumero=ottelunumero,
        kotijoukkue=joukkueen_nimi(ottelu_data.get("home"), "Koti"),
        vierasjoukkue=joukkueen_nimi(ottelu_data.get("away"), "Vieras"),
        jaksot=_tyhjat_jaksot(),
        lahde="api",
    )

    if ottelu_data.get("canceled"):
        taulu.tilanne_txt = "Ottelu peruttu"
        return taulu

    if not tulos:
        # {"result": null} -> kirjaus ei ole alkanut
        taulu.tilanne_txt = "Ottelu ei ole alkanut"
        return taulu

    tila = paattele_tila(tulos)
    on_jaksopeli = bool(tulos.get("isPeriodMatch"))

    # --- Jaksovoitot ja jaksosarakkeet ------------------------------------
    if on_jaksopeli:
        jaksovoitot = tulos.get("periods") or {}
        taulu.koti_jaksovoitot = jaksovoitot.get("home")
        taulu.vieras_jaksovoitot = jaksovoitot.get("away")
        otsikot = JAKSOJEN_OTSIKOT
    else:
        # Junioriottelussa ei ole jaksovoittoja eikä supervuoroa, vain yksi
        # tulossarake.
        taulu.info_txt = "Junioriottelu"
        otsikot = JUNIORIN_OTSIKOT

    taulu.jaksot = _rakenna_jaksot(tulos.get("runs") or [], otsikot, tila)

    # --- Palot ja sisävuoro -----------------------------------------------
    if tila.vuoro_kaynnissa:
        taulu.palot = tulos.get("outCount") or 0
        taulu.sisavuoro = paattele_lyova_joukkue(tulos, ottelu_data)
        if taulu.sisavuoro is None:
            debug_message(
                f"Lyömässä olevaa joukkuetta ei voitu päätellä (ottelu {ottelunumero})",
                DEBUG_MESSAGE_LEVEL_WARN,
            )

    # --- Tilarivi ----------------------------------------------------------
    jakso_nro = tila.jakso_idx + 1

    if tila.paattynyt:
        # Koko taulu näytetään, mutta tilateksti kertoo ottelun päättyneen
        taulu.tilanne_txt = "Ottelu on päättynyt"
    elif tila.jaksotauko:
        # Alkava jakso näytetään, mutta vuoroparia ei ole vielä olemassa
        taulu.tilanne_txt = tilannerivi(jakso_nro)
    else:
        vuoropari_txt = vuoroparin_nimi(
            jakso_nro, tila.vuoropari_idx, lopettava=tulos.get("batTurn") == 1
        )
        if on_jaksopeli:
            taulu.tilanne_txt = tilannerivi(jakso_nro, vuoropari_txt)
        else:
            # Junioriottelussa ei ole jaksoja, joten "1. jakso" olisi
            # harhaanjohtava. Näytetään pelkkä vuoropari.
            taulu.tilanne_txt = vuoropari_txt

    return taulu
