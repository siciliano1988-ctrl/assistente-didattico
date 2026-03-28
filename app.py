from flask import Flask, render_template, request, jsonify, send_file, session
from functools import wraps
import os, json, subprocess, sys, traceback
from openai import OpenAI
from pathlib import Path

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "didattica_segreta_2024")

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
PASSWORD = os.environ.get("APP_PASSWORD", "Vanbasten")

# ── Legge i template reali dal disco ──────────────────────────────────────────
PROTO_DIR = Path(__file__).parent / "protocolli"

def leggi_template(nome_file):
    try:
        return (PROTO_DIR / nome_file).read_text(encoding="utf-8")
    except:
        return ""

# ── System prompt base ────────────────────────────────────────────────────────
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
"""

# ── Dizionario prompt per tipologia ──────────────────────────────────────────
def build_prompt(tipo_id, materia, argomento, classe, opzioni):
    note = opzioni.get("note", "")
    bes = opzioni.get("bes", False)
    dsa = opzioni.get("dsa", False)

    # ── VERIFICA GRAMMATICA ───────────────────────────────────────────────────
    if tipo_id == "verifica_grammatica":
        proto = leggi_template("protocollo_grammatica.py")
        return f"""{SYSTEM_BASE}

PROTOCOLLO DI RIFERIMENTO (seguilo fedelmente):
{proto}

RICHIESTA:
Crea una Verifica di Grammatica Italiana per classe {classe}.
Argomento grammaticale: {argomento}
{'Versione DSA-friendly' if dsa else 'Versione standard'}
{'Note aggiuntive: ' + note if note else ''}

Segui esattamente il protocollo. Output: /tmp/output_scheda.pdf"""

    # ── VERIFICA COMPRENSIONE TESTO ───────────────────────────────────────────
    elif tipo_id == "verifica_comprensione":
        template = leggi_template("template_comprensione.py")
        return f"""{SYSTEM_BASE}

TEMPLATE DI RIFERIMENTO (adatta questo codice al nuovo argomento):
{template}

RICHIESTA:
Crea una Verifica di Comprensione del Testo stile INVALSI per classe {classe}.
Argomento/tema del testo: {argomento}
{'Note aggiuntive: ' + note if note else ''}

Adatta il template al nuovo argomento mantenendo la struttura.
Output: /tmp/output_scheda.pdf"""

    # ── SCHEDA UMANISTICA ─────────────────────────────────────────────────────
    elif tipo_id == "scheda_umanistica":
        template = leggi_template("template_umanistica.py")
        palette = {
            "storia":     "C1=(0.52,0.20,0.04) C1L=(1.00,0.92,0.82) C2=(0.80,0.62,0.04) C2L=(1.00,0.97,0.80) GRAD_A=(0.42,0.14,0.02) GRAD_B=(0.82,0.44,0.10) ICON_EMOJI='🏛️'",
            "geografia":  "C1=(0.08,0.48,0.54) C1L=(0.84,0.96,0.97) C2=(0.14,0.56,0.22) C2L=(0.88,0.98,0.88) GRAD_A=(0.04,0.34,0.40) GRAD_B=(0.20,0.65,0.55) ICON_EMOJI='🌍'",
            "tecnologia": "C1=(0.20,0.20,0.20) C1L=(0.94,0.94,0.94) C2=(0.88,0.46,0.06) C2L=(1.00,0.95,0.83) GRAD_A=(0.10,0.10,0.10) GRAD_B=(0.45,0.45,0.45) ICON_EMOJI='⚙️'",
            "italiano":   "C1=(0.68,0.12,0.12) C1L=(1.00,0.90,0.90) C2=(0.80,0.62,0.04) C2L=(1.00,0.97,0.80) GRAD_A=(0.55,0.08,0.08) GRAD_B=(0.85,0.30,0.15) ICON_EMOJI='📖'",
            "inglese":    "C1=(0.10,0.20,0.55) C1L=(0.88,0.92,1.00) C2=(0.68,0.12,0.12) C2L=(1.00,0.90,0.90) GRAD_A=(0.06,0.12,0.42) GRAD_B=(0.25,0.55,0.90) ICON_EMOJI='🇬🇧'",
            "francese":   "C1=(0.10,0.28,0.70) C1L=(0.86,0.92,1.00) C2=(0.68,0.12,0.12) C2L=(1.00,0.90,0.90) GRAD_A=(0.06,0.18,0.58) GRAD_B=(0.30,0.55,0.85) ICON_EMOJI='🇫🇷'",
            "grammatica": "C1=(0.48,0.14,0.68) C1L=(0.95,0.88,1.00) C2=(0.08,0.48,0.54) C2L=(0.84,0.96,0.97) GRAD_A=(0.35,0.08,0.55) GRAD_B=(0.65,0.28,0.82) ICON_EMOJI='✏️'",
        }
        pal = palette.get(materia.lower(), palette["storia"])
        return f"""{SYSTEM_BASE}

