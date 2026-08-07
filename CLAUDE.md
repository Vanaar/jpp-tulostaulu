# CLAUDE.md

Junnut Pelaa Pesistä -tulostaulu: Flask-sovellus, joka tarjoaa upotettavan
pesäpallon tulostaulu-widgetin osoitteessa `/<ottelunumero>`. Kaksi eri
tulostaulua saman URL-rakenteen takana:

- **Livetaulu** hakee tiedot Pesäpalloliiton pesistulokset-API:sta. Ei käytä
  tietokantaa. Tämä on aktiivisen kehityksen kohde.
- **Manuaalitaulu** on käsin päivitettävä (`/paivita/<numero>`) ja käyttää
  MySQL:ää. Toimii, eikä siihen ole tarkoitus koskea.

Koodi, kommentit, muuttujanimet ja käyttöliittymätekstit ovat suomeksi. Jatka
samalla tavalla.

## Haarat

`pt3.0` on nykyinen kehityshaara (API-toteutus). `pt2.0` on edellinen versio,
joka scrapesi pesistulokset.fi:tä Seleniumilla. `main` on vanha. Jos etsit
"miten tämä ennen toimi", katso `pt2.0`, älä `main`.

## Ajaminen ja testit

```
flask --app jpp-tulostaulu run --debug --host=0.0.0.0
python -m unittest discover -s tests -v
python tools/esikatselu.py > esikatselu.html   # renderöi taulun eri tiloissa
```

## Gotchat

**`config.py` puuttuu repostä ja ilman sitä mikään ei importtaudu.** Se on
`.gitignore`ssa (sisältää tietokannan salasanan ja API-avaimen). Jokainen
moduuli tekee `from config import Config` importin yhteydessä. Kopioi
`config.example.py` → `config.py`, jos ympäristö on tyhjä. Uudet asetukset
luetaan `getattr(Config, 'NIMI', oletus)` -tyyliin, jotta vanha `config.py` ei
kaada sovellusta.

**Käynnistystiedoston nimessä on väliviiva** (`jpp-tulostaulu.py`), joten sitä
ei voi importata. Testit rakentavat Flask-sovelluksen itse funktiolla
`luo_sovellus()` tiedostossa `tests/test_reitit.py`. Jos lisäät reitin tai
muutat blueprintin rekisteröintiä, muutos pitää tehdä molempiin.

**Yksi template palvelee kahta täysin eri datamallia.** `tulostaulu.html`
saa joko SQLAlchemy-olion (`app/models.py: Otteludata`) tai `LiveOttelu`-olion
(`app/live.py`). `LiveOttelu` on tarkoituksella duck-typattu vastaamaan
kenttänimiltään kantamallia. **Jos lisäät templateen kentän, lisää se
molempiin** — muuten toinen taulu hajoaa hiljaa.

**Sisävuoron korostus perustuu joukkueen nimen vertailuun**
(`ottelu.nykyinen_lyontivuoro == ottelu.kotijoukkue`). Se on peräisin
manuaalitaulusta. Jos joukkueilla olisi identtinen näyttönimi, korostus menisi
molempiin riveihin. Älä riko tätä sopimusta ilman että korjaat manuaalipuolen
samalla.

**`palot` on HTML-merkkijono, joka renderöidään `|safe`-suodattimella.**
`parsi_x_palot()` tuottaa vain `X`- ja `<br/>`-merkkejä. Pidä se sellaisena.

**Widgetin URL-sopimus on julkinen eikä sitä saa muuttaa:** `/<ottelunumero>`,
valinnaiset `?style=<default|siipe>` ja `?debug=on`. Tauluja on upotettu
ulkopuolisille sivuille.

### pesistulokset-API:n kummallisuudet

Kaksi päätepistettä, molemmat `?id=<numero>&apikey=<avain>`:
`/public/match` (joukkueet, meta, lopputulos) ja `/public/match-live-result`
(elävä tilanne). Esimerkkivastaukset ovat `tests/test_live.py`:n vakioina —
käytä niitä totuutena, älä arvaa kenttien muotoa.

- **`currentPeriod` ja `currentInning` ovat 0-pohjaisia**, tulostaulun
  `jakso_nro` ja `vuoropari_nro` 1-pohjaisia.
- **`batTurn`: 0 = aloittava, 1 = lopettava.** `batTurnTeamKey` (`"home"`/
  `"away"`) kertoo lyövän joukkueen suoraan. Varapolku on `meta.first_bat_turns`,
  jossa on jaksoittain lyönnin aloittavan joukkueen id — vertaa `home.id` /
  `away.id`:hen. Molemmat polut ovat `app/live.py: paattele_lyova_joukkue`.
