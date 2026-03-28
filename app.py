from flask import Flask, render_template, request, jsonify, session, Response
from functools import wraps
import os, json, subprocess, sys
from openai import OpenAI
from pathlib import Path

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "didattica_segreta_2024")

DEEPSEEK_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
PASSWORD     = os.environ.get("APP_PASSWORD", "Vanbasten")
PROTO_DIR    = Path(__file__).parent / "protocolli"

# ─── Helpers ─────────────────────────────────────────────────────────────────

def leggi_template(nome):
    try:
        return (PROTO_DIR / nome).read_text(encoding="utf-8")
    except:
        return ""

def ai(prompt, max_tok=4096):
    client = OpenAI(api_key=DEEPSEEK_KEY, base_url="https://api.deepseek.com")
    return client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role":"user","content":prompt}],
        max_tokens=max_tok,
        temperature=0.2
    ).choices[0].message.content.strip()

def esegui_codice(codice):
    """Esegue codice Python e restituisce (ok, errore, pdf_bytes)"""
    pdf_path = "/tmp/out.pdf"
    if os.path.exists(pdf_path):
        os.remove(pdf_path)

    # Forza il percorso output
    codice = codice.replace('"/mnt/user-data/outputs/scheda_matematica.pdf"', '"/tmp/out.pdf"')
    codice = codice.replace("'/mnt/user-data/outputs/scheda_matematica.pdf'", "'/tmp/out.pdf'")
    codice = codice.replace('"/tmp/output_scheda.pdf"', '"/tmp/out.pdf"')
    codice = codice.replace("'/tmp/output_scheda.pdf'", "'/tmp/out.pdf'")
    codice = codice.replace('os.makedirs("/mnt/user-data/outputs"', 'os.makedirs("/tmp"')

    # Aggiungi chiamata generate() se necessario
    if "def generate()" in codice and "generate()" not in codice.split("def generate()")[1][-100:]:
        codice += "\ngenerate()\n"

    try:
        r = subprocess.run(
            [sys.executable, "-c", codice],
            capture_output=True, text=True, timeout=90,
            env={**os.environ, "MPLBACKEND":"Agg"}
        )
        if r.returncode != 0:
            return False, r.stderr[-800:], None
        if not os.path.exists(pdf_path):
            return False, "PDF non creato. stdout: " + r.stdout[-300:], None
        with open(pdf_path, "rb") as f:
            return True, None, f.read()
    except subprocess.TimeoutExpired:
        return False, "Timeout (90s)", None
    except Exception as e:
        return False, str(e), None

def servi_pdf(pdf_bytes, nome):
    nome = nome.replace(" ", "_") + ".pdf"
    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={nome}",
            "Content-Length": str(len(pdf_bytes)),
            "Cache-Control": "no-store"
        }
    )

def login_required(f):
    @wraps(f)
    def w(*a, **k):
        if not session.get("ok"):
            return jsonify({"error":"Non autorizzato"}), 401
        return f(*a, **k)
    return w

# ─── Auth ─────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    if not session.get("ok"):
        return render_template("login.html")
    return render_template("index.html")

@app.route("/login", methods=["POST"])
def login():
    if request.get_json().get("password") == PASSWORD:
        session["ok"] = True
        return jsonify({"success":True})
    return jsonify({"success":False})

@app.route("/logout")
def logout():
    session.clear()
    return jsonify({"success":True})

# ─── Genera codice con AI ─────────────────────────────────────────────────────

@app.route("/genera", methods=["POST"])
@login_required
def genera():
    d = request.get_json()
    tipo     = d.get("tipo_id","")
    materia  = d.get("materia","")
    arg      = d.get("argomento","").strip()
    classe   = d.get("classe","Prima Media")
    opzioni  = d.get("opzioni",{})
    note     = opzioni.get("note","")
    bes      = opzioni.get("bes",False)
    dsa      = opzioni.get("dsa",False)

    if not arg:
        return jsonify({"error":"Inserisci un argomento"}), 400

    # Costruisci prompt in base al tipo
    try:
        codice = genera_codice(tipo, materia, arg, classe, note, bes, dsa)
    except Exception as e:
        return jsonify({"error": f"Errore AI: {str(e)}"}), 500

    # Pulizia markdown
    if "```python" in codice:
        codice = codice.split("```python")[1].split("```")[0].strip()
    elif codice.startswith("```"):
        codice = "\n".join(codice.split("\n")[1:])
        if codice.strip().endswith("```"):
            codice = codice.strip()[:-3].strip()

    return jsonify({"success":True, "codice":codice})

