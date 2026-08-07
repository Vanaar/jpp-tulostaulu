# jpp-tulostaulu

Junnut Pelaa Pesistä -tulostaulu suomalaisen pesäpallon peleihin.

## Versiot

- **Livetaulu** hakee ottelun tiedot Pesäpalloliiton pesistulokset-API:sta.
  Ei käytä tietokantaa lainkaan.
- **Manuaalitaulu** toimii kuten ennenkin ja käyttää MySQL-tietokantaa.

## Käyttö

Widget upotetaan osoitteella `/<ottelunumero>`, esim.

    https://<palvelin>/129209
    https://<palvelin>/129209?style=siipe
    https://<palvelin>/129209?debug=on

Jos ottelunumero löytyy tietokannasta manuaaliotteluna, näytetään
manuaalitaulu. Muussa tapauksessa tiedot haetaan pesistulokset-API:sta.

## Asennus

1. `pip install -r requirements.txt`
2. Kopioi `config.example.py` -> `config.py` ja täytä tietokanta-asetukset
   sekä `PESISTULOKSET_API_KEY`.
3. Aja:

       flask --app jpp-tulostaulu run --debug --host=0.0.0.0

## API

Livetaulu käyttää kahta julkista päätepistettä:

    GET https://api.pesistulokset.fi/api/v1/public/match?id=<id>&apikey=<avain>
    GET https://api.pesistulokset.fi/api/v1/public/match-live-result?id=<id>&apikey=<avain>

Vastaukset välimuistitetaan palvelimen muistiin (ks. `config.example.py`),
joten katsojien määrä ei vaikuta API-kutsujen määrään.
