# Sauna ja kesäkeittiö – tiedostot

| Kansio | Sisältö |
|---|---|
| `nykytila/` | Saunan nykytila lupapiirustuksista: `sauna_nykytila_pohja_1-50.dxf`, `sauna_nykytila_julkisivut_1-50.dxf`, `sauna_nykytila_pohja_skannausreferenssi.dxf` (+ `sauna_nykytila_skannausalusta.png`) |
| `kesakeittio_VE1/` | VE1: lasitettu etusivu pilarilinjassa, liukuovi etusivulla. Arkit 1–3 (A3, 1:50), esikatselukuvat, `kesakeittio_VE1_3d.html` |
| `kesakeittio_VE2/` | VE2: lasiseinä välipalkin linjassa (y 1046), edessä avoin katos, etureunassa 3 pilaria. **VE2A** terassi katkaistu, **VE2B** terassi säilyy. Arkit 1–3 kummastakin, `kesakeittio_VE2_3d.html` (terassivalinta mallissa) |
| `skriptit/` | `build_nykytila_pohja.py`, `build_nykytila_julkisivut.py`, `build_kesakeittio.py --ve 1\|2A\|2B\|all`, `build_kesakeittio_3d.py` (pohja `kesakeittio_3d_pohja.html`), `photomontage_kesakeittio.py` |
| `vanhat/` | Vanhentuneet luonnokset ja fotomontaasi (avoin, pidempi rakenne) |

Arkit: `arkki1_kattorakenne`, `arkki2_lattiarunko_paaty`, `arkki3_julkisivut`. Mallitila = A3-arkki 1:50.

Kaikki kesäkeittiön tiedostot syntyvät uudelleen komennoilla:

```
python skriptit/build_kesakeittio.py
python skriptit/build_kesakeittio_3d.py
```

`#`-alkuiset tiedostot ovat LibreCADin automaattisia varmuuskopioita.