- **`null` ei ole 0.** `runs`-taulukot on esitäytetty nulleilla koko jakson
  mitalta. Pelaamaton vuoropari on `null` (esim. kotijoukkue johtaa eikä lyö
  viimeistä vuoroparia — ottelussa 129209 näin käy jakson 1 lopussa). Jakson
  summa on ei-null-arvojen summa; jos jakso ei ole alkanut, arvo on `None` ja
  solu jää tyhjäksi.
- **Alkamaton ottelu palauttaa `{"result": null}`.** Joukkueiden nimet saa silti
  `/match`-kutsulla.
- **`isPeriodMatch: false` tarkoittaa junioriottelua**: ei jaksovoittoja, vain
  yksi jaksosarake, otteluinfoksi "Junioriottelu".
- **Päättyneessä ottelussa `batTurn` ja `outCount` jäävät viimeiseen tilaansa.**
  Tuotepäätös: koko taulu näytetään silti normaalisti, vain tilarivillä lukee
  "Ottelu on päättynyt".

### Verkkokutsut ja välimuisti

**Kaikki HTTP-kutsut API:in kulkevat `app/pesistulokset_api.py`:n kautta.** Älä
kutsu `requests`ia suoraan reiteistä. Moduulissa on prosessin sisäinen
TTL-välimuisti, jonka koko pointti on että katsojamäärä ei vaikuta
API-kutsujen määrään. `tests/test_reitit.py` vahtii tätä: 20 selainpyyntöä saa
aiheuttaa korkeintaan 2 API-kutsua.

Välimuistin ja reitityspäätösten dictit eivät koskaan tyhjene itsestään. Muutaman
ottelun palvelimella tämä on merkityksetöntä, mutta jos jotain muuttuu, se on
tiedostettu asia eikä unohdus.

### Tietokantariippuvuus

Livetaulun **täytyy** toimia ilman tietokantaa. `MANUAALITAULU_KAYTOSSA = False`
ajaa sovelluksen kokonaan ilman kantaa, ja `tests/test_reitit.py`:n
`IlmanTietokantaaTesti` varmistaa ettei `get_db`-kutsua tapahdu. `app.db`
importataan tarkoituksella funktioiden sisällä, ei moduulin alussa.

Reitityssääntö: numero on manuaaliottelu jos ja vain jos se löytyy kannasta
rivinä, jossa `pesistulokset = 0`. **Kannassa on vanhoja `pesistulokset = 1`
-rivejä** ajalta jolloin scrape kirjoitti tuloksia kantaan. Ne eivät ole
manuaaliotteluita vaan ohjautuvat API-polulle. Älä poista tätä tarkistusta.

## Tiedostot

| Tiedosto | Vastuu |
| --- | --- |
| `app/pesistulokset_api.py` | HTTP-kutsut + välimuisti + virheensieto |
| `app/live.py` | API-vastaus → tulostaulun näkymämalli |
| `app/routes.py` | Reititys live/manuaali, ei bisneslogiikkaa |
| `app/db.py`, `app/models.py` | Vain manuaalitaulu |
| `app/functions.py` | Jaettuja apufunktioita molemmille tauluille |
| `app/templates/tulostaulu.html` | Itse taulu, haetaan selaimeen 5 s välein |
| `app/templates/ottelu.html` | Widgetin kehyssivu + pollaus |
| `tools/esikatselu.py` | Ei osa sovellusta; renderöi taulun eri tiloissa |

## Tiedossa olevat avoimet kohdat

- **Lyömässä olevan joukkueen päättelyä ei ole vahvistettu oikealla käynnissä
  olevalla ottelulla** — vain esimerkkidatalla ja käsin rakennetulla
  testitilanteella. Tämä on tärkein asia todentaa seuraavan ottelun aikana.
- Supervuoron ja kotiutuskisan käyttäytyminen API:ssa on päätelty
  `runs`-taulukon rakenteesta, ei nähty oikeassa ottelussa.
- `/uusi` ja `/paivita` ovat ilman mitään tunnistautumista.
- `app/db.py`:n istunnonhallinta on omalaatuista (`update_match` sulkee
  yhteyden `finally`-lohkossa, `get_match_by_ottelunumero` luo uuden istunnon
  joka kutsulla). Peruja vanhasta versiosta; ei koskettu tässä refaktoroinnissa.

## Cowork-sessioissa

Koneen paikallinen Linux-VM (`device_bash`) ei ole aina käytettävissä, jolloin
git-komentoja ei voi ajaa etänä. Silloin: kirjoita tiedostot
`device_commit_files`illä ja anna käyttäjälle git-komennot ajettavaksi.
Älä koskaan ylikirjoita `config.py`:tä — siinä ovat tuotannon tunnukset.
