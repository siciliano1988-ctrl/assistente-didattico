from flask import Flask, render_template, request, jsonify, send_file, session
from functools import wraps
import os, json, subprocess, sys, traceback
from openai import OpenAI
from pathlib import Path

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "didattica_segreta_2024")

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
PASSWORD = os.environ.get("APP_PASSWORD", "Vanbasten")

PROTO_DIR = Path(__file__).parent / "protocolli"

def leggi_template(nome_file):
    try:
        return (PROTO_DIR / nome_file).read_text(encoding="utf-8")
    except:
        return ""

SYSTEM_BASE = """Sei un assistente specializzato nella creazione di materiali didattici
per la scuola secondaria di primo grado italiana (Prof. A. Giuffrida).

REGOLE ASSOLUTE:
1. Rispondi SEMPRE e SOLO con codice Python puro, senza spiegazioni, senza markdown, senza ```
2. Il codice deve salvare il PDF in: /tmp/output_scheda.pdf
3. Il codice deve essere immediatamente eseguibile senza errori
4. NON usare LaTeX, usa SEMPRE ReportLab
5. Font disponibili: Helvetica, Helvetica-Bold, Helvetica-Oblique, Helvetica-BoldOblique
6. Lingua: italiano sempre
7. Stile: professionale, adatto a stampa A4
8. Il codice deve essere eseguibile direttamente. Se usi funzioni, chiamale alla fine.
9. SEMPRE aggiungere: import os; os.makedirs('/tmp', exist_ok=True) dopo gli import
10. CRITICO: nelle f-string usa SOLO caratteri ASCII standard.
    VIETATO usare: bullet ● • ★ ✓ ✗ frecce → ← ↑ ↓ e qualsiasi unicode non-ASCII dentro f-string.
    USA INVECE: asterisco * trattino - maggiore > minore < e solo lettere/numeri normali.
    ESEMPIO SBAGLIATO: f"● {num_blocco} TITOLO"
    ESEMPIO GIUSTO:    f"* {num_blocco} TITOLO"
    ESEMPIO SBAGLIATO: f"→ {valore}"
    ESEMPIO GIUSTO:    f"-> {valore}"
    I caratteri speciali puoi usarli SOLO nelle stringhe normali (non f-string):
    cv.drawString(x, y, "● Titolo")  -- questo va bene
    title = f"● {num}"  -- questo causa SyntaxError, VIETATO
"""

