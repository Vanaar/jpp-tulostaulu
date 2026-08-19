# CLAUDE.md

Junnut Pelaa Pesistä -tulostaulu: Flask-sovellus, joka tarjoaa upotettavan
pesäpallon tulostaulu-widgetin osoitteessa `/<ottelunumero>`. Tiedot haetaan
Pesäpalloliiton pesistulokset-API:sta. **Tietokantaa ei ole.**

Aiemmin tauluja oli kaksi saman URL-rakenteen takana: API-pohjainen livetaulu
ja käsin päivitettävä manuaalitaulu, joka oli ainoa MySQL:ää käyttänyt osa.
Manuaalitaulu poistettiin 4.0:ssa, koska sitä ei käytännössä koskaan käytetty
mutta se piti yllä koko kantariippuvuutta.

Koodi, kommentit, muuttujanimet ja käyttöliittymätekstit ovat suomeksi. Jatka
samalla tavalla.

## Haarat

`main` on tulostaulun virallinen versio ja päähaara (4.0). Haarauta uusi työ
siitä.

Paluureitit, järjestyksessä uusimmasta vanhimpaan:

- **`v3.1`-tagi**: viimeinen versio, jossa manuaalitaulu ja tietokanta ovat
  mukana. Tänne palataan, jos 4.0:n poistoista löytyy jotain tarpeellista.
  `pt3.0`-haara osoittaa samaan 3.0-työhön.
- **`pt2.0`-haara**: sitä edeltävä versio, joka scrapesi pesistulokset.fi:tä
  Seleniumilla. **Tuotanto ajoi pitkään tätä.** Säilytetään paluureittinä —
  älä poista äläkä muuta. Jos etsit "miten tämä ennen toimi", katso `pt2.0`.

Huom: `main` oli pitkään jäljessä, koska tuotantoon vietiin aikanaan `pt2.0`
eikä mainia päivitetty. Tilanne korjattiin 7.8.2026 mergellä `pt3.0` → `main`.
Sitä vanhemmat main-commitit ovat 1.0-aikaa eivätkä kerro nykytilasta.

## Ajaminen ja testit

```
flask --app jpp-tulostaulu run --debug --host=0.0.0.0
python -m unittest discover -s tests -v
python tools/esikatselu.py > esikatselu.html   # renderöi taulun eri tiloissa
```

## Gotchat

**`config.py` puuttuu repostä ja ilman sitä mikään ei importtaudu.** Se on
`.gitignore`ssa (sisältää API-avaimen). Jokainen moduuli tekee
`from config import Config` importin yhteydessä. Kopioi `config.example.py` →
`config.py`, jos ympäristö on tyhjä.

**Puuttuva asetus ei saa kaataa sovellusta — kaikki `Config`-luku menee
`getattr`in läpi.** Tämä ei ole tyyliseikka: 19.8.2026 tuotantoonvienti kaatui
juuri tähän. `app/db.py` kutsui `debug_message`ia ennen `create_engine`ia,
tuotannon `config.py`:stä puuttui `DEBUG_LEVEL`, ja `debug_message` luki sen
suoraan `Config`ista. Syntynyt `AttributeError` jäi `get_db`:n
`except Exception`in alle ja muuttui viestiksi "Tietokantayhteyttä ei voitu
luoda", vaikka kantaan ei koskaan otettu yhteyttä. Jokainen tulostaulu —
myös se joka ei kantaa tarvinnut — palautti 500:n. Kirjoita siis aina
`getattr(Config, 'NIMI', oletus)`, myös silloin kun asetus on
`config.example.py`:ssä. Ainoa pakollinen asetus on `PESISTULOKSET_API_KEY`.

**Käynnistystiedoston nimessä on väliviiva** (`jpp-tulostaulu.py`), joten sitä
ei voi importata. Testit rakentavat Flask-sovelluksen itse funktiolla
`luo_sovellus()` tiedostossa `tests/test_reitit.py`. **Reittejä ei tarvitse
enää muistaa lisätä kahteen paikkaan** — myös `/` on blueprintissä, joten
molemmat saavat reitit samasta lähteestä. Sen sijaan `template_folder`- ja
`static_folder`-polut sekä blueprintin rekisteröinti on yhä pidettävä
yhtenevinä.

