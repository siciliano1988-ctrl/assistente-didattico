================================================================
ASSISTENTE DIDATTICO AI — Prof. A. Giuffrida
Generatore di materiali scolastici con intelligenza artificiale
================================================================

COSA FA QUESTA APP
------------------
Questa app genera verifiche, schede didattiche e mappe in PDF
usando l'intelligenza artificiale DeepSeek.

Come funziona:
1. Scegli il tipo di materiale dal menu (es. Verifica di Storia)
2. Inserisci l'argomento (es. Il Medioevo)
3. Clicchi GENERA CON AI
4. DeepSeek legge il tuo template Python reale e lo adatta
5. Il server esegue il codice con ReportLab
6. Il PDF si scarica automaticamente sul tuo dispositivo

Funziona su qualsiasi dispositivo: PC, tablet, Android, iPhone, LIM.


================================================================
PARTE 1 — CREA L'ACCOUNT GITHUB
================================================================

GitHub serve per conservare i file dell'app online.
E' gratuito e non richiede carta di credito.

PASSO 1A — Registrati su GitHub
  1. Apri il browser e vai su: https://github.com
  2. Clicca il pulsante verde "Sign up"
  3. Inserisci la tua email
  4. Scegli una password (almeno 8 caratteri)
  5. Scegli un nome utente (es. prof-giuffrida)
  6. Clicca "Continue"
  7. Risolvi il piccolo puzzle di verifica
  8. Clicca "Create account"
  9. Apri la tua email e clicca il link di conferma

PASSO 1B — Crea il repository (la cartella online)
  1. Dopo il login su GitHub, clicca il simbolo "+" in alto a destra
  2. Clicca "New repository"
  3. Nel campo "Repository name" scrivi esattamente:
         assistente-didattico
  4. Lascia tutto il resto come sta
  5. Clicca il pulsante verde "Create repository"
  6. Si apre una pagina con scritto "Quick setup"