def build_prompt(tipo_id, materia, argomento, classe, opzioni):
    note = opzioni.get("note", "")
    bes = opzioni.get("bes", False)
    dsa = opzioni.get("dsa", False)

    if tipo_id == "verifica_grammatica":
        proto = leggi_template("protocollo_grammatica.py")
        return f"""{SYSTEM_BASE}
PROTOCOLLO: {proto}
RICHIESTA: Crea Verifica di Grammatica Italiana per classe {classe}.
Argomento: {argomento}. {'DSA-friendly' if dsa else 'Standard'}
{'Note: ' + note if note else ''}
Output: /tmp/output_scheda.pdf"""

    elif tipo_id == "verifica_comprensione":
        template = leggi_template("template_comprensione.py")
        return f"""{SYSTEM_BASE}
TEMPLATE: {template}
RICHIESTA: Adatta per Verifica Comprensione Testo, classe {classe}, argomento: {argomento}
Output: /tmp/output_scheda.pdf"""

    elif tipo_id == "scheda_umanistica":
        template = leggi_template("template_umanistica.py")
        palette = {
            "storia":     "C1=(0.52,0.20,0.04) C1L=(1.00,0.92,0.82) C2=(0.80,0.62,0.04) ICON_EMOJI='🏛️' MATERIA_STR='storia'",
            "geografia":  "C1=(0.08,0.48,0.54) C1L=(0.84,0.96,0.97) C2=(0.14,0.56,0.22) ICON_EMOJI='🌍' MATERIA_STR='geografia'",
            "tecnologia": "C1=(0.20,0.20,0.20) C1L=(0.94,0.94,0.94) C2=(0.88,0.46,0.06) ICON_EMOJI='⚙️' MATERIA_STR='tecnologia'",
            "italiano":   "C1=(0.68,0.12,0.12) C1L=(1.00,0.90,0.90) C2=(0.80,0.62,0.04) ICON_EMOJI='📖' MATERIA_STR='italiano'",
            "inglese":    "C1=(0.10,0.20,0.55) C1L=(0.88,0.92,1.00) C2=(0.68,0.12,0.12) ICON_EMOJI='🇬🇧' MATERIA_STR='inglese'",
            "francese":   "C1=(0.10,0.28,0.70) C1L=(0.86,0.92,1.00) C2=(0.68,0.12,0.12) ICON_EMOJI='🇫🇷' MATERIA_STR='francese'",
        }
        pal = palette.get(materia.lower(), palette["storia"])
        return f"""{SYSTEM_BASE}
TEMPLATE: {template}
RICHIESTA: Scheda Didattica di {materia} per classe {classe}, argomento: {argomento}
Palette: {pal}
{'BES/DSA: semplifica esercizi' if bes or dsa else ''}
{'Note: ' + note if note else ''}
Output: /tmp/output_scheda.pdf"""

    elif tipo_id == "scheda_matematica":
        return f"""{SYSTEM_BASE}
RICHIESTA: Crea una Scheda di Matematica con ReportLab per classe {classe}.
Argomento: {argomento}

STRUTTURA SEMPLICE (massimo 120 righe):
- Import: from reportlab.lib.pagesizes import A4; from reportlab.pdfgen import canvas; import os
- os.makedirs('/tmp', exist_ok=True)
- W, H = A4; OUT = "/tmp/output_scheda.pdf"
- cv = canvas.Canvas(OUT, pagesize=A4)
- Intestazione semplice con titolo e box dati studente
- 3-4 esercizi su frazioni con spazio per risposta
- cv.save()

NON usare funzioni complesse. NON usare f-string con variabili nei titoli.
USA stringhe normali per i titoli: cv.drawString(x,y,"1. Titolo esercizio")
{"Note: " + note if note else ""}
Output: /tmp/output_scheda.pdf"""
    elif tipo_id == "mappa_mentale":
        template = leggi_template("template_mappa_mentale.py")
        return f"""{SYSTEM_BASE}
TEMPLATE: {template}
RICHIESTA: Mappa Mentale Buzan per classe {classe}, argomento: {argomento}
Adatta SOLO la sezione DATI DA MODIFICARE.
Output: /tmp/output_scheda.pdf"""

    elif tipo_id == "mappa_concettuale":
        template = leggi_template("template_mappa_concettuale.py")
        return f"""{SYSTEM_BASE}
TEMPLATE: {template}
RICHIESTA: Mappa Concettuale Orizzontale per classe {classe}, argomento: {argomento}
Output: /tmp/output_scheda.pdf"""

    elif tipo_id == "mappa_gerarchica":
        template = leggi_template("template_mappa_gerarchica.py")
        return f"""{SYSTEM_BASE}
TEMPLATE: {template}
RICHIESTA: Mappa Gerarchica DSA per classe {classe}, argomento: {argomento}
Output: /tmp/output_scheda.pdf"""

    else:
        materie_info = {
            "storia":    ("Storia", "9 esercizi, 100 punti, stile Loescher"),
            "geografia": ("Geografia", "9 esercizi, 100 punti, stile Loescher"),
            "scienze":   ("Scienze", "9 esercizi, stile Loescher"),
            "tecnologia":("Tecnologia", "10 esercizi, stile EDISCO"),
            "inglese":   ("Inglese", "10 esercizi, 60 punti, consegne in inglese"),
            "francese":  ("Francese", "10 esercizi, 60 punti, consegne in francese"),
            "arte":      ("Storia dell'Arte", "10 esercizi con immagini segnaposto"),
            "musica":    ("Storia della Musica", "10 esercizi, 49 punti"),
            "motoria":   ("Scienze Motorie", "10 esercizi, 50 punti"),
        }
        info = materie_info.get(materia.lower(), (materia, "9 esercizi stile Loescher"))
        return f"""{SYSTEM_BASE}
RICHIESTA: Verifica di {info[0]} per classe {classe}.
Argomento: {argomento}
Struttura: {info[1]}
Stile grafico: intestazione colorata, box dati studente, esercizi numerati,
puntini per le risposte, quadratini V/F, punteggi, totale finale.
{'BES/DSA: font grande, esercizi semplici' if bes or dsa else ''}
{'Note: ' + note if note else ''}
Output: /tmp/output_scheda.pdf"""


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return jsonify({"error": "Non autorizzato"}), 401
        return f(*args, **kwargs)
    return decorated


