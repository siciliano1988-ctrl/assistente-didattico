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

    # STEP 1: DeepSeek genera SOLO i testi (JSON piccolo, 400 token)
    # Prompt ricco per ottenere contenuti didattici di qualita
    prompt_json = (
        "Sei un esperto di didattica della matematica per la scuola media italiana." + chr(10) +
        "Crea contenuti didattici RICCHI, PRECISI e COMPLETI su: " + arg + " (classe " + classe + ")." + chr(10) +
        "I testi devono essere adatti a ragazzi di 11-13 anni, chiari, corretti matematicamente." + chr(10) +
        "Rispondi SOLO con JSON valido. Nessun testo extra. Nessun markdown." + chr(10) + chr(10) +
        "{" + chr(10) +
        '  "titolo": "' + arg.upper()[:35] + '",' + chr(10) +
        '  "def1": "Definizione precisa e completa di ' + arg + ' per ragazzi (max 88 char, no apostrofi)",' + chr(10) +
        '  "reg1": "Prima proprieta o regola fondamentale di ' + arg + ' con spiegazione (max 88 char, no apostrofi)",' + chr(10) +
        '  "reg2": "Seconda proprieta o regola di ' + arg + ' con esempio numerico (max 88 char, no apostrofi)",' + chr(10) +
        '  "reg3": "Terza regola o caso speciale di ' + arg + ' (max 88 char, no apostrofi)",' + chr(10) +
        '  "es1": "Esempio numerico completo 1: mostra il calcolo passo per passo (max 65 char)",' + chr(10) +
        '  "es2": "Esempio numerico completo 2: altro caso con numeri diversi (max 65 char)",' + chr(10) +
        '  "es3": "Esempio numerico completo 3: caso piu complesso (max 65 char)",' + chr(10) +
        '  "ese1": "Calcola o risolvi: esercizio specifico su ' + arg + ' con numeri (max 78 char, no apostrofi)",' + chr(10) +
        '  "ese2": "Calcola o risolvi: secondo esercizio su ' + arg + ' con numeri diversi (max 78 char, no apostrofi)",' + chr(10) +
        '  "ese3": "Calcola o risolvi: terzo esercizio piu articolato su ' + arg + ' (max 78 char, no apostrofi)",' + chr(10) +
        '  "ese4": "Esercizio 4: applica una proprieta di ' + arg + ' con numeri specifici (max 78 char, no apostrofi)",' + chr(10) +
        '  "ese5": "Esercizio 5: problema piu complesso che combina regole di ' + arg + ' (max 78 char, no apostrofi)",' + chr(10) +
        '  "ese6": "Esercizio 6: sfida con ' + arg + ' per chi ha capito bene (max 78 char, no apostrofi)",' + chr(10) +
        '  "vf1": "Affermazione VERA specifica e precisa su ' + arg + ' con numeri (max 72 char, no apostrofi)",' + chr(10) +
        '  "vf2": "Affermazione FALSA su ' + arg + ' con un errore comune dei ragazzi (max 72 char, no apostrofi)",' + chr(10) +
        '  "vf3": "Affermazione VERA su una proprieta di ' + arg + ' (max 72 char, no apostrofi)",' + chr(10) +
        '  "vf4": "Affermazione FALSA su ' + arg + ' che sembra vera ma non lo e (max 72 char, no apostrofi)",' + chr(10) +
        '  "prob1": "Problema applicativo 1: contesto reale che usa ' + arg + ' con dati numerici (max 78 char, no apostrofi)",' + chr(10) +
        '  "prob1b": "Seconda riga problema 1: chiedi calcolo specifico con i dati (max 78 char, no apostrofi)",' + chr(10) +
        '  "prob2": "Problema applicativo 2: situazione concreta diversa che usa ' + arg + ' (max 78 char, no apostrofi)",' + chr(10) +
        '  "prob2b": "Seconda riga problema 2: chiedi il risultato con verifica (max 78 char, no apostrofi)"' + chr(10) +
        "}"
    )

    try:
        raw = ai(prompt_json, max_tok=1200)
        print("JSON DeepSeek:", raw[:200])
        # Pulizia
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"): raw = raw[4:]
            raw = raw.split("```")[0]
        t = json.loads(raw.strip())
    except Exception as e:
        print("DeepSeek JSON fallito:", str(e))
        # Fallback con testi generici
        t = {
            "titolo": arg.upper()[:35],
            "def1": arg + " e un concetto fondamentale della matematica.",
            "reg1": "Prima regola importante di " + arg + ".",
            "reg2": "Seconda regola importante di " + arg + ".",
            "es1": "Esempio 1: ...",
            "es2": "Esempio 2: ...",
            "es3": "Esempio 3: ...",
            "ese1": "Esercizio 1: applica " + arg + ".",
            "ese2": "Esercizio 2: calcola usando " + arg + ".",
            "ese3": "Esercizio 3: risolvi con " + arg + ".",
            "ese4": "Esercizio 4: usa le proprieta di " + arg + ".",
            "ese5": "Esercizio 5: problema su " + arg + ".",
            "ese6": "Esercizio 6: verifica con " + arg + ".",
            "vf1": "La prima affermazione su " + arg + " e vera.",
            "vf2": "La seconda affermazione su " + arg + " e falsa.",
            "vf3": "La terza affermazione su " + arg + " e vera.",
            "vf4": "La quarta affermazione su " + arg + " e vera.",
            "prob1": "Problema 1: applica " + arg + " per risolvere.",
            "prob1b": "Mostra il procedimento e scrivi il risultato.",
            "prob2": "Problema 2: usa " + arg + " per trovare il risultato.",
            "prob2b": "Mostra il procedimento e scrivi il risultato."
        }

    # STEP 2: genera PDF con template Python hardcoded
    q = chr(34)
    bul = chr(9679)

    codice = """
import os
os.makedirs('/tmp', exist_ok=True)
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import math

W, H = A4
cv = canvas.Canvas('/tmp/out.pdf', pagesize=A4)
ML, MR = 28, 28
BW = W - ML - MR
X0 = ML + 10
GAP = 7
NAVY=(0.10,0.20,0.55); NAVYL=(0.88,0.92,1.00)
ORANGE=(0.88,0.46,0.06); ORANGEL=(1.00,0.95,0.83)
GREEN=(0.14,0.56,0.22); GREENL=(0.88,0.98,0.88)
RED=(0.68,0.12,0.12); REDL=(1.00,0.90,0.90)
TEAL=(0.08,0.48,0.54); TEALL=(0.84,0.96,0.97)
BROWN=(0.52,0.28,0.05); BROWNL=(1.00,0.94,0.82)
GOLD=(0.80,0.62,0.04)
WHITE=(1,1,1); BLACK=(0.05,0.05,0.05)
GRAY=(0.48,0.48,0.48); GRAYL=(0.95,0.95,0.95)

def sf(c): cv.setFillColorRGB(*c)
def ss(c): cv.setStrokeColorRGB(*c)

def header():
    # Gradiente header
    for i in range(30):
        t=i/30
        r=0.10+(0.25-0.10)*t; g=0.20+(0.55-0.20)*t; b=0.55+(0.90-0.55)*t
        cv.setFillColorRGB(r,g,b)
        y=H-78+i*(78/30)
        cv.rect(0,y,W,78/30+0.5,fill=1,stroke=0)
    sf(WHITE); cv.setFont('Helvetica-Bold',22)
    cv.drawString(86,H-38,""" + q + t["titolo"] + q + """)
    sf((0.85,0.92,1.00)); cv.setFont('Helvetica',11)
    cv.drawString(88,H-56,""" + q + "Scheda di matematica - Classe " + classe + q + """)
    sf(NAVYL); cv.roundRect(ML,H-100,BW,22,5,fill=1,stroke=0)
    sf(BLACK); cv.setFont('Helvetica',9)
    cv.drawString(X0,H-89,"Nome: _________________   Cognome: _________________   Classe: ______   Data: __________")

def footer():
    sf(GRAYL); cv.rect(0,0,W,20,fill=1,stroke=0)
    sf(GRAY); cv.setFont('Helvetica-Oblique',7.5)
    cv.drawCentredString(W/2,6,"Prof. A. Giuffrida  -  Matematica")

def blocco(y_top, h, titolo, cb, cl):
    bx=ML; by=y_top-h
    sf(cl); cv.roundRect(bx,by,BW,h,7,fill=1,stroke=0)
    ss(cb); cv.setLineWidth(1.5)
    cv.roundRect(bx,by,BW,h,7,fill=0,stroke=1)
    sf(cb); cv.roundRect(bx,y_top-26,BW,26,7,fill=1,stroke=0)
    sf(WHITE); cv.setFont('Helvetica-Bold',9.5)
    cv.drawString(X0,y_top-18,titolo)
    return y_top-26-9

TOP = H-104

# ── PAGINA 1 ──────────────────────────────────────────────────────
header()
y = TOP

# Blocco 1 - Teoria (h=230 per contenere anche reg3)
yc = blocco(y, 230, """ + q + bul + " 1   " + t["titolo"] + q + """, NAVY, NAVYL)
# Box definizione
cv.setFillColorRGB(0.93,0.95,1.0)
cv.roundRect(X0, yc-38, BW-20, 34, 5, fill=1, stroke=0)
sf(NAVY); cv.setFont('Helvetica-Bold',9)
cv.drawString(X0+6, yc-8, "DEFINIZIONE")
sf(BLACK); cv.setFont('Helvetica',9.5)
cv.drawString(X0+6, yc-22, """ + q + t["def1"] + q + """)
# Regole
sf(NAVY); cv.setFont('Helvetica-Bold',9)
cv.drawString(X0, yc-52, "REGOLE FONDAMENTALI")
sf(BLACK); cv.setFont('Helvetica',9.5)
cv.drawString(X0+6, yc-66, """ + q + "1.  " + t["reg1"] + q + """)
cv.drawString(X0+6, yc-82, """ + q + "2.  " + t["reg2"] + q + """)
cv.drawString(X0+6, yc-98, """ + q + "3.  " + t.get("reg3","") + q + """)
# Esempi
sf(ORANGE); cv.setFont('Helvetica-Bold',9)
cv.drawString(X0, yc-118, "ESEMPI:")
sf(BLACK); cv.setFont('Helvetica',9.5)
cv.drawString(X0+6, yc-132, """ + q + "a)  " + t["es1"] + q + """)
cv.drawString(X0+6, yc-148, """ + q + "b)  " + t["es2"] + q + """)
cv.drawString(X0+6, yc-164, """ + q + "c)  " + t["es3"] + q + """)
y = y - 230 - GAP

# Blocco 2 - Esercizi
h2 = 160
yc = blocco(y, h2, """ + q + bul + " 2   ESERCIZI" + q + """, ORANGE, ORANGEL)
sf(BLACK); cv.setFont('Helvetica',9.5)
for i,(ese,lett) in enumerate(zip([""" + q + t["ese1"] + q + "," + q + t["ese2"] + q + "," + q + t["ese3"] + q + """], ['a','b','c'])):
    cv.drawString(X0, yc-2-i*38, lett + ")  " + ese)
    cv.setDash([3,4]); ss(GRAY); cv.setLineWidth(0.7)
    cv.line(X0+10, yc-16-i*38, X0+BW-20, yc-16-i*38)
    cv.line(X0+10, yc-28-i*38, X0+BW-20, yc-28-i*38)
    cv.setDash([])
y = y - h2 - GAP

cv.showPage()

# ── PAGINA 2 ──────────────────────────────────────────────────────
header(); footer()
y = TOP

# Blocco 3 - Altri esercizi
h3 = 160
yc = blocco(y, h3, """ + q + bul + " 3   ANCORA ESERCIZI" + q + """, GREEN, GREENL)
sf(BLACK); cv.setFont('Helvetica',9.5)
for i,(ese,lett) in enumerate(zip([""" + q + t["ese4"] + q + "," + q + t["ese5"] + q + "," + q + t["ese6"] + q + """], ['a','b','c'])):
    cv.drawString(X0, yc-2-i*38, lett + ")  " + ese)
    cv.setDash([3,4]); ss(GRAY); cv.setLineWidth(0.7)
    cv.line(X0+10, yc-16-i*38, X0+BW-20, yc-16-i*38)
    cv.line(X0+10, yc-28-i*38, X0+BW-20, yc-28-i*38)
    cv.setDash([])
y = y - h3 - GAP

# Blocco 4 - Vero/Falso
vf_items = [""" + q + t["vf1"] + q + "," + q + t["vf2"] + q + "," + q + t["vf3"] + q + "," + q + t["vf4"] + q + """]
h4 = 26+9 + len(vf_items)*22 + 10
yc = blocco(y, h4, """ + q + bul + " 4   VERO O FALSO?" + q + """, TEAL, TEALL)
sf(BLACK); cv.setFont('Helvetica',9.5)
for i,aff in enumerate(vf_items):
    yr = yc - 8 - i*22
    cv.drawString(X0+4, yr, str(i+1)+".  "+aff)
    ss((0.2,0.6,0.2)); cv.setLineWidth(0.8)
    cv.rect(X0+BW-75, yr-3, 30, 14, fill=0, stroke=1)
    sf((0.2,0.6,0.2)); cv.setFont('Helvetica-Bold',7.5)
    cv.drawCentredString(X0+BW-60, yr+5, "VERO")
    ss((0.7,0.1,0.1))
    cv.rect(X0+BW-40, yr-3, 30, 14, fill=0, stroke=1)
    sf((0.7,0.1,0.1))
    cv.drawCentredString(X0+BW-25, yr+5, "FALSO")
    cv.setFont('Helvetica',9.5)
y = y - h4 - GAP

# Blocco 5 - Problemi
h5 = 140
yc = blocco(y, h5, """ + q + bul + " 5   PROBLEMI" + q + """, BROWN, BROWNL)
sf(BLACK); cv.setFont('Helvetica-Bold',9.5)
cv.drawString(X0, yc-8, "1.  " + """ + q + t["prob1"] + q + """)
cv.setFont('Helvetica',9)
cv.drawString(X0+10, yc-22, """ + q + t["prob1b"] + q + """)
cv.setDash([3,4]); ss(GRAY); cv.setLineWidth(0.7)
cv.line(X0, yc-36, X0+BW-20, yc-36)
cv.line(X0, yc-48, X0+BW-20, yc-48)
cv.setDash([])
cv.setFont('Helvetica-Bold',9.5)
cv.drawString(X0, yc-65, "2.  " + """ + q + t["prob2"] + q + """)
cv.setFont('Helvetica',9)
cv.drawString(X0+10, yc-79, """ + q + t["prob2b"] + q + """)
cv.setDash([3,4]); ss(GRAY); cv.setLineWidth(0.7)
cv.line(X0, yc-93, X0+BW-20, yc-93)
cv.line(X0, yc-105, X0+BW-20, yc-105)
cv.setDash([])

cv.showPage()
cv.save()
print("OK")
"""

    ok, errore, pdf_bytes = esegui_codice(codice)
    if not ok:
        print("ERRORE:", errore)
        return jsonify({"error": errore}), 500

    return servi_pdf(pdf_bytes, "Scheda_Matematica_" + arg)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
