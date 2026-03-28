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
Crea una scheda didattica di matematica su "{argomento}" per classe {classe}.

Genera codice Python ReportLab CORTO (max 70 righe) e FUNZIONANTE.

STRUTTURA ESATTA da seguire:

import os
os.makedirs('/tmp', exist_ok=True)
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
W, H = A4
cv = canvas.Canvas("/tmp/output_scheda.pdf", pagesize=A4)
ML, MR = 28, 28

# INTESTAZIONE
cv.setFillColorRGB(0.10, 0.20, 0.55)
cv.rect(0, H-70, W, 70, fill=1, stroke=0)
cv.setFillColorRGB(1, 1, 1)
cv.setFont("Helvetica-Bold", 18)
cv.drawCentredString(W/2, H-38, "SCHEDA DI MATEMATICA")
cv.setFont("Helvetica", 11)
cv.drawCentredString(W/2, H-56, "{argomento} - Classe {classe}")
cv.setFillColorRGB(0.93, 0.93, 0.93)
cv.rect(ML, H-98, W-ML-MR, 24, fill=1, stroke=0)
cv.setFillColorRGB(0.1, 0.1, 0.1)
cv.setFont("Helvetica", 9)
cv.drawString(ML+6, H-89, "Nome: _______________  Cognome: _______________  Classe: _____  Data: ___________")

# ESERCIZI su {argomento}
# [qui generi 3 esercizi appropriati con linee punteggiate per le risposte]
# Per ogni esercizio:
# - Titolo con rettangolo colorato
# - Testo esercizio
# - Linee punteggiate per le risposte: cv.setDash([3,4]); cv.line(ML, y, W-MR, y); cv.setDash([])

# PUNTEGGIO TOTALE in fondo
cv.setFont("Helvetica-Bold", 11)
cv.drawCentredString(W/2, 40, "PUNTEGGIO TOTALE: _______ / 100")

cv.save()

REGOLE CRITICHE:
1. USA SOLO stringhe normali per tutti i testi. MAI f-string con variabili.
2. Scrivi testi HARDCODED: cv.drawString(x, y, "1.  Calcola le seguenti frazioni:")
3. NON scrivere mai: f"qualcosa {{variabile}}"
4. Il codice deve essere completo e funzionante
{"Note: " + note if note else ""}"""
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
            max_tokens=4096,
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



@app.route("/genera_pdf_matematica", methods=["POST"])
@login_required
def genera_pdf_matematica():
    """
    Genera scheda matematica in due step:
    1. DeepSeek genera SOLO i dati da sostituire (JSON piccolo)
    2. Il server applica i dati al template originale ed esegue
    """
    data = request.get_json()
    argomento = data.get("argomento", "Frazioni")
    classe = data.get("classe", "Prima Media")

    template_path = PROTO_DIR / "template_matematica.py"
    if not template_path.exists():
        return jsonify({"error": "Template matematica non trovato sul server"}), 404

    # STEP 1: chiedi a DeepSeek solo i dati da sostituire
    prompt_dati = f"""Sei un esperto di didattica della matematica per la scuola media.
Devo adattare una scheda di matematica all argomento: {argomento} per classe {classe}.

Rispondi SOLO con un oggetto JSON valido, nessun altro testo, nessun markdown.
Il JSON deve avere esattamente questa struttura:

{{
  "titolo_teoria": "Titolo del blocco teoria (es: CHE COS E UNA FRAZIONE?)",
  "testo_teoria_1": "Prima riga spiegazione teorica (max 90 caratteri)",
  "testo_teoria_2": "Seconda riga spiegazione teorica (max 110 caratteri)",
  "pizze_items": [[2,4],[1,3],[3,6],[2,8],[3,8],[1,2],[1,4],[2,5],[3,4],[1,6],[4,8],[2,3],[1,5],[3,5],[2,6],[1,8],[5,8],[3,3],[2,7],[4,6]],
  "vero_falso": [
    "Affermazione 1 vera o falsa su {argomento} (max 80 caratteri)",
    "Affermazione 2 vera o falsa su {argomento} (max 80 caratteri)",
    "Affermazione 3 vera o falsa su {argomento} (max 80 caratteri)",
    "Affermazione 4 vera o falsa su {argomento} (max 80 caratteri)"
  ],
  "problemi": [
    ["Testo problema 1 su {argomento} (max 85 caratteri)", "Suggerimento o seconda riga (max 85 caratteri)"],
    ["Testo problema 2 su {argomento} (max 85 caratteri)", "Suggerimento o seconda riga (max 85 caratteri)"]
  ]
}}