**Taulun sarakkeet tulevat datasta, eivät vakioista.** `Ottelu.sarakkeet`
(`app/live.py`) on lista dictejä (`otsikko`, `koti`, `vieras`, `aktiivinen`),
ja template piirtää täsmälleen ne: jaksopelissä jaksot (vähintään 1, 2, S, K)
ja vuoroparipelissä yksittäiset vuoroparit. Lihavoituun sarakkeeseen tulee
`paapisteet_koti` / `paapisteet_vieras`. `aktiivinen` kertoo vain missä
sarakkeessa pelataan; sisävuoron korostukseen tarvitaan lisäksi `sisavuoro`.

**Sisävuoro on eksplisiittinen kenttä.** `Ottelu.sisavuoro` on `"koti"`,
`"vieras"` tai `None`, ja template korostaa sen perusteella sekä aktiivisen
solun että palosolun sijainnin. Aiemmin (3.x) korostus pääteltiin vertaamalla
joukkueen näyttönimeä; sopimus periytyi manuaalitaulusta ja olisi osunut
molempiin riveihin, jos joukkueilla olisi ollut sama nimi. Jaksotauolla,
alkamattomassa ja päättyneessä ottelussa arvo on `None`, jolloin korostusta
eikä paloja näytetä.

**`palot` on HTML-merkkijono, joka renderöidään `|safe`-suodattimella.**
`parsi_x_palot()` tuottaa vain `X`- ja `<br/>`-merkkejä. Pidä se sellaisena.

**Widgetin URL-sopimus on julkinen eikä sitä saa muuttaa:** `/<ottelunumero>`,
`/<ottelunumero>/tulostaulu` sekä valinnaiset `?style=<default|siipe>`,
`?debug=on` ja `?koko=<kerroin>`. Tauluja on upotettu ulkopuolisille sivuille.
Parametreja saa lisätä valinnaisina, mutta olemassa olevia ei saa poistaa
eikä niiden merkitystä muuttaa.

**`/` on ottelunumeron avauslomake, ei hallintakäyttöliittymä.** Kelvollinen
syöte on pelkkiä numeroita; `parsi_ottelunumero` (`app/functions.py`) trimmaa
välilyönnit ja pudottaa etunollat, joten `007` avaa `/7`. Tarkistus tehdään
palvelimella (`GET /?ottelunumero=<syöte>` → 302 tai lomake virheviestin
kanssa), jotta sivu toimii ilman JavaScriptiä; sivun skripti vain säästää
edestakaisen pyynnön. Lomakkeessa on `novalidate`, koska muuten selaimen oma
`pattern`-tarkistus estäisi lähetyksen ennen submit-käsittelijää ja käyttäjä
näkisi selaimen omankielisen kuplan suomenkielisen virheviestin sijaan.
`pattern="[0-9]*"` on siellä vain iOS:n numeronäppäimistöä varten.

**`?koko=` on tarkoitettu striimigrafiikkaan.** Kerroin annetaan
`#tulostaulu`-elementille `zoom`-tyylinä, jolloin taulu skaalautuu
asettelutasolla ja pysyy terävänä; striimiohjelman lähteen venyttäminen sen
sijaan skaalaa valmiin bittikartan. Arvo tulkitaan `app/functions.py:
parsi_koko`issa ja rajataan välille 0.5-5; roska ja puuttuva arvo palauttavat
1.0, jolloin `zoom`-tyyliä ei kirjoiteta lainkaan. Zoom on kehyssivulla eikä
taulufragmentissa, joten se säilyy 5 sekunnin päivitysten yli.

**`ottelu.html`:ssä on oltava viewport-meta.** Ilman sitä mobiiliselain ja osa
webview-toteutuksista olettaa sivun 980 px levyiseksi ja skaalaa taulun
murto-osaan koostaan — samalla kapean upotuksen media-kysely ei osu koskaan.

**Tyylit on jaettu rakenteeseen ja väreihin.** `scoreboard_base.css` sisältää
mitat, typografian ja muodot; `scoreboard_default.css` ja
`scoreboard_siipe.css` asettavat pelkät `--pt-*`-värimuuttujat. `ottelu.html`
lataa ensin basen ja sitten tyylin. Uusi väritys = uusi muuttujatiedosto.
Base-tiedoston säännöt on kirjoitettu `table.scoreboard`-alkuisina, jotta
spesifisyys pysyy samana ja lähdejärjestys ratkaisee — muuten yleinen
solusääntö jyrää yksittäisten solujen värit.