def genera_codice(tipo, materia, arg, classe, note, bes, dsa):
    """Chiama DeepSeek e restituisce codice Python pronto"""

    regole = f"""REGOLE ASSOLUTE:
- Rispondi SOLO con codice Python puro, zero testo, zero markdown, zero backtick
- Output PDF: /tmp/out.pdf
- os.makedirs('/tmp', exist_ok=True) subito dopo gli import
- Usa SOLO font Helvetica, Helvetica-Bold, Helvetica-Oblique
- MAI caratteri unicode speciali dentro f-string (usa stringhe normali)
- Codice completo ed eseguibile immediatamente
- Argomento: {arg}, Classe: {classe}
{"- Stile BES/DSA: font grande, frasi brevi, molto spazio" if bes or dsa else ""}
{"- Note aggiuntive: " + note if note else ""}
"""

    if tipo == "scheda_umanistica":
        template = leggi_template("template_umanistica.py")
        palette = {
            "storia":     ("0.52,0.20,0.04","1.00,0.92,0.82","0.80,0.62,0.04","1.00,0.97,0.80","storia","🏛️"),
            "geografia":  ("0.08,0.48,0.54","0.84,0.96,0.97","0.14,0.56,0.22","0.88,0.98,0.88","geografia","🌍"),
            "tecnologia": ("0.20,0.20,0.20","0.94,0.94,0.94","0.88,0.46,0.06","1.00,0.95,0.83","tecnologia","⚙️"),
            "italiano":   ("0.68,0.12,0.12","1.00,0.90,0.90","0.80,0.62,0.04","1.00,0.97,0.80","italiano","📖"),
            "inglese":    ("0.10,0.20,0.55","0.88,0.92,1.00","0.68,0.12,0.12","1.00,0.90,0.90","inglese","🇬🇧"),
            "francese":   ("0.10,0.28,0.70","0.86,0.92,1.00","0.68,0.12,0.12","1.00,0.90,0.90","francese","🇫🇷"),
        }
        pal = palette.get(materia.lower(), palette["storia"])
        return ai(f"""{regole}
Adatta questo template Python per una scheda di {materia} su "{arg}".
C1=({pal[0]}), C1L=({pal[1]}), C2=({pal[2]}), C2L=({pal[3]})
MATERIA_STR="{pal[4]}", ICON_EMOJI="{pal[5]}"
Sostituisci SOLO i contenuti, mantieni tutta la struttura grafica.
TEMPLATE:
{template}""", max_tok=8000)

    elif tipo == "mappa_mentale":
        template = leggi_template("template_mappa_mentale.py")
        return ai(f"""{regole}
Adatta questo template per una mappa mentale su "{arg}".
Modifica SOLO la sezione dati (HUB_LINES, RAMI, CALLOUT).
TEMPLATE:
{template}""", max_tok=8000)

    elif tipo == "mappa_concettuale":
        template = leggi_template("template_mappa_concettuale.py")
        return ai(f"""{regole}
Adatta questo template per una mappa concettuale su "{arg}".
TEMPLATE:
{template}""", max_tok=8000)

    elif tipo == "mappa_gerarchica":
        template = leggi_template("template_mappa_gerarchica.py")
        return ai(f"""{regole}
Adatta questo template per una mappa gerarchica su "{arg}".
TEMPLATE:
{template}""", max_tok=8000)

    else:
        # Tutte le verifiche: genera codice da zero
        info_tipo = {
            "verifica_grammatica":   ("Grammatica Italiana",  "6 esercizi stile EDISCO"),
            "verifica_comprensione": ("Comprensione Testo",   "9 esercizi stile INVALSI"),
            "verifica_storia":       ("Storia",               "9 esercizi 100 punti stile Loescher"),
            "verifica_geografia":    ("Geografia",            "9 esercizi 100 punti stile Loescher"),
            "verifica_scienze":      ("Scienze",              "9 esercizi stile Loescher"),
            "verifica_tecnologia":   ("Tecnologia",           "10 esercizi stile EDISCO"),
            "verifica_inglese":      ("Inglese",              "10 esercizi 60 punti consegne in inglese"),
            "verifica_francese":     ("Francese",             "10 esercizi 60 punti consegne in francese"),
            "verifica_arte":         ("Storia dell Arte",     "10 esercizi con segnaposto immagini"),
            "verifica_musica":       ("Storia della Musica",  "10 esercizi 49 punti"),
            "verifica_motoria":      ("Scienze Motorie",      "10 esercizi 50 punti"),
        }.get(tipo, (materia or "Materia", "9 esercizi"))

        return ai(f"""{regole}
Crea una verifica di {info_tipo[0]} su "{arg}" per classe {classe}.
Struttura: {info_tipo[1]}.
Stile grafico professionale:
- Intestazione con box colorato, titolo bianco, dati studente
- Esercizi numerati con header colorato
- Puntini per le risposte (MAI linee)
- Quadratini per V/F
- Punteggi per ogni esercizio
- Totale finale /100
Output: /tmp/out.pdf""", max_tok=4096)

