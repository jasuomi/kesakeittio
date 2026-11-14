"""Kesäkeittiön 3D-mallit selaimeen (three.js) pohjasta kesakeittio_3d_pohja.html.

Tuottaa:
  kesakeittio_VE1/kesakeittio_VE1_3d.html
  kesakeittio_VE2/kesakeittio_VE2_3d.html   (terassivalinta VE2A katkaistu / VE2B säilyy)
Mitat samat kuin build_kesakeittio.py:ssä.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(HERE, "kesakeittio_3d_pohja.html")

DIMS = {
    "1": """      <dt>Liukuovi</dt><dd>n. 900 × 1900, etusivu</dd>
      <dt>Takaseinä</dt><dd>umpi</dd>
      <dt>Pääty, etusivu</dt><dd>lasi koko korkeus</dd>""",
    "2": """      <dt>Etureunan pilarit</dt><dd>3 kpl, jako 1524</dd>
      <dt>Lasiseinä</dt><dd>välipalkin alla, y 1046</dd>
      <dt>Liukuovi</dt><dd>n. 1205 × 2300</dd>
      <dt>Sisätila</dt><dd>n. 3,9 × 3,2 m</dd>
      <dt>Takaseinä</dt><dd>umpi</dd>""",
}
TERRACE = """<fieldset><legend>Terassi lasiseinän sisäpuolella</legend>
        <label><input type="radio" name="ter" value="cut" id="ter-cut" checked> VE2A: katkaistu, kansi betonin päälle</label>
        <label><input type="radio" name="ter" value="keep" id="ter-keep"> VE2B: säilyy, korotettu taso +0.165</label>
      </fieldset>"""
DESC = {"1": "Lasitettu etusivu, liukuovi etusivulla",
        "2": "Lasiseinä välipalkin linjassa, edessä avoin katos"}

src = open(SRC, encoding="utf-8").read()
for ve, folder in (("1", "kesakeittio_VE1"), ("2", "kesakeittio_VE2")):
    html = (src.replace("__VE__", ve).replace("__VE_DESC__", DESC[ve]).replace("<!--VE_DIMS-->", DIMS[ve])
            .replace("<!--VE2_TERRACE-->", TERRACE if ve == "2" else ""))
    if ve == "2":
        html = html.replace("<h1>Kesäkeittiö VE2</h1>", '<h1>Kesäkeittiö <span id="ve-name">VE2A</span></h1>')
    out = os.path.join(ROOT, folder, f"kesakeittio_VE{ve}_3d.html")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w", encoding="utf-8").write(html)
    print("saved", out)