### pesistulokset-API:n kummallisuudet

Kaksi päätepistettä, molemmat `?id=<numero>&apikey=<avain>`:
`/public/match` (joukkueet, meta, lopputulos) ja `/public/match-live-result`
(elävä tilanne). Esimerkkivastaukset ovat `tests/test_live.py`:n vakioina —
käytä niitä totuutena, älä arvaa kenttien muotoa.

- **`currentPeriod` ja `currentInning` lasketaan eri tavalla, vaikka ne ovat
  samassa vastauksessa.** Tämä on API:n pahin ansa, ja se maksoi yhden
  kokonaisen bugikierroksen.
  - `currentInning` on menossa olevan vuoroparin 0-pohjainen indeksi →
    `vuoropari_nro = currentInning + 1`.
  - `currentPeriod` on **viimeksi päättyneen** jakson 0-pohjainen indeksi:
    1. jaksossa `-1`, 2. jaksossa `0`, päättyneessä ottelussa `1` →
    `jakso_nro = currentPeriod + 2`.
  - Todennettu 8.8.2026 otteluilla 130345, 131618, 130446, 130487 ja
    vertaamalla `/online/<id>/events` -päätepisteeseen, jonka `period` on
    aito 0-pohjainen menossa oleva jakso ja `inning` identtinen
    `currentInning`in kanssa. Älä yhtenäistä näitä ilman uutta todennusta.
- **Jaksotauolla `currentInning` ei nollaudu.** Kun jakso ratkeaa, se jää
  edellisen jakson viimeiseen vuoropariin siihen asti, kunnes uuden jakson
  ensimmäinen tulos kirjataan (nähty ottelussa 130446: `inning` 3 → 0).
  Tauko tunnistetaan siitä, että jakso on päättynyt (`currentPeriod >= 0`)
  mutta alkavan jakson `runs`-taulukko on kokonaan `null`. Silloin näytetään
  alkava jakso ilman vuoroparia, eikä sisävuoroa tai paloja näytetä.
- **`meta.first_bat_turns` indeksoidaan `currentPeriod + 1`:llä.** Lyönti-
  järjestys vaihtuu jaksoittain (pelisäännöt 30 §), joten väärä indeksi ei
  anna sinne päin vaan systemaattisesti väärän joukkueen. Negatiivinen
  indeksi lukisi Pythonissa listaa lopusta.
- **Supervuoron aloittajaa ei voi päätellä vuorottelusta.** Sen valitsee
  hutunkeiton voittanut kapteeni vasta 2. jakson jälkeen (30 §), joten
  `first_bat_turns[2]` ja `[3]` ovat `null` siihen asti. Kun ne täyttyvät,
  ne ovat **aina keskenään samat**: kotiutuskisan aloittaa supervuoron
  aloittaja (8 §). `details.draw_of_choice_winner` kertoo hutunkeiton
  voittajan, mutta ei aloittajaa — voittaja saa valita myös ulkovuoron,
  ja niin kävi ottelussa 127482.
- **Supervuoro ja kotiutuskisa jatkavat samaa jaksonumerointia.**
  `currentPeriod` on supervuoron jälkeen 2 ja kotiutuskisan jälkeen 3, eli
  `+2`-sääntö pätee koko ottelun elinkaaren. `runs`-pituudet ovat
  `[4, 4, 1, 1]`: supervuoro**pari** on yksi vuoropari ja kotiutuskisa yksi
  kokonaisuus. `periods` laskee supervuoron tai kotiutuskisan voiton
  jaksovoitoksi, joten lopputulos voi olla 2-1 tai 1-2.
