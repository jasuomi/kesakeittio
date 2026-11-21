# Kesäkeittiö – projektin tila

Päivitetty 15.11.2026. Tiedostorakenne: ks. `LUEMINUT.md`. GitHub: yksityinen repo `jasuomi/kesakeittio`, viimeisin commit `2a45bbe` (pushattu).

## Kohde

Kesäkeittiö olemassa olevan hirsisaunan (valmistunut 1990) päätyyn J. Pohjana lupapiirustukset (`../Leimatut rakennuslupapiirustukset.pdf`, sivut 15–17), uudelleenpiirretty `nykytila/`-kansioon.

**Koordinaatit** (kaikissa skripteissä): origo linjojen G/B leikkauksessa, x = rakennuksen pituussuunta (G=0, H=2400, J=5400), y = poikittain (B=0 etuseinä, E=4200 takaseinä). Korot: 0.000 = alimman hirren alapinta = pohjalaatan yläpinta. Nykyinen katto 22,5°, harja N+3.300 linjalla y=2100, räystäät y=−600 / 4800, päädyn räystäs x=6000; kuistin katon jatke x 6000–6410 säilyy. Terassi +0.165, terassilaatta x ≤ 6302, y ≤ 1600 (sen takana laatta päättyy seinälinjaan J, x=5465).

## Sovitut ratkaisut (kaikki vaihtoehdot)

| Osa | Ratkaisu |
|---|---|
| Pituus | 4000 päätyseinän J ulkopinnasta (x 5465 → 9465) |
| Leveys | laatan takareuna y=4265 → porraskaistan etureuna y=−1360 (5625 = 45 lautaa) |
| Porraskaista | terassin edessä 5 × (120 + 5) = 625, koko keittiön pituudelta, alkaa x=2430; puretun etuportaan tilalle terassin jatke +0.165 |
| Lattia | kansilauta 28×120 kyll. pituussuuntaan, yläpinta **+0.028**; runko yläpinta **±0.000 = laatan yläpinta** (korjattu 14.11.) |
| Lattiarunko | pituuspalkit 2×48×123 (6 linjaa, kiinnitys laatan reunaan: terassin kohdalla laatan päätyyn x=6302, sen takana seinälinjaan J), poikkipalkit 48×123 k500 väliin palkkikengillä, reunapalkki terassilaatan takareunaan, pilarianturat ø250 + pilarien anturat 300×300 |
| Pilarit | liimapuu 115×115, takareunassa 4 (jako 1016), päädyssä 5 (jako 1054) |
| Katto | 22,5°, harja nykyisen linjassa, yläpinta +3.130 (40 mm nykyisen katon alapinnan alla), räystäs +2.012, päätyräystäs 500; valokate, ruoteet 25×50 tai 22×100, vasat 48×98 k900 |
| Palkit (C24, todelliset mitat) | väli- ja harjapalkit 2×48×198 naulattu pari (jänne 3,94 m, kiinnitys hirsipäätyyn teräskannakkeilla), reunapalkit 48×123 (alapinta +2.008, vapaa korkeus lattiasta 1980) |
| Takaseinä | umpi koko korkeudelta rakennuksen seinään asti, rankarunko 48×98 k600 + havuvaneri 12 mm + ulkoverhous |
| Jäykistys | kattotason X-tuulisiteet 40×2 molempiin lappeisiin; kannakkeet hirsipäätyyn myös veto/puristus/sivuttaisvoimalle; 1. vasa välikappaleilla hirsien päihin (y 1350, 2850); takareunapalkki nurkkalevyllä E/J-nurkkaan; päädyn uloimmissa väleissä vetotangot ø12 ristiin; nostoankkuroinnit; väliaikainen vinotuenta |

## Vaihtoehdot

- **VE1** – etusivu lasitettu pilarilinjassa (y −8), etureunassa 4 pilaria, liukuovi 1. pilarivälissä (n. 900 × 1880), kiinteä lasi rakennuksen nurkan ja 1. pilarin välissä, pääty lasitettu kokonaan.
- **VE2** – lasiseinä välipalkin alla (y 1046) J-päädystä päätyyn, välipalkki ylähirtenä, kantamaton karmirunko 90×90 GL, 3 moduulia à n. 1205, liukuovi keskellä (n. 1205 × 2270, ovilehti ulkopuolella), pääty lasitettu välipalkista takanurkkaan, edessä avoin katos, etureunassa 3 pilaria (jako 1524), pituuspalkki lasiseinän alle.
  - **VE2A** terassin runko ja kansi katkaistaan lasiseinän sisäpuolelta, kansilaudoitus suoraan betonin päälle (+0.028, sama kuin lattia, laudat yhtenäiset J-päädystä).
  - **VE2B** terassi säilyy, sisälle korotettu taso +0.165 (n. 840 × 510).