TEMPLATE DI RIFERIMENTO (usa questo codice come base):
{template}

RICHIESTA:
Crea una Scheda Didattica di {materia} per classe {classe}.
Argomento: {argomento}
Palette colori materia: {pal}
{'Adatta per BES/DSA: font più grande, meno testo, esercizi semplificati' if bes or dsa else ''}
{'Note aggiuntive: ' + note if note else ''}

Adatta il template sostituendo SOLO i contenuti (palette, titoli, testi esercizi).
MAI modificare le funzioni di sistema. Output: /tmp/output_scheda.pdf"""

    # ── SCHEDA MATEMATICA ─────────────────────────────────────────────────────
    elif tipo_id == "scheda_matematica":
        template = leggi_template("template_matematica.py")
        return f"""{SYSTEM_BASE}

TEMPLATE DI RIFERIMENTO (usa questo codice come base):
{template}

REGOLA FONDAMENTALE: sostituire SOLO i contenuti. MAI toccare costanti/funzioni.
Layout fisso: ML=28 MR=28 BW=539.28 BPAD=10 GAP=7 TH=26 TOP=737.89

RICHIESTA:
Crea una Scheda di Matematica per classe {classe}.
Argomento: {argomento}
{'Note aggiuntive: ' + note if note else ''}

Adatta il template con nuovi numeri/esercizi sull'argomento richiesto.
Usa i blocchi disponibili: b_theory, b_pizze_scrivi, b_pizze_colora,
b_equivalenti, b_confronto_num, b_addizioni_stesso_den, b_semplifica,
b_abbinamento, b_cerchi, b_vero_falso, b_problemi.
Output: /tmp/output_scheda.pdf"""

    # ── MAPPA MENTALE (BUZAN) ─────────────────────────────────────────────────
    elif tipo_id == "mappa_mentale":
        template = leggi_template("template_mappa_mentale.py")
        return f"""{SYSTEM_BASE}

TEMPLATE MAPPA MENTALE STILE BUZAN (adatta questo codice):
{template}

RICHIESTA:
Crea una Mappa Mentale (radiale, stile Buzan) per classe {classe}.
Argomento centrale: {argomento}
{'Note aggiuntive: ' + note if note else ''}

Adatta SOLO la sezione DATI DA MODIFICARE:
- HUB_LINES: parole chiave dell'argomento centrale (max 2 righe)
- CALLOUT_TITLE e CALLOUT_TEXT: sintesi dell'argomento
- I 7 rami primari con etichette, colori e sottorami pertinenti
MAI modificare le funzioni grafiche. Output: /tmp/output_scheda.pdf"""

    # ── MAPPA CONCETTUALE ORIZZONTALE ─────────────────────────────────────────
    elif tipo_id == "mappa_concettuale":
        template = leggi_template("template_mappa_concettuale.py")
        return f"""{SYSTEM_BASE}

TEMPLATE MAPPA CONCETTUALE ORIZZONTALE (adatta questo codice):
{template}

RICHIESTA:
Crea una Mappa Concettuale Orizzontale (8 box collegati) per classe {classe}.
Argomento: {argomento}
{'Note aggiuntive: ' + note if note else ''}

La mappa ha un nodo centrale e 8 box rettangolari disposti intorno.
Ogni box ha titolo, 5 voci con descrizione.
Adatta SOLO i contenuti (titoli box, voci, testo nodo centrale).
MAI modificare le funzioni grafiche. Output: /tmp/output_scheda.pdf"""

    # ── MAPPA GERARCHICA DSA ──────────────────────────────────────────────────
    elif tipo_id == "mappa_gerarchica":
        template = leggi_template("template_mappa_gerarchica.py")
        return f"""{SYSTEM_BASE}

TEMPLATE MAPPA GERARCHICA (adatta questo codice):
{template}

RICHIESTA:
Crea una Mappa Gerarchica verticale a 4 livelli per classe {classe}.
Argomento: {argomento}
Font sans-serif ad alto contrasto, adatta per DSA.
{'Note aggiuntive: ' + note if note else ''}

