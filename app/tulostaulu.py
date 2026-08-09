# tulostaulu.py
"""Tulostaulun näkymämalli: ainoa asia, jonka molemmat taulut jakavat.

Aiemmin livetaulu jäljitteli manuaalitaulun tietokantariviä (`Otteludata`)
kenttä kentältä, jotta sama template kelpaisi molemmille. Se sitoi livetaulun
kannan sarakemuotoon: kahdeksan litteää `jakso_N_koti_juoksut` -kenttää,
sisävuoro joukkueen näyttönimenä ja palot HTML-merkkijonona.

Nyt kumpikin taulu rakentaa oman sovittimensa avulla tämän `Tulostaulu`-olion:

    app/live.py      pesistulokset-API   -> Tulostaulu
    app/manuaali.py  Otteludata-kantarivi -> Tulostaulu

Template näkee vain `Tulostaulu`-olion eikä tiedä kumpi taulu on kyseessä.
Uusi kenttä lisätään tähän, jolloin Python pakottaa täyttämään sen molemmissa
sovittimissa - ennen kentän saattoi lisätä vain toiseen ja toinen taulu hajosi
hiljaa.
"""

from dataclasses import dataclass, field


# Jaksosarakkeiden otsikot: 1. jakso, 2. jakso, supervuoro, kotiutuskisa.
JAKSOJEN_OTSIKOT = ("1", "2", "S", "K")

# Junioriottelussa ei ole jaksoja lainkaan, vain yksi tulossarake.
JUNIORIN_OTSIKOT = ("1",)

KOTI = "koti"
VIERAS = "vieras"


@dataclass
class Jakso:
    """Yksi jaksosarake tulostaulussa.

    `koti` ja `vieras` ovat None, jos jakso ei ole alkanut - silloin solu jää
    tyhjäksi. Alkanut mutta pisteetön jakso on 0, ei None.
    """

    otsikko: str
    koti: int | None = None
    vieras: int | None = None
    aktiivinen: bool = False


@dataclass
class Tulostaulu:
    """Kaikki mitä tulostaulun renderöintiin tarvitaan.

    tilanne_txt  Tilarivin vasen solu: mitä ottelussa juuri nyt tapahtuu
                 ("1. jakso / 2. aloittava") tai ottelun tila, jos mitään ei
                 tapahdu ("Ottelu on päättynyt", "Ottelu ei ole alkanut").
    info_txt     Tilarivin oikea solu: ottelua koskeva lisätieto
                 ("Junioriottelu"). Tyhjä, jos lisättävää ei ole.

    Aiemmin nämä kaksi solua jakoivat kentät `jakso_txt` ja `otteluinfo`
    piilotetulla sopimuksella: jos `jakso_txt` oli asetettu, `otteluinfo`
    siirtyi oikeaan soluun, muuten vasempaan. Nyt kummallakin solulla on oma
    kenttänsä.
    """

    ottelunumero: int
    kotijoukkue: str = "Koti"
    vierasjoukkue: str = "Vieras"
    koti_jaksovoitot: int | None = None
    vieras_jaksovoitot: int | None = None
    jaksot: list[Jakso] = field(default_factory=list)
    # KOTI, VIERAS tai None. Ei joukkueen nimi: nimivertailu korosti molemmat
    # rivit, jos joukkueilla oli sama näyttönimi.
    sisavuoro: str | None = None
    # Palojen lukumäärä. Ei HTML-merkkijonoa - template piirtää X:t.
    palot: int = 0
    tilanne_txt: str = ""
    info_txt: str = ""
    # "api" tai "manuaali". Näytetään vain debug-rivillä.
    lahde: str = "api"

    @property
    def sarakkeita(self):
        """Taulun sarakkeiden määrä: joukkue, jaksovoitot, jaksot ja palot."""
        return 2 + len(self.jaksot) + 1


def jakson_nimi(jakso_nro):
    """1 -> "1. jakso", 3 -> "Supervuoro". Tuntematon -> tyhjä."""
    return {
        1: "1. jakso",
        2: "2. jakso",
        3: "Supervuoro",
        4: "Kotiutuskisa",
    }.get(jakso_nro, "")


def vuoroparin_nimi(jakso_nro, vuoropari_idx, lopettava):
    """Esim. "3. aloittava". Supervuorossa ja kotarissa vain "aloittava".

    Supervuoro ja kotiutuskisa ovat yhden vuoroparin mittaisia, joten
    järjestysnumero olisi turha: jakson nimi kertoo jo kaiken. Mahdolliset
    jatkoparit numeroidaan silti.

    `vuoropari_idx` on 0-pohjainen. Molemmat taulut käyttävät tätä samaa
    funktiota, jotta sama tilanne näyttää samalta kummassakin.
    """
    puoli = "lopettava" if lopettava else "aloittava"

    if jakso_nro >= 3 and vuoropari_idx == 0:
        return puoli

    return f"{vuoropari_idx + 1}. {puoli}"


def tilannerivi(jakso_nro, vuoropari_txt=""):
    """Yhdistää jakson ja vuoroparin tilarivin tekstiksi."""
    jakso_txt = jakson_nimi(jakso_nro)
    if jakso_txt and vuoropari_txt:
        return f"{jakso_txt} / {vuoropari_txt}"
    return jakso_txt or vuoropari_txt