- Lopullista vaihtoehtoa ei ole valittu.

## Tuotokset

- DXF-arkit A3 1:50 (mallitila = arkki): `kesakeittio_VE1/`, `kesakeittio_VE2/` (VE2A ja VE2B), kukin arkki1 kattorakenne + rakennetyypit, arkki2 lattiarunko + päätyjulkisivu, arkki3 etu- ja takajulkisivu; esikatselu-PNG:t.
- 3D-mallit (Claude-artifactit, yksityisiä): VE1 https://claude.ai/artifact/Ao584H6cpkneW9iXZhVxph , VE2 (terassivalinta) https://claude.ai/artifact/7fvkAaNTGkazSKr4kwMDiv . Lähde `skriptit/kesakeittio_3d_pohja.html`; julkaisu uudelleen samaan linkkiin muutosten jälkeen.
- Generointi: `python skriptit/build_kesakeittio.py` (kaikki VE:t) ja `python skriptit/build_kesakeittio_3d.py`. Esikatselukuvat renderöity ezdxf + matplotlib -skriptillä (ei repossa).
- Vanhentuneet: `vanhat/` (fotomontaasi ja luonnos kuvaavat vanhaa avointa, pidempää rakennetta).

## Mitoitusoletukset (alustavat)

Lumikuorma maassa 2,5 kN/m² (katolla 2,0), omapaino 0,25 kN/m², C24 fm,d 13,7 MPa (kmod 0,8, γM 1,4), GL30c, taipumaraja L/300. Tarkistetut käyttöasteet: väli/harjapalkit 2×48×198 n. 78 %, taipuma n. 11 mm = L/360 (jänne 3,94 m), reunapalkki 48×123 n. 46 % (VE1 jänne 1016) ja n. 60 % (VE2 jänne 1524). Luonnosmitoitus – tarkistettava rakennesuunnittelussa.

## Seuraava vaihe: rakennesuunnitelma

Sisältö: selostus (CC1, käyttöluokat, kuormat, materiaalit, jäykistys), statiikkalaskelmat (eurokoodit, myös liitokset, nosto, perustukset/routa), perustussuunnitelma, runkopiirustukset, liitosdetaljit 1:5–1:10, puutavara- ja kiinnikeluettelo. Lupaa varten pätevän rakennesuunnittelijan hyväksyntä.

Puuttuvat lähtötiedot:
1. Suunniteltava vaihtoehto (VE1 / VE2A / VE2B)
2. Kunta/sijainti (lumikuorma, tuuli, routasyvyys), ympäristön suojaisuus
3. Maaperä (sora/hiekka/moreeni/savi/kallio), pohjavesi
4. Mitattuna: pohjalaatan ja terassilaatan paksuus, reunan korkeus maasta, reuna-anturat ja routaeristys, kunto; hirsipäädyn J kunto ja korot kannakkeiden kohdalla; nykyisen katon alapinnan korko ja räystäs (valokuvan perusteella poikkeavat hieman lupapiirustuksista)
5. Valokatteen tuote, lasitus- ja liukuovijärjestelmä
6. Perustustapa (betoniplintti / valuputki / ruuviperustus)
7. Raskaat varusteet (tulisija, pizzauuni, grilli, vesipiste), talvikäyttö ja lumenpoisto
8. Rakennuslupatilanne ja vaatiiko kunta nimetyn rakennesuunnittelijan

Jos tietoja ei ole, voidaan aloittaa varovaisilla oletuksilla (esim. lumi 2,75 kN/m², routiva maa) ja merkitä ne selvästi.

## Huomioita työtavasta

- PowerShell 5.1 ei tue `&&`: push komennolla `git -C "C:\Users\jasuo\OneDrive\Documents\Code\sauna_cad" push`.
- Claude Coden automaattinen lupatarkistus on estänyt `git push` -komennon; käyttäjä pushaa itse tai lisää sallintasäännön `Bash(git push:*)`.
- `#`-alkuiset tiedostot ovat LibreCADin varmuuskopioita (.gitignore).
