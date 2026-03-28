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
    """
    Per la scheda matematica il flusso è diverso:
    1. DeepSeek riceve il template e genera SOLO i dati in JSON
    2. Il server sostituisce i dati nel template ed esegue
    """
    d = request.get_json()
    arg    = d.get("argomento","Frazioni")
    classe = d.get("classe","Prima Media")

    template_path = PROTO_DIR / "template_matematica.py"
    if not template_path.exists():
        return jsonify({"error":"Template matematica non trovato"}), 404

    template = template_path.read_text(encoding="utf-8")

    # Chiedi a DeepSeek SOLO i dati, non il codice
    prompt_json = f"""Sei un esperto di matematica per la scuola media.
Devo adattare una scheda di matematica all'argomento: {arg} (classe {classe}).

Rispondi ESCLUSIVAMENTE con questo JSON (nessun testo prima o dopo, nessun markdown):
{{
  "titolo": "titolo breve in maiuscolo per {arg} (max 30 caratteri)",
  "sottotitolo": "breve descrizione di {arg} (max 50 caratteri)",
  "spiegazione_1": "prima riga spiegazione teorica di {arg} (max 88 caratteri, no apostrofi)",
  "spiegazione_2": "seconda riga spiegazione di {arg} (max 105 caratteri, no apostrofi)",
  "vf_1": "affermazione vera o falsa su {arg} (max 72 caratteri, no apostrofi)",
  "vf_2": "seconda affermazione su {arg} (max 72 caratteri, no apostrofi)",
  "vf_3": "terza affermazione su {arg} (max 72 caratteri, no apostrofi)",
  "vf_4": "quarta affermazione su {arg} (max 72 caratteri, no apostrofi)",
  "problema_1a": "testo problema 1 su {arg} (max 80 caratteri, no apostrofi)",
  "problema_1b": "seconda riga problema 1 (max 80 caratteri, no apostrofi)",
  "problema_2a": "testo problema 2 su {arg} (max 80 caratteri, no apostrofi)",
  "problema_2b": "seconda riga problema 2 (max 80 caratteri, no apostrofi)"
}}"""

    try:
        dati_raw = ai(prompt_json, max_tok=500)

        # Pulizia JSON
        if "```" in dati_raw:
            dati_raw = dati_raw.split("```")[1]
            if dati_raw.startswith("json"):
                dati_raw = dati_raw[4:]
            dati_raw = dati_raw.split("```")[0]
        dati_raw = dati_raw.strip()

        dati = json.loads(dati_raw)

    except Exception as e:
        # Fallback con dati minimi
        dati = {
            "titolo": arg.upper()[:30],
            "sottotitolo": "Scheda di matematica",
            "spiegazione_1": "Studia " + arg + " seguendo gli esempi.",
            "spiegazione_2": "Esegui gli esercizi con attenzione e ordine.",
            "vf_1": "La prima affermazione e vera.",
            "vf_2": "La seconda affermazione e falsa.",
            "vf_3": "La terza affermazione e vera.",
            "vf_4": "La quarta affermazione e vera.",
            "problema_1a": "Risolvi il primo problema su " + arg + ".",
            "problema_1b": "Scrivi il procedimento e il risultato.",
            "problema_2a": "Risolvi il secondo problema su " + arg + ".",
            "problema_2b": "Scrivi il procedimento e il risultato."
        }

    # Sostituisci i dati nel template
    q  = chr(34)
    ap = chr(39)
    bu = chr(9679)

    codice = template

    # Fix percorso output
    codice = codice.replace(
        q + "/mnt/user-data/outputs/scheda_matematica.pdf" + q,
        q + "/tmp/out.pdf" + q
    )
    codice = codice.replace(
        'os.makedirs("/mnt/user-data/outputs",exist_ok=True)',
        'os.makedirs("/tmp",exist_ok=True)'
    )

    # Titolo header
    codice = codice.replace(
        'cv.drawString(86,H-32,"LE FRAZIONI")',
        'cv.drawString(86,H-32,"' + dati["titolo"] + '")'
    )

    # Sottotitolo header
    codice = codice.replace(
        'cv.drawString(88,H-50,"Scheda di matematica  ' + chr(183) + '  esercita passo dopo passo")',
        'cv.drawString(88,H-50,"' + dati["sottotitolo"] + ' - Classe ' + classe + '")'
    )

    # Spiegazione teorica riga 1
    codice = codice.replace(
        'cv.drawString(X0,yc-2,"Una FRAZIONE indica quante PARTI prendo di un intero diviso in PARTI UGUALI.")',
        'cv.drawString(X0,yc-2,"' + dati["spiegazione_1"] + '")'
    )

    # Spiegazione teorica riga 2
    codice = codice.replace(
        'cv.drawString(X0,yc-16,"Il numero IN ALTO e' + ap + ' il NUMERATORE (parti prese), quello IN BASSO e' + ap + ' il DENOMINATORE (parti totali).")',
        'cv.drawString(X0,yc-16,"' + dati["spiegazione_2"] + '")'
    )

    # Titolo blocco teoria
    codice = codice.replace(
        '"' + bu + ' 1   CHE COS' + ap + 'E' + ap + ' UNA FRAZIONE?"',
        '"' + bu + ' 1   CHE COS' + ap + 'E' + ap + ' ' + dati["titolo"] + '?"'
    )

    # Affermazioni Vero/Falso
    vf_originali = [
        '2/4 e 1/2 sono frazioni equivalenti perche' + ap + ' 2x2 = 4x1.',
        'Con lo stesso numeratore, la frazione con denominatore maggiore e' + ap + ' la piu' + ap + ' grande.',
        'Per semplificare 6/8 si divide per 2: si ottiene 3/4.',
        'La frazione 3/7 e' + ap + ' maggiore di 3/9 perche' + ap + ' 7 e' + ap + ' minore di 9.',
    ]
    vf_nuovi = [dati["vf_1"], dati["vf_2"], dati["vf_3"], dati["vf_4"]]
    for orig, nuovo in zip(vf_originali, vf_nuovi):
        codice = codice.replace('"' + orig + '"', '"' + nuovo + '"')

    # Problemi
    prob_originali = [
        ('Sara ha mangiato 2/8 di una torta, Luca ne ha mangiata 1/4.',
         'Chi ne ha mangiata di piu' + ap + '? (Suggerimento: trova la fraz. equiv. di 1/4 con den. 8.)'),
        ('Una bottiglia e' + ap + ' piena per 3/4. Ne bevo 1/2.',
         'Quanta acqua rimane? (Suggerimento: trova il denominatore comune 4.)'),
    ]
    prob_nuovi = [
        (dati["problema_1a"], dati["problema_1b"]),
        (dati["problema_2a"], dati["problema_2b"]),
    ]
    for (orig_a, orig_b), (nuovo_a, nuovo_b) in zip(prob_originali, prob_nuovi):
        codice = codice.replace('"' + orig_a + '"', '"' + nuovo_a + '"')
        codice = codice.replace('"' + orig_b + '"', '"' + nuovo_b + '"')

    # Aggiungi chiamata generate()
    if 'if __name__' in codice:
        idx = codice.find('if __name__')
        codice = codice[:idx] + 'generate()\n'
    elif codice.count('generate()') < 2:
        codice += '\ngenerate()\n'

    ok, errore, pdf_bytes = esegui_codice(codice)
    if not ok:
        return jsonify({"error": errore}), 500

    return servi_pdf(pdf_bytes, "Scheda_Matematica_" + arg)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