@app.route("/")
def index():
    if not session.get("logged_in"):
        return render_template("login.html")
    return render_template("index.html")

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if data.get("password") == PASSWORD:
        session["logged_in"] = True
        return jsonify({"success": True})
    return jsonify({"success": False})

@app.route("/logout")
def logout():
    session.clear()
    return jsonify({"success": True})

@app.route("/genera", methods=["POST"])
@login_required
def genera():
    data = request.get_json()
    tipo_id   = data.get("tipo_id", "")
    materia   = data.get("materia", "")
    argomento = data.get("argomento", "").strip()
    classe    = data.get("classe", "Prima Media")
    opzioni   = data.get("opzioni", {})

    if not argomento:
        return jsonify({"error": "Inserisci un argomento"}), 400

    prompt = build_prompt(tipo_id, materia, argomento, classe, opzioni)

    try:
        client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=8000,
            temperature=0.2
        )
        codice = response.choices[0].message.content.strip()

        # Rimuovi backtick markdown se presenti
        if "```python" in codice:
            codice = codice.split("```python")[1].split("```")[0].strip()
        elif codice.startswith("```"):
            lines = codice.split("\n")
            codice = "\n".join(lines[1:])
            if codice.strip().endswith("```"):
                codice = codice.strip()[:-3].strip()

        # Aggiungi chiamata generate() se presente ma non chiamata
        if "def generate(" in codice and "generate()" not in codice.split("def generate(")[1][-100:]:
            codice += "\n\ngenerate()"
        elif "def generate(" in codice and codice.count("generate()") == 1 and codice.endswith("generate()") == False:
            codice += "\n\ngenerate()"

        # Assicura che /tmp esista
        if "makedirs" not in codice:
            codice = codice.replace(
                "import os",
                "import os\nos.makedirs('/tmp', exist_ok=True)"
            )

        # Pulizia aggressiva: sostituisce caratteri non-ASCII in TUTTE le righe
        # non solo nelle f-string, per sicurezza
        sostituzioni = {
            '●': '*',   # ●
            '•': '-',   # •
            '→': '->',  # →
            '←': '<-',  # ←
            '↑': '^',   # ↑
            '↓': 'v',   # ↓
            '✓': 'OK',  # ✓
            '✗': 'NO',  # ✗
            '★': '*',   # ★
            '☆': '*',   # ☆
            '▶': '>',   # ▶
            '◀': '<',   # ◀
            '✔': 'OK',  # ✔
            '✘': 'NO',  # ✘
            '·': '-',   # ·
            '—': '--',  # —
            '–': '-',   # –
        }

        def pulisci_riga(line):
            # Pulisce solo le righe che contengono f-string
            if 'f"' in line or "f'" in line:
                for char, sostituto in sostituzioni.items():
                    line = line.replace(char, sostituto)
            return line

        righe_pulite = [pulisci_riga(r) for r in codice.split(chr(10))]
        codice = chr(10).join(righe_pulite)

        return jsonify({"success": True, "codice": codice})
    except Exception as e:
        return jsonify({"error": f"Errore AI: {str(e)}"}), 500


@app.route("/genera_pdf", methods=["POST"])
@login_required
def genera_pdf():
    data   = request.get_json()
    codice = data.get("codice", "")
    nome   = data.get("nome", "scheda_didattica")

    if not codice:
        return jsonify({"error": "Nessun codice"}), 400

    # Rimuovi file PDF precedente se esiste
    pdf_path = "/tmp/output_scheda.pdf"
    if os.path.exists(pdf_path):
        os.remove(pdf_path)

    try:
        result = subprocess.run(
            [sys.executable, "-c", codice],
            capture_output=True, text=True, timeout=60,
            env={**os.environ, "MPLBACKEND": "Agg"}
        )

        # Se c'è un errore mostralo preciso
        if result.returncode != 0:
            errore = result.stderr[-1200:] if result.stderr else "Errore sconosciuto"
            return jsonify({"error": f"Errore nel codice Python:\n{errore}"}), 500

        if not os.path.exists(pdf_path):
            # Mostra stdout per debug
            stdout = result.stdout[-400:] if result.stdout else ""
            return jsonify({"error": f"PDF non creato. Output: {stdout}"}), 500

        nome_file = f"{nome.replace(' ','_')}.pdf"
        return send_file(pdf_path, as_attachment=True,
                         download_name=nome_file, mimetype="application/pdf")

    except subprocess.TimeoutExpired:
        return jsonify({"error": "Timeout: il codice ha impiegato troppo tempo"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