- **Tasan mennyt supervuoro (0-0) ei ole sama kuin pelaamaton.** Ottelussa
  127482 supervuoro päättyi 0-0 ja jatkui kotiutuskisaan; S-sarakkeessa
  lukee tällöin 0, ei tyhjä. Pelaamaton erä on `null` (ottelu 146541).
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
- **`isPeriodMatch: false` tarkoittaa vuoroparipeliä.** Ei jaksoja eikä
  jaksovoittoja: `runs`issa on vain yksi alkio, jonka sisällä ovat pelatut
  vuoroparit. Taulu piirretään silloin vuoropari kerrallaan ja lihavoituun
  sarakkeeseen tulee juoksut yhteensä. Otteluinfoksi tulee "Vuoroparipeli".
  **Termi "junioriottelu" oli väärä ja on poistettu**: kaudella 2026 juniorit
  pelaavat jaksopelejä aivan pienimpiä ikäluokkia lukuun ottamatta, ja
  esimerkiksi Nuorten Ykköspesiksen ottelussa 131618 `isPeriodMatch` on `true`.
  Todennettu 11.8.2026 ottelulla 146447 (junnusuper, F-ikäiset): yksi jakso,
  kaksi vuoroparia, 17-14. Testidatana `tests/test_live.py`:ssä.
- **Vuoroparien määrää ei saa lukea `details.inning_count`ista.** Se on
  ottelussa 146447 `4`, vaikka vuoropareja pelattiin kaksi. Ainoa luotettava
  lähde on `runs`-taulukon muoto. Muita saman ottelun tunnusmerkkejä ovat
  `meta.playing_type: 1` (jaksopeleissä 2), `meta.simple_score_keeping: true`
  ja `series.level: "Junnusuper"`, mutta `isPeriodMatch` on näistä ainoa
  yksiselitteinen — sarjataso ei kerro pelimuotoa.
- **Päättyneessä ottelussa `batTurn` ja `outCount` jäävät viimeiseen tilaansa.**
  Tuotepäätös: koko taulu näytetään silti normaalisti, vain tilarivillä lukee
  "Ottelu on päättynyt".

### Verkkokutsut ja välimuisti

**Kaikki HTTP-kutsut API:in kulkevat `app/pesistulokset_api.py`:n kautta.** Älä
kutsu `requests`ia suoraan reiteistä. Moduulissa on prosessin sisäinen
TTL-välimuisti, jonka koko pointti on että katsojamäärä ei vaikuta
API-kutsujen määrään. `tests/test_reitit.py` vahtii tätä: 20 selainpyyntöä saa
aiheuttaa korkeintaan 2 API-kutsua.

Välimuistin dictit eivät koskaan tyhjene itsestään. Muutaman ottelun
palvelimella tämä on merkityksetöntä, mutta jos jotain muuttuu, se on
tiedostettu asia eikä unohdus.

### Ei tietokantaa

Sovelluksessa ei ole tietokantaa eikä sitä pidä tuoda takaisin.
`tests/test_reitit.py`:n `EiTietokantaaTesti` on regressiovahti: se varmistaa
että `import app.db` nostaa `ModuleNotFoundError` ja ettei `sqlalchemy` päädy
`sys.modules`iin tulostaulupyynnön aikana.

Reitityksestä poistui samalla ottelunumeroiden välimuisti (`_reititys`), jonka
ainoa tehtävä oli välttää kantakysely joka päivityksellä. Numero menee nyt
suoraan API-polulle. `app/pesistulokset_api.py`:n oma TTL-välimuisti on eri
asia ja edelleen välttämätön.

## Tiedostot

| Tiedosto | Vastuu |
| --- | --- |
| `jpp-tulostaulu.py` | Käynnistys: Flask-olio + blueprintin rekisteröinti |
| `app/pesistulokset_api.py` | HTTP-kutsut + välimuisti + virheensieto |
| `app/live.py` | API-vastaus → tulostaulun näkymämalli (`Ottelu`) |
| `app/routes.py` | Reititys, ei bisneslogiikkaa |
| `app/functions.py` | Jaettuja apufunktioita |
| `app/templates/index.html` | Juurisivu: ottelunumeron avauslomake |
| `app/templates/tulostaulu.html` | Itse taulu, haetaan selaimeen 5 s välein |
| `app/templates/ottelu.html` | Widgetin kehyssivu + pollaus |
| `static/css/scoreboard_base.css` | Taulun rakenne, mitat ja muodot |
| `static/css/scoreboard_default.css`, `_siipe.css` | Pelkät värimuuttujat |
| `tools/esikatselu.py` | Ei osa sovellusta; renderöi taulun eri tiloissa |

## Tiedossa olevat avoimet kohdat

