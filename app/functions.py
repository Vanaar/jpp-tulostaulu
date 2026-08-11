from config import Config
import datetime


# Widgetin kokokerroin (?koko=). Rajat estävät sen, että yksittäinen upotus
# tuottaisi mielivaltaisen suuren tai olemattoman pienen taulun.
KOKO_MIN = 0.5
KOKO_MAX = 5.0
KOKO_OLETUS = 1.0


def parsi_koko(arvo):
    """Tulkitsee ?koko=<kerroin> -parametrin. Virheellinen arvo -> 1.0.

    Kerroin annetaan taululle `zoom`-tyylinä, jolloin se skaalautuu
    asettelutasolla ja pysyy terävänä. Striimiohjelman lähteen venyttäminen
    sen sijaan skaalaa valmiin bittikartan ja pehmentää tekstin.
    """
    if arvo is None:
        return KOKO_OLETUS

    try:
        koko = float(str(arvo).strip().replace(",", "."))
    except (TypeError, ValueError):
        return KOKO_OLETUS

    # NaN ei ole yhtä suuri itsensä kanssa; äärettömyydet eivät kelpaa myöskään
    if koko != koko or koko in (float("inf"), float("-inf")):
        return KOKO_OLETUS

    return min(max(koko, KOKO_MIN), KOKO_MAX)


def debug_message(message, level=1):
    if Config.DEBUG and level >= Config.DEBUG_LEVEL:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")

def vuoropari_int_to_str(vuoropari_nro):
    vuoropari_dict = {
        1: "1. aloittava",
        2: "1. lopettava",
        3: "2. aloittava",
        4: "2. lopettava",
        5: "3. aloittava",
        6: "3. lopettava",
        7: "4. aloittava",
        8: "4. lopettava",
        9: "S. aloittava",
        10: "S. lopettava",
        11: "K. aloittava",
        12: "K. lopettava",
        13: "K. jatkoparit",
        14: "Ottelu päättynyt"
    }
    return vuoropari_dict.get(vuoropari_nro, "ERROR: Vuoropari")

def jakso_into_to_str(jakso_nro):
    jakso_dict = {
        1: "1. jakso",
        2: "2. jakso",
        3: "Supervuoro",
        4: "Kotiutuskisa"
    }
    return jakso_dict.get(jakso_nro, "ERROR: Jakso")

def parsi_x_palot(palot: int):
    palot_txt = ""
    for i in range(0, palot):
        palot_txt += "X"
        if (i + 1) % 4 == 0:
            palot_txt += "<br/>"

    return palot_txt