# ─── Scarica PDF ──────────────────────────────────────────────────────────────

@app.route("/scarica_pdf", methods=["POST"])
@login_required
def scarica_pdf():
    d = request.get_json()
    codice = d.get("codice","")
    nome   = d.get("nome","documento")

    if not codice:
        return jsonify({"error":"Nessun codice"}), 400

    ok, errore, pdf_bytes = esegui_codice(codice)
    if not ok:
        return jsonify({"error": errore}), 500

    return servi_pdf(pdf_bytes, nome)

# ─── Scheda Matematica (route speciale) ───────────────────────────────────────

@app.route("/genera_matematica", methods=["POST"])
@login_required
def genera_matematica():
    d = request.get_json()
    arg    = d.get("argomento", "Frazioni")
    classe = d.get("classe", "Prima Media")

    template_path = PROTO_DIR / "template_matematica.py"
    if not template_path.exists():
        return jsonify({"error": "Template matematica non trovato"}), 404

    template = template_path.read_text(encoding="utf-8")

    # Estrai SOLO la parte statica (helper functions + header/footer)
    # Rimuovi il docstring iniziale che confonde DeepSeek
    idx_blocchi = template.find("# ============" + "=" * 60 + "\n# BLOCCHI")
    if idx_blocchi == -1:
        idx_blocchi = template.find("# BLOCCHI")
    parte_statica = template[:idx_blocchi] if idx_blocchi > 0 else template[:7800]

    # Rimuovi il docstring iniziale (confonde DeepSeek)
    if parte_statica.startswith('"""'):
        fine_doc = parte_statica.find('"""', 3)
        if fine_doc > 0:
            parte_statica = parte_statica[fine_doc + 3:].lstrip()

    # Fix percorso output
    parte_statica = parte_statica.replace(
        '"/mnt/user-data/outputs/scheda_matematica.pdf"',
        '"/tmp/out.pdf"'
    )
    parte_statica = parte_statica.replace(
        'os.makedirs("/mnt/user-data/outputs",exist_ok=True)',
        'os.makedirs("/tmp",exist_ok=True)'
    )

    # Chiedi a DeepSeek di riscrivere SOLO le funzioni degli esercizi
    prompt = f"""Scrivi codice Python per una scheda di matematica su "{arg}" (classe {classe}).

USA queste funzioni gia definite (non ridefinirle):
block_open(cv,y_top,h,title,cb,cl)->yc, frac(cv,cx,cy,num,den,fsz,col),
pizza(cv,cx,cy,r,num,den,fc), write_lines(cv,cx,cy,col),
draw_header(cv), draw_footer(cv), sf(cv,c), ss(cv,c)

Colori: NAVY,NAVYL,ORANGE,ORANGEL,GREEN,GREENL,RED,REDL,TEAL,TEALL,BROWN,BROWNL,PURPLE,PURPLEL,GOLD,WHITE,BLACK,GRAY,GRAYL
Costanti: ML=28, X0=38, X1=557.28, BW=539.28, CW=519.28, TOP=737.89, GAP=7, TH=26
OUT="/tmp/out.pdf" gia definito.

SCRIVI SOLO queste funzioni (niente altro, niente spiegazioni):

def b_teoria(cv, y_top):
    # Spiega {arg} per classe {classe}, h=200
    # Usa block_open(), cv.drawString() con testi su {arg}
    ...

def b_es1(cv, y_top):
    # Esercizio 1 su {arg}, h appropriata
    ...

def b_es2(cv, y_top):
    # Esercizio 2 su {arg}
    ...

def b_es3(cv, y_top):
    # Esercizio 3 su {arg}
    ...

def b_vf(cv, y_top):
    # Vero/Falso su {arg}, 4 affermazioni
    ...

def b_problemi(cv, y_top):
    # 2 problemi su {arg}
    ...

def generate():
    import os; os.makedirs("/tmp", exist_ok=True)
    cv = canvas.Canvas(OUT, pagesize=A4)
    draw_header(cv)
    y = TOP
    y = b_teoria(cv, y)
    y = b_es1(cv, y)
    cv.showPage()
    draw_header(cv); draw_footer(cv)
    y = TOP
    y = b_es2(cv, y)
    y = b_es3(cv, y)
    cv.showPage()
    draw_header(cv); draw_footer(cv)
    y = TOP
    y = b_vf(cv, y)
    y = b_problemi(cv, y)
    cv.showPage()
    cv.save()

REGOLE:
- Solo stringhe normali in drawString (NO f-string con variabili)
- h di ogni blocco deve essere sufficiente per il contenuto
- PAG1 totale max 738pt, PAG2 e PAG3 max 718pt
- Tutto il contenuto riguarda "{arg}", niente frazioni o altro"""

    try:
        funzioni_esercizi = ai(prompt, max_tok=4096)

        # Pulizia markdown
        if "```python" in funzioni_esercizi:
            funzioni_esercizi = funzioni_esercizi.split("```python")[1].split("```")[0].strip()
        elif "```" in funzioni_esercizi:
            funzioni_esercizi = funzioni_esercizi.split("```")[1].split("```")[0].strip()

        # Controllo: DeepSeek ha restituito il template originale invece di generare?
        if "TEMPLATE_SCHEDA_BES" in funzioni_esercizi or "REGOLA FONDAMENTALE" in funzioni_esercizi:
            return jsonify({"error": "DeepSeek ha restituito il template originale invece di generare nuove funzioni. Riprova."}), 500

        # Controllo: il codice contiene le funzioni necessarie?
        if "def generate()" not in funzioni_esercizi and "def b_" not in funzioni_esercizi:
            return jsonify({"error": "DeepSeek non ha generato le funzioni necessarie. Riprova."}), 500

    except Exception as e:
        return jsonify({"error": f"DeepSeek non risponde: {str(e)}"}), 500

    # Componi il codice finale
    sep = chr(10) + chr(10)
    codice = parte_statica + sep + funzioni_esercizi

    # Assicura generate() venga chiamata
    if "def generate()" in codice and codice.count("generate()") < 2:
        codice += chr(10) + "generate()" + chr(10)
    ok, errore, pdf_bytes = esegui_codice(codice)
    if not ok:
        # Log del codice generato per debug
        print("=== CODICE GENERATO (primi 500 char) ===")
        print(codice[:500])
        print("=== ERRORE ===")
        print(errore)
        return jsonify({"error": errore}), 500

    return servi_pdf(pdf_bytes, "Scheda_Matematica_" + arg)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
