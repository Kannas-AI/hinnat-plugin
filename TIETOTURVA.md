# Hinnat-plugin — tietoturva

Tämä kuvaus on tarkoitettu asiakkaan IT:lle tai sille Claudelle, jota
pyydetään arvioimaan plugin ennen käyttöönottoa. Kaikki alla oleva näkyy
tämän repon koodista; tiedostopolut ovat kansiosta `hinnat/`.

Ylläpitäjä: Kannas (pasi@kannas.ai). Ilmoita haavoittuvuudesta samaan
osoitteeseen — vastaamme ja korjaamme ennen julkista mainintaa.

## Mitä plugin on

Ohut asiakas Kannaksen palvelulle `https://saldo.kannas.ai`. Hinnoittelu,
organisaation hinnastot ja Clauden yksityiskohtainen ohje ovat palvelimella
organisaation avaimen (`hk_…`) takana. Koneella ajetaan vain käynnistin,
palvelinyhteys ja Onnisen saldotarkistus (Onninen ei päästä palvelinta
sisään, vain käyttäjän oman kirjautumisen).

## Mitä koneella ajetaan

- **Session alussa** (`hooks/hooks.json`): pluginin oma Python ajaa
  `scripts/session_start.py`:n. Se lukee avaimen, avaa tarvittaessa
  avainikkunan, hakee organisaation säännöt ja palvelimen ohjeen, ja
  päättyy aina onnistuneesti — se ei koskaan estä sessiota. Se ei lataa eikä
  aja koodia verkosta eikä asenna mitään.
- **Avainikkuna**: Windowsilla `scripts/avain.ps1` (luettava PowerShell,
  annetaan `powershell -Command -`:lle syötteenä, ei koodattuna eikä
  allekirjoittamattomana tiedostona), Macilla järjestelmän oma
  `display dialog` (osascript). Avain kirjoitetaan piilotettuna.
- **Komennot** (`scripts/hinnat.py`): Claude ajaa niitä, kun käyttäjä pyytää
  hintaa tai tarjousta. Claude Coden normaalit luvat pätevät; plugin ei pyydä
  ohittamaan niitä.
- Ei `shell=True`-kutsuja eikä `eval`ia; jokainen aliprosessi saa
  argumenttilistan. Palvelimen antamat tiedostonimet hyväksytään vain
  pelkkinä niminä (ei kansiota, ei `..`), joten palvelin ei voi kirjoittaa
  tiedostoa minnekään muualle kuin `tarjoukset/`-kansioon.

## Mitä koneelta lähtee (vain `saldo.kannas.ai`, HTTPS)

- jokaisessa pyynnössä: organisaation avain (`Authorization`-otsake),
  käyttäjän itse antama etunimi lokia varten (`X-Hinnat-User`) ja pluginin
  versio
- hinnoiteltavat hakusanat ja materiaalilistat (rivit, määrät, huomiot)
- Onnisen saldotarkistuksen tulos (tuotekoodi ja varastomäärä)
- opetetut sanat, kohdesäännöt ja sääntöehdotukset
- organisaation tukkuhinnastotiedostot, kun käyttäjä lataa ne

**Ei lähde koskaan:** salasanat, Onnisen kirjautumisevästeet, käyttäjän omat
säännöt (`me/preferences.md`), tarjoukset tai muut tiedostot koneelta.

## Mitä koneelle tallennetaan

Pluginin datakansioon (`~/.claude/plugins/data/hinnat-…`):

- `.key` — organisaation avain (Macilla tiedostolupa 600). Avain avaa vain
  oman organisaation hinnoittelun, ei näy chatissa eikä lokeissa, ja Kannas
  vaihtaa sen pyynnöstä.
- `state.json`, `rules/` — synkronoidut säännöt ja tila
- `me/preferences.md` — käyttäjän omat säännöt
- `.secrets/onninen_state.json` — vain jos Onnisen live-saldo on otettu
  käyttöön: selaimen kirjautumistila (evästeet), ei salasanaa

Tarjoukset (Excel ja tilaustiedostot) tallentuvat käyttäjän avaamaan
kansioon `tarjoukset/`. Niitä ei lähetetä minnekään.

## Mitä palvelin säilyttää

Organisaatiokohtaisesti, avaimen takana; toinen organisaatio ei näe niitä:
hinnasto (ja edellinen), säännöt, sanasto, sääntöehdotukset, tapahtumaloki
(kuka opetti sanan tai latasi hinnaston) ja käyttömäärät kuukausittain
(tarjousten ja hakujen määrä, arvo ja arvioitu säästö — ei nimiä eikä
listojen sisältöä). Tarjouksia ei säilytetä. Tarjous lasketaan palvelimella,
mutta sitä ei tallenneta. Organisaatio saa datansa ulos ja poistettua
pyynnöstä.

## Palvelimen ohje Claudelle

Session alussa plugin hakee palvelimelta ohjeen (`=== HINNAT-OHJE ===`) ja
antaa sen Claudelle: vastausmuoto, ostajien päätökset, komentojen käyttö.
Ohje päivittyy ilman pluginin julkaisua, jotta korjaukset tavoittavat kaikki
heti. Tämä tarkoittaa, että asiakas luottaa Kannaksen palvelimeen samoin kuin
mihin tahansa SaaS-palveluun. Ohje ei koskaan pyydä Claudea:

- ohittamaan Claude Coden lupia tai ajamaan komentoja kysymättä
- kysymään salasanoja tai avainta chatissa
- lähettämään tiedostoja tai tietoja muualle kuin `saldo.kannas.ai`:hin
- avaamaan selainta muille kuin tukkujen omille sivuille

## Onnisen live-saldo (valinnainen)

Käyttäjä ottaa sen käyttöön itse. Se käyttää koneen omaa Pythonia ja
Playwright-selainosaa, jotka Claude asentaa käyttäjän luvalla. Kirjautuminen
tehdään käyttäjän näkyvässä selainikkunassa omilla tunnuksilla; salasanaa ei
tallenneta eikä se kulje Clauden kautta.

## Mukana tulevat Python-ajoympäristöt

`python/` sisältää Python 3.14:n Windowsille (python.org:n embeddable-paketti)
ja Macille (python-build-standalone, Apple Silicon ja Intel). Lähteet,
pakettien SHA-256-tarkisteet ja jokaisen tiedoston tarkiste ovat tiedostossa
`python/LAHDE.txt`. Windowsin `python.exe` ja DLL:t on allekirjoittanut
Python Software Foundation (tarkista: `Get-AuthenticodeSignature`).

## Versiot ja päivitykset

Jokainen julkaisu on tämän repon tagi `vX.Y.Z`, ja versiosta 2.1.6 alkaen
tagit säilyvät, joten julkaisuja voi verrata keskenään. Claude päivittää
pluginin uusimpaan versioon seuraavassa sessiossa.