IMPORTANTE: le pizze_items restano uguali, cambiano solo teoria, vero_falso e problemi."""

    try:
        client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt_dati}],
            max_tokens=1000,
            temperature=0.3
        )
        risposta = response.choices[0].message.content.strip()

        # Pulisci eventuale markdown
        if "```json" in risposta:
            risposta = risposta.split("```json")[1].split("```")[0].strip()
        elif "```" in risposta:
            risposta = risposta.split("```")[1].split("```")[0].strip()

        dati = json.loads(risposta)

    except Exception as e:
        # Se DeepSeek fallisce, usa dati di default adattati
        dati = {
            "titolo_teoria": f"CHE COS E {argomento.upper()}?",
            "testo_teoria_1": f"Studiamo {argomento} con esempi pratici e visivi.",
            "testo_teoria_2": f"Esercita passo dopo passo con gli esercizi seguenti.",
            "pizze_items": [[2,4],[1,3],[3,6],[2,8],[3,8],[1,2],[1,4],[2,5],[3,4],[1,6],[4,8],[2,3],[1,5],[3,5],[2,6],[1,8],[5,8],[3,3],[2,7],[4,6]],
            "vero_falso": [
                f"La prima affermazione riguarda {argomento}.",
                f"La seconda affermazione riguarda {argomento}.",
                f"La terza affermazione riguarda {argomento}.",
                f"La quarta affermazione riguarda {argomento}."
            ],
            "problemi": [
                [f"Problema 1 su {argomento}.", "Risolvi e scrivi il risultato."],
                [f"Problema 2 su {argomento}.", "Risolvi e scrivi il risultato."]
            ]
        }

    # STEP 2: leggi il template e applica i dati
    codice = template_path.read_text(encoding="utf-8")

    # Cambia percorso output
    codice = codice.replace(
        'OUT  = "/mnt/user-data/outputs/scheda_matematica.pdf"',
        'OUT  = "/tmp/output_scheda.pdf"'
    )
    codice = codice.replace(
        'os.makedirs("/mnt/user-data/outputs",exist_ok=True)',
        'os.makedirs("/tmp",exist_ok=True)'
    )

    # Sostituisci titolo teoria
    titolo_old = "● 1   CHE COS'E' UNA FRAZIONE?"
    titolo_new = f"● 1   {dati.get('titolo_teoria', 'SPIEGAZIONE TEORICA')}"
    codice = codice.replace(f'"{titolo_old}"', f'"{titolo_new}"')

    # Sostituisci testo teoria
    testo1_old = "Una FRAZIONE indica quante PARTI prendo di un intero diviso in PARTI UGUALI."
    testo1_new = dati.get("testo_teoria_1", testo1_old)
    codice = codice.replace(f'"{testo1_old}"', f'"{testo1_new}"')

    testo2_old = "Il numero IN ALTO e' il NUMERATORE (parti prese), quello IN BASSO e' il DENOMINATORE (parti totali)."
    testo2_new = dati.get("testo_teoria_2", testo2_old)
    codice = codice.replace(f'"{testo2_old}"', f'"{testo2_new}"')

    # Sostituisci affermazioni Vero/Falso
    vf_dati = dati.get("vero_falso", [])
    vf_originali = [
        "2/4 e 1/2 sono frazioni equivalenti perche' 2x2 = 4x1.",
        "Con lo stesso numeratore, la frazione con denominatore maggiore e' la piu' grande.",
        "Per semplificare 6/8 si divide per 2: si ottiene 3/4.",
        "La frazione 3/7 e' maggiore di 3/9 perche' 7 e' minore di 9.",
    ]
    for i, (orig, nuovo) in enumerate(zip(vf_originali, vf_dati)):
        if nuovo:
            codice = codice.replace(f'"{orig}"', f'"{nuovo}"')

    # Sostituisci problemi
    prob_dati = dati.get("problemi", [])
    prob_originali = [
        ("Sara ha mangiato 2/8 di una torta, Luca ne ha mangiata 1/4.",
         "Chi ne ha mangiata di piu'? (Suggerimento: trova la fraz. equiv. di 1/4 con den. 8.)"),
        ("Una bottiglia e' piena per 3/4. Ne bevo 1/2.",
         "Quanta acqua rimane? (Suggerimento: trova il denominatore comune 4.)"),
    ]
    for i, (orig_pair, nuovo_pair) in enumerate(zip(prob_originali, prob_dati)):
        if nuovo_pair and len(nuovo_pair) >= 2:
            codice = codice.replace(f'"{orig_pair[0]}"', f'"{nuovo_pair[0]}"')
            codice = codice.replace(f'"{orig_pair[1]}"', f'"{nuovo_pair[1]}"')

    # Aggiungi chiamata generate()
    if 'if __name__' in codice:
        idx = codice.find('if __name__')
        codice = codice[:idx] + 'generate()' + chr(10)
    elif codice.count('generate()') < 2:
        codice += chr(10) + chr(10) + 'generate()'

    # Esegui il codice
    pdf_path = "/tmp/output_scheda.pdf"
    if os.path.exists(pdf_path):
        os.remove(pdf_path)

    try:
        result = subprocess.run(
            [sys.executable, "-c", codice],
            capture_output=True, text=True, timeout=60,
            env={**os.environ, "MPLBACKEND": "Agg"}
        )
        if result.returncode != 0:
            errore = result.stderr[-1200:]
            return jsonify({"error": f"Errore template: {errore}"}), 500
        if not os.path.exists(pdf_path):
            return jsonify({"error": "PDF non creato"}), 500
        nome_file = f"Scheda_Matematica_{argomento}.pdf".replace(" ", "_")
        return send_file(pdf_path, as_attachment=True,
                        download_name=nome_file, mimetype="application/pdf")
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Timeout generazione PDF"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
