# jpp-tulostaulu

Junnut Pelaa Pesistä -tulostaulu suomalaisen pesäpallon peleihin. Upotettava
widget, joka hakee ottelun tiedot Pesäpalloliiton pesistulokset-API:sta.
Tietokantaa ei tarvita.

## Käyttö

Widget upotetaan osoitteella `/<ottelunumero>`, esim.

    https://<palvelin>/129209
    https://<palvelin>/129209?style=siipe
    https://<palvelin>/129209?koko=2
    https://<palvelin>/129209?debug=on

Valinnaiset parametrit:

| Parametri | Arvot | Merkitys |
| --- | --- | --- |
| `style` | `default`, `siipe` | taulun väritys |
| `koko` | 0.5-5 | kokokerroin striimigrafiikkaa varten |
| `debug` | `on` | näyttää päivitystiedot taulun alla |

Juurisivu `/` on ottelunumeron avauslomake: syötetty numero avaa taulun
osoitteeseen `/<ottelunumero>`. Muuta hallintakäyttöliittymää ei ole.

## Asennus

1. `pip install -r requirements.txt`
2. Kopioi `config.example.py` -> `config.py` ja täytä `PESISTULOKSET_API_KEY`.
3. Aja:

       flask --app jpp-tulostaulu run --debug --host=0.0.0.0

Testit:

    python -m unittest discover -s tests -v

## Päivitys 3.x -> 4.0

4.0:ssa manuaalitaulu ja koko tietokantariippuvuus on poistettu. Tuotannon
`config.py`:hyn ei tarvitse koskea, mutta siinä on oltava vähintään
`PESISTULOKSET_API_KEY`; `DEBUG` ja `DEBUG_LEVEL` kannattaa asettaa
eksplisiittisesti.

Poistuneet asetukset (voi poistaa `config.py`:stä; eivät haittaa, mutta mikään
ei enää lue niitä):

- `SQLALCHEMY_DATABASE_URI`, `SQLALCHEMY_TRACK_MODIFICATIONS`
- `MANUAALITAULU_KAYTOSSA`
- `REITITYS_TTL`
- `SECRET_KEY`

Poistuneet reitit: `/uusi` ja `/paivita/<numero>`. Jos jokin vanha
manuaaliottelunumero on upotettuna jonnekin, se ohjautuu jatkossa API-polulle
ja palauttaa 404:n, ellei numeroa löydy pesistuloksista.

Riippuvuudet: `SQLAlchemy`, `mysql`, `mysqlclient` ja `greenlet` on poistettu
`requirements.txt`:stä.

## API

Tulostaulu käyttää kahta julkista päätepistettä:

    GET https://api.pesistulokset.fi/api/v1/public/match?id=<id>&apikey=<avain>
    GET https://api.pesistulokset.fi/api/v1/public/match-live-result?id=<id>&apikey=<avain>

Vastaukset välimuistitetaan palvelimen muistiin (ks. `config.example.py`),
joten katsojien määrä ei vaikuta API-kutsujen määrään.