- ~~Lyömässä olevan joukkueen päättelyä ei ole vahvistettu~~ **Todennettu
  8.8.2026** viidellä oikealla ottelulla: alkamaton, käynnissä oleva jaksossa
  1 ja 2, jaksotauko, jakson vaihtuminen ja päättynyt. Sisävuoron korostus,
  jakso- ja vuoroparinumerointi sekä palojen kertyminen toimivat.
- ~~Supervuoron ja kotiutuskisan käyttäytyminen on päätelty~~ **Todennettu
  8.8.2026** otteluilla 146541 (ratkesi supervuoroon) ja 127482 (ratkesi
  kotiutuskisaan). Molemmat ovat testidatana `tests/test_live.py`:ssä.
  Päättyneet ottelut on nähty; supervuoroa tai kotiutuskisaa **käynnissä**
  ei vieläkään, mutta logiikka on sama ja lukittu testeillä.
- ~~`isPeriodMatch: false` renderöityi jaksopelin sarakkeilla~~ **Korjattu
  11.8.2026.** Taulun muoto tulee nyt `runs`-taulukosta: jaksopelissä
  sarakkeina ovat jaksot (vähintään 1, 2, S, K) ja vuoroparipelissä
  yksittäiset vuoroparit. Todennettu ottelulla 146447.
- **`details.inning_count` ja `meta.super_inning_in_use` ovat käyttämättä.**
  Säännöt sallivat juniori- ja turnausotteluissa 3 tai 2 vuoroparin jaksot.
  Jaksopelissä koodi olettaa yhä vähintään neljä saraketta; jos `runs`issa on
  enemmän jaksoja, ne piirtyvät, mutta vähempää ei näytetä. `inning_count` ei
  kelpaa lähteeksi (ks. yllä ottelu 146447).
  **S-saraketta ei pidä piilottaa `super_inning_in_use`n
  perusteella** (päätös 11.8.2026): pudotuspeleissä supervuoro on käytössä,
  eikä API kerro suoraan onko ottelu pudotuspeli — `meta.playing_type` oli 2
  kaikissa tarkistetuissa otteluissa. `super_inning_in_use` on kirjurin
  käsin asettama ja vaihtelee otteluittain ilman selvää sääntöä (129010 ja
  130446 `false`, 131618 `true`), joten siihen ei voi luottaa. Tyhjä
  S-sarake on pienempi paha kuin puuttuva.
- **`/online/<id>/events` on dokumentoimaton mutta hyödyllinen.** Se antaa
  ottelun tapahtumat ja ylätasolla luotettavan nykytilan (`period`, `inning`,
  `bat_turn`, `team`). Hyvä ristiintarkistukseen, mutta älä ota tuotannon
  datalähteeksi: dokumentoimaton, eri polun takana, ja `finished` laahaa.
- ~~`/uusi` ja `/paivita` ovat ilman mitään tunnistautumista~~ **Poistuivat
  4.0:ssa manuaalitaulun mukana.** Sovelluksessa ei ole enää yhtään reittiä,
  joka kirjoittaisi mitään; kaikki on lukemista.
- ~~`app/db.py`:n istunnonhallinta on omalaatuista~~ **Poistui 4.0:ssa.**
- **Vanhat manuaaliottelunumerot palauttavat nyt 404:n**, jos numeroa ei
  löydy pesistuloksista. Tiedostettu ja hyväksytty seuraus manuaalitaulun
  poistosta (päätös 19.8.2026).
- **`Ottelu.on_jaksopeli` ja `vuoropari_nro` ovat kentissä mutta template ei
  lue niitä.** `on_jaksopeli` on lukittu testeillä ja kertoo pelimuodon
  suoraan; jätetty paikalleen, koska se on halpa ja kuvaa dataa. Jos taulu
  joskus tarvitsee pelimuotokohtaista logiikkaa, se on jo siinä.

## Cowork-sessioissa

Koneen paikallinen Linux-VM (`device_bash`) ei ole aina käytettävissä, jolloin
git-komentoja ei voi ajaa etänä. Silloin: kirjoita tiedostot
`device_commit_files`illä ja anna käyttäjälle git-komennot ajettavaksi.
Älä koskaan ylikirjoita `config.py`:tä — siinä ovat tuotannon tunnukset.