Adatta SOLO i dati (DATI_ESEMPIO: titolo, rami, sotto-rami).
MAI modificare le funzioni grafiche. Output: /tmp/output_scheda.pdf"""

    # ── VERIFICA GENERICA (altre materie) ────────────────────────────────────
    else:
        materie_info = {
            "storia":    ("Storia", "9 esercizi: definizioni, V/F, completamento, abbinamento, ordine cronologico, domande aperte. Totale 100 punti."),
            "geografia": ("Geografia", "9 esercizi: concetti geografici, carte, V/F, completamento, abbinamento, domande aperte. Totale 100 punti."),
            "scienze":   ("Scienze", "9 esercizi: definizioni, immagine, domande aperte, V/F, scelta multipla, completamento, abbinamento, ordine, testo. Totale variabile."),
            "tecnologia":("Tecnologia", "10 esercizi: definizioni, immagine, domande aperte, V/F, scelta multipla, completamento, abbinamento, ordine, tabella, domanda finale."),
            "inglese":   ("Inglese", "10 esercizi: immagini-parole, completamento, coniugazione, trasformazione, sottolinea, abbinamento, immagine+domande, traduzione, T/F, componi frasi. Totale 60 punti."),
            "francese":  ("Francese", "10 esercizi stile Loescher. Totale 60 punti. Consegne in francese."),
            "arte":      ("Storia dell'Arte", "10 esercizi con immagini (segnaposto). Le immagini sono PARTE ATTIVA degli esercizi."),
            "musica":    ("Storia della Musica", "10 esercizi: V/F, definizioni, completamento, abbinamento, scelta multipla, testo, linea del tempo. Totale 49 punti."),
            "motoria":   ("Scienze Motorie", "10 esercizi con immagini. Almeno 6 esercizi con immagini segnaposto."),
        }
        info = materie_info.get(materia.lower(), (materia, "9 esercizi stile Loescher/EDISCO. Struttura professionale."))

        return f"""{SYSTEM_BASE}

RICHIESTA:
Crea una Verifica di {info[0]} per classe {classe}.
Argomento: {argomento}
Struttura: {info[1]}

STILE GRAFICO OBBLIGATORIO:
- Intestazione: box grigio scuro con titolo bianco
- Box dati studente: Nome, Cognome, Classe, Data con puntini
- Esercizi numerati con header colorato
- Puntini per le risposte (MAI linee)
- Quadratini V/F: piccoli box 12x12pt
- Punteggio per ogni esercizio, totale finale
- Font: Helvetica, dimensioni leggibili
- Stile EDISCO/Loescher professionale

{'Versione BES/DSA: font più grande, esercizi semplificati, molto spazio' if bes or dsa else ''}
{'Note aggiuntive: ' + note if note else ''}
Output: /tmp/output_scheda.pdf"""


# ── Decoratore login ──────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return jsonify({"error": "Non autorizzato"}), 401
        return f(*args, **kwargs)
    return decorated

# ── Routes ────────────────────────────────────────────────────────────────────
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
    tipo_id  = data.get("tipo_id", "")
    materia  = data.get("materia", "")
    argomento = data.get("argomento", "").strip()
    classe   = data.get("classe", "Prima Media")
    opzioni  = data.get("opzioni", {})

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
        if codice.startswith("```"):
            lines = codice.split("\n")
            codice = "\n".join(lines[1:])
            if codice.endswith("```"):
                codice = codice[:-3].strip()
        return jsonify({"success": True, "codice": codice})
    except Exception as e:
        return jsonify({"error": f"Errore AI: {str(e)}"}), 500

@app.route("/genera_pdf", methods=["POST"])
@login_required
def genera_pdf():
    data = request.get_json()
    codice = data.get("codice", "")
    nome   = data.get("nome", "scheda_didattica")
    if not codice:
        return jsonify({"error": "Nessun codice"}), 400
    try:
        result = subprocess.run(
            [sys.executable, "-c", codice],
            capture_output=True, text=True, timeout=60,
            env={**os.environ, "MPLBACKEND": "Agg"}
        )
        if result.returncode != 0:
            return jsonify({"error": f"Errore: {result.stderr[-800:]}"}), 500
        pdf_path = "/tmp/output_scheda.pdf"
        if not os.path.exists(pdf_path):
            return jsonify({"error": "PDF non generato"}), 500
        nome_file = f"{nome.replace(' ','_')}.pdf"
        return send_file(pdf_path, as_attachment=True,
                         download_name=nome_file, mimetype="application/pdf")
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Timeout: generazione troppo lenta"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