PASSO 1C — Carica i file
  1. Nella stessa pagina, clicca il link:
         "uploading an existing file"
     (lo trovi nel testo "...or create a new file or
      upload an existing file")
  2. Estrai lo ZIP sul tuo PC (click destro > Estrai tutto)
  3. Apri la cartella estratta: "app_didattica"
  4. Seleziona TUTTI i file e cartelle dentro "app_didattica"
     (Ctrl+A per selezionare tutto)
  5. Trascinali nella pagina GitHub (nella zona tratteggiata)
  6. Aspetta che finisca il caricamento
  7. In basso clicca il pulsante verde "Commit changes"
  8. I tuoi file sono ora su GitHub!


================================================================
PARTE 2 — OTTIENI LA CHIAVE API DEEPSEEK
================================================================

DeepSeek e' l'intelligenza artificiale che genera i materiali.
I primi 5 dollari sono gratuiti (circa 8 mesi di utilizzo).

PASSO 2A — Registrati su DeepSeek Platform
  1. Vai su: https://platform.deepseek.com/sign_up
  2. Inserisci la tua email
  3. Scegli una password
  4. Conferma la tua email

PASSO 2B — Crea la chiave API
  1. Vai su: https://platform.deepseek.com/api_keys
  2. Clicca "Create new API key"
  3. Nel campo "Name" scrivi: assistente-didattico
  4. Clicca "Create"
  5. Appare una chiave del tipo: sk-xxxxxxxxxxxxxxxxxxxx

   ATTENZIONE — La chiave appare UNA SOLA VOLTA!
   Copiala subito e salvala nel Blocco Note sul tuo PC.
   Non condividerla mai con nessuno.

PASSO 2C — Verifica i crediti
  1. Vai su: https://platform.deepseek.com/usage
  2. Dovresti vedere 5 dollari di crediti gratuiti
  3. Con 200 PDF al mese consumi circa 0,60 dollari
  4. Quindi i crediti gratuiti durano circa 8 mesi


================================================================
PARTE 3 — PUBBLICA L'APP SU RENDER
================================================================

Render e' il servizio gratuito che fa girare l'app online.

PASSO 3A — Registrati su Render
  1. Vai su: https://render.com
  2. Clicca "Get Started for Free"
  3. Clicca "Sign up with GitHub"
     (questo collega Render al tuo account GitHub)
  4. Clicca "Authorize Render"
  5. Sei registrato!

PASSO 3B — Crea il servizio web
  1. Nella dashboard di Render, clicca il pulsante "New +"
  2. Clicca "Web Service"
  3. Clicca "Connect a repository"
  4. Cerca e seleziona "assistente-didattico"
     (il repository che hai creato su GitHub)
  5. Clicca "Connect"

PASSO 3C — Configura il servizio
   Compila i campi esattamente cosi':

   Name:            assistente-didattico
   Region:          Frankfurt (EU Central)
   Branch:          main
   Runtime:         Python 3
   Build Command:   pip install -r requirements.txt
   Start Command:   gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
   Plan:            Free

   Lascia tutto il resto come sta.

PASSO 3D — Inserisci le variabili d'ambiente (IMPORTANTE)
   Scorri verso il basso fino alla sezione "Environment Variables".
   Clicca "Add Environment Variable" per aggiungere ognuna:

   VARIABILE 1:
     Key:   DEEPSEEK_API_KEY
     Value: la tua chiave DeepSeek (quella che inizia con sk-)

   VARIABILE 2:
     Key:   APP_PASSWORD
     Value: Vanbasten

   VARIABILE 3:
     Key:   SECRET_KEY
     Value: assistente2024segreto

PASSO 3E — Avvia l'app
  1. Clicca il pulsante "Create Web Service"
  2. Render inizia a installare tutto (3-5 minuti)
  3. Vedi i log scorrere nella pagina
  4. Quando appare "Your service is live" l'app e' pronta!
  5. In alto vedi il link dell'app, tipo:
         https://assistente-didattico.onrender.com
  6. Copia questo link e salvalo nel Blocco Note


================================================================
PARTE 4 — USA L'APP
================================================================

COME APRIRE L'APP
  1. Apri Chrome, Safari o qualsiasi browser
  2. Scrivi il tuo indirizzo Render nella barra
     (es. https://assistente-didattico.onrender.com)
  3. La prima apertura del giorno puo' richiedere 30 secondi
     (Render "sveglia" il server gratuito)
  4. Poi funziona velocemente per tutta la giornata

COME ACCEDERE
  1. Appare la schermata di login
  2. Inserisci la password: Vanbasten
  3. Clicca "Accedi"

COME GENERARE UN MATERIALE
  1. Dal menu a sinistra scegli il tipo di materiale
     Esempi:
     - Verifiche > Storia
     - Schede Didattiche > Scheda di Matematica
     - Mappe > Mappa Mentale (stile Buzan)
  2. Leggi la descrizione che appare in giallo
  3. Scegli la materia e la classe
  4. Scrivi l'argomento (es. "Il Medioevo", "Le frazioni")
  5. Scegli eventuali opzioni (BES, DSA, bianco/nero...)
  6. Clicca il pulsante dorato "Genera con AI"
  7. Aspetta 15-30 secondi (la barra di progresso avanza)
  8. Appare il codice Python generato da DeepSeek
  9. Clicca "Scarica PDF"
 10. Il PDF si scarica sul tuo dispositivo

COSA GENERA L'AI
  L'intelligenza artificiale DeepSeek:
  - Legge il tuo template Python reale (es. TEMPLATE_SCHEDA_UMANISTICA.py)
  - Sostituisce SOLO i contenuti con il tuo argomento
  - Non tocca mai la struttura grafica
  - Il server esegue il codice con ReportLab
  - Il PDF risultante e' identico ai tuoi template originali


================================================================
PARTE 5 — COSTI
================================================================

Render.com:      GRATIS (piano Free)
DeepSeek AI:     circa 0,60 euro al mese per 200 PDF

I crediti gratuiti DeepSeek (5 dollari) durano circa 8 mesi.
Dopo: circa 7 euro all'anno totali.


================================================================
PARTE 6 — PROBLEMI FREQUENTI E SOLUZIONI
================================================================

PROBLEMA: L'app non si apre, schermo bianco
SOLUZIONE: Aspetta 30-40 secondi e ricarica la pagina.
           Il server gratuito di Render si "addormenta" dopo
           15 minuti di inattivita'. Si sveglia da solo.

PROBLEMA: "Password non corretta"
SOLUZIONE: La password e': Vanbasten (con V maiuscola)

PROBLEMA: Errore durante la generazione del PDF
SOLUZIONE 1: Controlla che la chiave DeepSeek sia valida
             su: https://platform.deepseek.com/usage
SOLUZIONE 2: Su Render, vai su Environment e verifica
             che DEEPSEEK_API_KEY sia inserita correttamente
SOLUZIONE 3: Riprova: a volte DeepSeek e' momentaneamente lento

PROBLEMA: Il PDF generato non e' corretto
SOLUZIONE: Nella finestra del codice puoi modificare
           manualmente il codice Python prima di cliccare
           "Scarica PDF". Il codice e' modificabile.

PROBLEMA: Voglio cambiare la password
SOLUZIONE: 1. Vai su Render > il tuo servizio
           2. Clicca "Environment"
           3. Modifica APP_PASSWORD con la nuova password
           4. Clicca "Save Changes"
           5. Aspetta che il servizio si riavvii (1-2 minuti)

PROBLEMA: Ho caricato nuovi template Python
SOLUZIONE: 1. Aggiorna i file su GitHub
              (carica i nuovi file nella cartella "protocolli")
           2. Su Render clicca "Manual Deploy"
           3. L'app si aggiorna automaticamente

PROBLEMA: Render dice che il piano gratuito e' scaduto
SOLUZIONE: Render ha cambiato politiche. Prova Railway.app
           che ha 5 dollari gratuiti al mese.
           Le istruzioni sono simili a quelle di Render.


================================================================
PARTE 7 — AGGIORNARE L'APP IN FUTURO
================================================================

Se vuoi aggiungere nuovi template o modificare l'app:

  1. Modifica i file sul tuo PC
  2. Vai su GitHub > il tuo repository
  3. Clicca sul file da aggiornare
  4. Clicca l'icona matita (Edit)
  5. Incolla il nuovo codice
  6. Clicca "Commit changes"
  7. Render rileva il cambiamento e aggiorna l'app da solo

In alternativa, puoi usare GitHub Desktop (programma gratuito)
per gestire i file in modo piu' comodo.


================================================================
RIEPILOGO RAPIDO — I 6 PASSI
================================================================

PASSO 1: Crea account su github.com
PASSO 2: Crea repository "assistente-didattico" e carica i file
PASSO 3: Crea chiave API su platform.deepseek.com
PASSO 4: Crea account su render.com (con GitHub)
PASSO 5: Crea Web Service su Render con le 3 variabili:
           DEEPSEEK_API_KEY = la tua chiave
           APP_PASSWORD = Vanbasten
           SECRET_KEY = assistente2024segreto
PASSO 6: Apri il link Render e usa l'app!

================================================================
Prof. A. Giuffrida — Assistente Didattico AI
================================================================
