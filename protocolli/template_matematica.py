"""
TEMPLATE_SCHEDA_BES.py — versione 2.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REGOLA FONDAMENTALE: sostituire SOLO i contenuti. MAI toccare costanti/funzioni.

LAYOUT FISSO (non modificare):
  ML=28  MR=28  BW=539.28  BPAD=10  GAP=7  TH=26
  X0=38  X1=557.28  CW=519.28  TOP=737.89

SPAZIO DISPONIBILE PER PAGINA:
  PAG1 (no footer): 737.89 pt
  PAG2+ (footer):   717.89 pt

FORMULA SPAZIO INTERNO BLOCCO:
  spazio = h - TH - 9 - 8 = h - 43
  ogni elemento deve avere offset ≤ spazio da yc

INTESTAZIONE STUDENTE (definitiva):
  "Nome: _________________   Cognome: _________________   Classe: ______   Data: __________"

BLOCCHI DISPONIBILI (vedere commenti su ogni funzione):
  b_theory               h=208  Teoria 2 col: box SX + schema DX + mini-box
  b_pizze_scrivi         h=479  4col*5righe, pizza -> write_lines (20 item)
  b_pizze_colora         h=293  6col*3righe, pizza vuota + frac sotto
  b_rettangoli_scrivi    h=479  4col*5righe, celle colorate -> write_lines (20 item)
  b_equivalenti          h=175  5 righe frecce+box, y_ctr=yc-20-ri*24
  b_confronto_num        h=96   6 coppie, box SQ=20 a yc-47
  b_barre_confronto      h=166  3 coppie barre + box [>][<][=]
  b_addizioni_stesso_den h=118  3col*2righe, espressione+linea puntinata
  b_addizioni_riga_frac  h=123  3col*2righe, frac()+op+frac()+=+box
  b_semplifica           h=133  2col*4righe, fraz->÷N->box con barra
  b_abbinamento          h=131  2 colonne senza tabella ne linee
  b_cerchi               h=155  4col*2righe, R=13, CY_ROW=[24,78]
  b_vero_falso           h=var  N*21+TH+27  (3->116, 4->137, 5->158, 6->179)
  b_problemi             h=133  2 problemi, step 13+12+16
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import math, os

W, H = A4
OUT  = "/mnt/user-data/outputs/scheda_matematica.pdf"  # <- cambia per ogni scheda

# ── LAYOUT COSTANTI ───────────────────────────────────────────────────────────
ML=28; MR=28; BW=W-ML-MR; BPAD=10; GAP=7; TH=26
X0=ML+BPAD; X1=ML+BW-BPAD; CW=X1-X0

# ── PALETTE ───────────────────────────────────────────────────────────────────
NAVY=(0.10,0.20,0.55);  NAVYL=(0.88,0.92,1.00)
SKY=(0.25,0.55,0.90)
ORANGE=(0.88,0.46,0.06);ORANGEL=(1.00,0.95,0.83)
GREEN=(0.14,0.56,0.22); GREENL=(0.88,0.98,0.88)
PURPLE=(0.48,0.14,0.68);PURPLEL=(0.95,0.88,1.00)
RED=(0.68,0.12,0.12);   REDL=(1.00,0.90,0.90)
TEAL=(0.08,0.48,0.54);  TEALL=(0.84,0.96,0.97)
BROWN=(0.52,0.28,0.05); BROWNL=(1.00,0.94,0.82)
GRAY=(0.48,0.48,0.48);  GRAYL=(0.95,0.95,0.95)
GOLD=(0.80,0.62,0.04)
WHITE=(1.00,1.00,1.00); BLACK=(0.05,0.05,0.05)
GRID_C=(0.80,0.87,0.95);GRID_S=14

def sf(cv,c): cv.setFillColorRGB(*c)
def ss(cv,c): cv.setStrokeColorRGB(*c)


# ── FUNZIONI DI SISTEMA -- NON MODIFICARE ────────────────────────────────────

def clip_box(cv,bx,by,bw,bh):
    p=cv.beginPath(); p.rect(bx,by,bw,bh)
    cv.clipPath(p,stroke=0,fill=0)

def draw_grid(cv,bx,by,bw,bh):
    cv.saveState(); clip_box(cv,bx,by,bw,bh)
    ss(cv,GRID_C); cv.setLineWidth(0.35)
    x=bx
    while x<=bx+bw+1: cv.line(x,by,x,by+bh); x+=GRID_S
    y=by
    while y<=by+bh+1: cv.line(bx,y,bx+bw,y); y+=GRID_S
    cv.restoreState()

def block_open(cv,y_top,h,title,cb,cl):
    """Disegna box+griglia+banda titolo. Ritorna yc = y_top-TH-9."""
    bx=ML; by=y_top-h
    sf(cv,cl); cv.roundRect(bx,by,BW,h,7,fill=1,stroke=0)
    draw_grid(cv,bx,by,BW,h)
    ss(cv,cb); cv.setLineWidth(1.5)
    cv.roundRect(bx,by,BW,h,7,fill=0,stroke=1)
    cv.saveState(); clip_box(cv,bx,y_top-TH,BW,TH)
    sf(cv,cb); cv.roundRect(bx,y_top-TH,BW,TH,7,fill=1,stroke=0)
    cv.restoreState()
    import re as _re
    _m=_re.match(r'\u25cf\s*(\d+)\s+(.*)',title)
    if _m:
        _num,_txt=_m.group(1),_m.group(2)
        _cy=y_top-TH/2; _cx=ML+14
        sf(cv,WHITE); cv.circle(_cx,_cy,9,fill=1,stroke=0)
        sf(cv,cb); cv.setFont('Helvetica-Bold',9)
        cv.drawCentredString(_cx,_cy-3.5,_num)
        sf(cv,WHITE); cv.setFont('Helvetica-Bold',9.5)
        cv.drawString(ML+30,y_top-TH+8,_txt)
    else:
        sf(cv,WHITE); cv.setFont('Helvetica-Bold',9.5)
        cv.drawString(X0,y_top-TH+8,title)
    return y_top-TH-9

def frac(cv,cx,cy,num,den,fsz=12,col=BLACK):
    """Frazione num/den centrata in (cx, cy=posizione barra).
    Usare SEMPRE per disegnare frazioni. MAI usare stringhe "n/d"."""
    sf(cv,col); cv.setFont("Helvetica-Bold",fsz)
    lw=fsz*0.9; ss(cv,col); cv.setLineWidth(1.1)
    cv.line(cx-lw/2,cy,cx+lw/2,cy)
    cv.drawCentredString(cx,cy+fsz*0.28,str(num))
    cv.drawCentredString(cx,cy-fsz*0.80,str(den))

def pizza(cv,cx,cy,r,num,den,fc=ORANGE):
    """Pizza a spicchi. num=0 = pizza vuota da colorare."""
    cv.saveState(); clip_box(cv,cx-r-1,cy-r-1,2*r+2,2*r+2)
    aper=360.0/max(den,1)
    for i in range(den):
        sa=90+i*aper
        sf(cv,fc if i<num else WHITE)
        p=cv.beginPath(); p.moveTo(cx,cy)
        steps=max(8,int(aper/3))
        for s in range(steps+1):
            a=math.radians(sa+s*aper/steps)
            p.lineTo(cx+r*math.cos(a),cy+r*math.sin(a))
        p.close(); cv.drawPath(p,fill=1,stroke=0)
    ss(cv,(0.30,0.14,0.00)); cv.setLineWidth(0.6)
    for i in range(den):
        a=math.radians(90+i*aper)
        cv.line(cx,cy,cx+r*math.cos(a),cy+r*math.sin(a))
    cv.setLineWidth(1.2); cv.circle(cx,cy,r,fill=0,stroke=1)
    cv.restoreState()

def write_lines(cv,cx,cy,col=ORANGE):
    """3 linee puntinate per scrivere una frazione sotto un grafico."""
    cv.saveState(); clip_box(cv,cx-18,cy-16,36,32)
    ss(cv,(0.55,0.55,0.55)); cv.setLineWidth(0.6); cv.setDash([2,3])
    cv.line(cx-14,cy+12,cx+14,cy+12)
    cv.setDash([]); ss(cv,col); cv.setLineWidth(1.3)
    cv.line(cx-16,cy+1,cx+16,cy+1)
    ss(cv,(0.55,0.55,0.55)); cv.setLineWidth(0.6); cv.setDash([2,3])
    cv.line(cx-14,cy-11,cx+14,cy-11)
    cv.setDash([]); cv.restoreState()


# ── HEADER / FOOTER ──────────────────────────────────────────────────────────

def draw_header(cv):
    steps=30
    for i in range(steps):
        t=i/steps
        r=NAVY[0]+(SKY[0]-NAVY[0])*t
        g=NAVY[1]+(SKY[1]-NAVY[1])*t
        b=NAVY[2]+(SKY[2]-NAVY[2])*t
        sf(cv,(r,g,b))
        y_s=H-78+i*(78/steps)
        cv.rect(0,y_s,W,78/steps+0.5,fill=1,stroke=0)
    cv.saveState(); clip_box(cv,0,H-78,W,78)
    sf(cv,(1,1,1)); cv.setFillAlpha(0.06)
    for cx,cy,cr in [(60,H-20,55),(W-50,H-55,40),(W/2+100,H-10,30),(150,H-68,25)]:
        cv.circle(cx,cy,cr,fill=1,stroke=0)
    cv.setFillAlpha(1.0); cv.restoreState()
    ico_x,ico_y=52,H-39
    sf(cv,ORANGE); cv.circle(ico_x,ico_y,24,fill=1,stroke=0)
    sf(cv,WHITE); cv.setFont("Helvetica-Bold",20)
    cv.drawCentredString(ico_x,ico_y-7,"🔢")          # <- cambia emoji
    sf(cv,WHITE); cv.setFont("Helvetica-Bold",26)
    cv.drawString(86,H-32,"LE FRAZIONI")               # <- cambia titolo
    sf(cv,(0.85,0.92,1.00)); cv.setFont("Helvetica",11)
    cv.drawString(88,H-50,"Scheda di matematica  ·  esercita passo dopo passo")
    badges=[("NUMERATORE",GOLD),("DENOMINATORE",ORANGE),("EQUIVALENTI",TEAL)]  # <- cambia
    bx=88
    for txt,col in badges:
        sf(cv,col); tw=len(txt)*5.6+14
        cv.roundRect(bx,H-72,tw,14,4,fill=1,stroke=0)
        sf(cv,WHITE); cv.setFont("Helvetica-Bold",7)
        cv.drawString(bx+7,H-65,txt); bx+=tw+6
    sf(cv,NAVYL); cv.roundRect(ML,H-100,BW,22,5,fill=1,stroke=0)
    sf(cv,(0.20,0.20,0.20)); cv.setFont("Helvetica",9)
    cv.drawString(X0,H-100+8,
        "Nome: _________________   Cognome: _________________   Classe: ______   Data: __________")

def draw_footer(cv):
    sf(cv,GRAYL); cv.rect(0,0,W,20,fill=1,stroke=0)
    sf(cv,GRAY); cv.setFont("Helvetica-Oblique",7.5)
    cv.drawCentredString(W/2,6,"Prof. A. Giuffrida  ·  Matematica per tutti")

TOP=H-104


# =============================================================================
# BLOCCHI
# =============================================================================

# -----------------------------------------------------------------------------
# TIPO A -- TEORIA a due colonne  h=208  spazio=165  margine=+21pt
# REGOLA: nulla nella fascia yc-2..yc-32 tranne il testo. Schema parte da yc-34.
# -----------------------------------------------------------------------------
def b_theory(cv,y_top):
    h=208
    yc=block_open(cv,y_top,h,"● 1   CHE COS'E' UNA FRAZIONE?",NAVY,NAVYL)

    # Testo: yc-2..yc-26
    sf(cv,BLACK); cv.setFont("Helvetica-Bold",10.5)
    cv.drawString(X0,yc-2,"Una FRAZIONE indica quante PARTI prendo di un intero diviso in PARTI UGUALI.")
    cv.setFont("Helvetica",9.5)
    cv.drawString(X0,yc-16,"Il numero IN ALTO e' il NUMERATORE (parti prese), quello IN BASSO e' il DENOMINATORE (parti totali).")

    # Schema SX: box anatomia  top=yc-34  bottom=yc-86
    sx=X0+10; sh=52; sw=100; sy=yc-34
    sf(cv,(0.96,0.97,1.00)); ss(cv,NAVY); cv.setLineWidth(0.8)
    cv.roundRect(sx,sy-sh,sw,sh,5,fill=1,stroke=1)
    sf(cv,NAVY); cv.setFont("Helvetica-Bold",22)
    cv.drawCentredString(sx+sw/2,sy-18,"3")
    ss(cv,NAVY); cv.setLineWidth(2.0)
    cv.line(sx+16,sy-26,sx+sw-16,sy-26)
    cv.drawCentredString(sx+sw/2,sy-sh+8,"5")
    arr_x=sx+sw+8
    # Freccia NUMERATORE
    sf(cv,NAVY); cv.setFont("Helvetica-Bold",8.5)
    cv.drawString(arr_x+12,sy-14,"NUMERATORE")
    cv.setFont("Helvetica",8)
    cv.drawString(arr_x+12,sy-24,"quante parti PRENDO")
    ss(cv,NAVY); cv.setLineWidth(1.0)
    cv.line(arr_x,sy-18,arr_x+10,sy-18)
    cv.circle(arr_x,sy-18,2,fill=1,stroke=0)
    # Freccia DENOMINATORE (gap 30pt dalla freccia NUM)
    sf(cv,RED); cv.setFont("Helvetica-Bold",8.5)
    cv.drawString(arr_x+12,sy-sh+16,"DENOMINATORE")
    cv.setFont("Helvetica",8)
    cv.drawString(arr_x+12,sy-sh+5,"in quante parti e' DIVISO")
    ss(cv,RED); cv.setLineWidth(1.0)
    cv.line(arr_x,sy-sh+12,arr_x+10,sy-sh+12)
    cv.circle(arr_x,sy-sh+12,2,fill=1,stroke=0)

    # Schema DX: barra frazionata  top=yc-40  bottom=yc-72
    bar_x=X0+280; bar_w=130; bar_h=16; bar_y=yc-40
    sf(cv,NAVY); cv.setFont("Helvetica-Bold",8)
    cv.drawString(bar_x,bar_y+8,"Esempio:  3/5 della barra")
    cw_b=bar_w/5
    for i in range(5):
        sf(cv,NAVY if i<3 else NAVYL)
        ss(cv,NAVY); cv.setLineWidth(0.8)
        cv.rect(bar_x+i*cw_b,bar_y-bar_h,cw_b,bar_h,fill=1,stroke=1)
    sf(cv,NAVY); cv.setFont("Helvetica-Bold",8)
    cv.drawString(bar_x,bar_y-bar_h-10,"<- 3 colorate")
    cv.drawString(bar_x+bar_w*0.55,bar_y-bar_h-10,"2 non col. ->")

    # Mini-box 3 tipi  top=yc-100  bottom=yc-144
    ry=yc-100
    tipi=[(NAVY,NAVYL,"PROPRIA","num < den","es: 2/5"),
          (GREEN,GREENL,"APPARENTE","num = den","es: 4/4"),
          (RED,REDL,"IMPROPRIA","num > den","es: 7/4")]
    tw=(CW-8)/3
    for ri,(cb,cl,nome,regola,es) in enumerate(tipi):
        rx=X0+ri*(tw+4); rw=min(tw,X1-rx)
        sf(cv,cl); ss(cv,cb); cv.setLineWidth(1.1)
        cv.roundRect(rx,ry-44,rw,44,5,fill=1,stroke=1)
        cv.saveState(); clip_box(cv,rx,ry-13,rw,13)
        sf(cv,cb); cv.roundRect(rx,ry-13,rw,13,5,fill=1,stroke=0)
        cv.restoreState()
        sf(cv,WHITE); cv.setFont("Helvetica-Bold",7.5)
        cv.drawCentredString(rx+rw/2,ry-10,nome)
        sf(cv,BLACK); cv.setFont("Helvetica",7.5)
        cv.drawCentredString(rx+rw/2,ry-23,regola)
        sf(cv,cb); cv.setFont("Helvetica-Bold",8)
        cv.drawCentredString(rx+rw/2,ry-37,es)
    return y_top-h-GAP


# -----------------------------------------------------------------------------
# TIPO B -- PIZZE SCRIVI  h=479  (4col * 5righe = 20 item ESATTI)
# -----------------------------------------------------------------------------
def b_pizze_scrivi(cv,y_top,num_blocco=2):
    items=[(2,4),(1,3),(3,6),(2,8),(3,8),(1,2),
           (1,4),(2,5),(3,4),(1,6),(4,8),(2,3),
           (1,5),(3,5),(2,6),(1,8),(5,8),(3,3),
           (2,7),(4,6)]
    assert len(items)==20, "len(items) DEVE essere esattamente 20!"
    R=19; COLS=4; ROWS=5; cell_w=BW/COLS; cell_h=84
    h=TH+9+16+ROWS*cell_h+8
    yc=block_open(cv,y_top,h,
        f"● {num_blocco}   OSSERVA LA PIZZA -> SCRIVI la frazione colorata",
        ORANGE,ORANGEL)
    sf(cv,(0.18,0.18,0.18)); cv.setFont("Helvetica",9)
    cv.drawString(X0,yc-2,
        "Conta gli spicchi colorati (numeratore) e quelli totali (denominatore). Scrivi la frazione.")
    for idx,(num,den) in enumerate(items):
        col_i=idx%COLS; row_i=idx//COLS
        cx=ML+cell_w*col_i+cell_w/2
        cy=yc-18-row_i*cell_h-R-8
        cx=max(ML+R+4,min(cx,ML+BW-R-4))
        pizza(cv,cx,cy,R,num,den,fc=ORANGE)
        write_lines(cv,cx,cy-R-22,col=ORANGE)
    return y_top-h-GAP


# -----------------------------------------------------------------------------
# TIPO C -- PIZZE COLORA  h=293  (6col * 3righe = 18 item)
# -----------------------------------------------------------------------------
def b_pizze_colora(cv,y_top,num_blocco=3):
    sets=[[(1,2),(2,3),(3,8),(1,6),(5,8),(2,4)],
          [(1,4),(3,6),(2,5),(1,3),(4,8),(3,4)],
          [(2,6),(1,5),(3,3),(2,8),(1,8),(4,6)]]
    R=20; COLS=6; ROWS=3; cell_w=BW/COLS; cell_h=78
    h=TH+9+16+ROWS*cell_h+8
    yc=block_open(cv,y_top,h,
        f"● {num_blocco}   LEGGI la frazione -> COLORA le parti giuste",
        GREEN,GREENL)
    sf(cv,(0.18,0.18,0.18)); cv.setFont("Helvetica",9)
    cv.drawString(X0,yc-2,"Colora il numero giusto di spicchi indicato dalla frazione.")
    for row_i,frazioni in enumerate(sets):
        for col_i,(num,den) in enumerate(frazioni):
            cx=ML+cell_w*col_i+cell_w/2
            cy=yc-18-row_i*cell_h-R-6
            cx=max(ML+R+3,min(cx,ML+BW-R-3))
            pizza(cv,cx,cy,R,0,den)
            frac(cv,cx,cy-R-22,num,den,fsz=11,col=GREEN)
    return y_top-h-GAP


# -----------------------------------------------------------------------------
# TIPO D -- RETTANGOLI SCRIVI  h=479  (4col * 5righe = 20 item ESATTI)
# -----------------------------------------------------------------------------
def b_rettangoli_scrivi(cv,y_top,num_blocco=2):
    items=[(2,5),(1,4),(3,6),(2,7),(3,8),(1,3),
           (1,5),(3,4),(2,6),(1,7),(4,8),(2,3),
           (1,6),(3,5),(2,8),(1,4),(5,7),(3,3),
           (2,9),(4,6)]
    assert len(items)==20
    COLS=4; ROWS=5; cell_w=BW/COLS; cell_h=84
    h=TH+9+16+ROWS*cell_h+8
    yc=block_open(cv,y_top,h,
        f"● {num_blocco}   OSSERVA il rettangolo -> SCRIVI la frazione colorata",
        ORANGE,ORANGEL)
    sf(cv,(0.18,0.18,0.18)); cv.setFont("Helvetica",9)
    cv.drawString(X0,yc-2,
        "Conta le celle colorate (numeratore) e le celle totali (denominatore). Scrivi la frazione.")
    RECT_W=cell_w-22; RECT_H=26
    for idx,(num,den) in enumerate(items):
        col_i=idx%COLS; row_i=idx//COLS
        cx=ML+cell_w*col_i+cell_w/2
        cy=yc-18-row_i*cell_h-RECT_H/2-8
        cx=max(ML+RECT_W/2+4,min(cx,ML+BW-RECT_W/2-4))
        cw_s=RECT_W/den
        for i in range(den):
            cc=cx-RECT_W/2+i*cw_s
            sf(cv,ORANGE if i<num else (1.0,0.97,0.90))
            ss(cv,ORANGE); cv.setLineWidth(0.8)
            cv.rect(cc,cy-RECT_H/2,cw_s,RECT_H,fill=1,stroke=1)
        lx=cx; ly=cy-RECT_H/2-10
        ss(cv,(0.60,0.60,0.60)); cv.setLineWidth(0.6); cv.setDash([2,3])
        cv.line(lx-13,ly,lx+13,ly)
        cv.setDash([]); ss(cv,ORANGE); cv.setLineWidth(1.2)
        cv.line(lx-13,ly-10,lx+13,ly-10)
        ss(cv,(0.60,0.60,0.60)); cv.setLineWidth(0.6); cv.setDash([2,3])
        cv.line(lx-13,ly-20,lx+13,ly-20)
        cv.setDash([])
    return y_top-h-GAP


# -----------------------------------------------------------------------------
# TIPO E -- CATENA EQUIVALENTI  h=175  spazio=132  margine=+7pt
# y_ctr INIZIA a yc-20 (NON yc-12!), ROW_H=24
# -----------------------------------------------------------------------------
def b_equivalenti(cv,y_top,num_blocco=4):
    h=175
    yc=block_open(cv,y_top,h,
        f"● {num_blocco}   COMPLETA la catena di frazioni EQUIVALENTI",
        PURPLE,PURPLEL)
    sf(cv,BLACK); cv.setFont("Helvetica",9)
    cv.drawString(X0,yc-2,"Moltiplica o dividi numeratore e denominatore per lo stesso numero.")
    serie=[("1/4","x2","___/8","x2","4/16"),
           ("2/3","x3","6/9","x2","___/18"),
           ("3/5","x2","___/10","x3","9/15"),
           ("12/16","÷4","3/4","x5","___/20"),
           ("1/2","x3","___/6","x2","6/12")]
    FRAC_W=44; ARR_W=68; BOX_W=46; BOX_H=18; ROW_H=24
    chain_w=FRAC_W+ARR_W+FRAC_W+ARR_W+FRAC_W
    x_start=X0+(CW-chain_w)/2
    for ri,(a,op1,b,op2,c) in enumerate(serie):
        y_ctr=yc-20-ri*ROW_H   # inizia a yc-20, non yc-12!
        seq=[(a,x_start,False),(op1,x_start+FRAC_W,True),
             (b,x_start+FRAC_W+ARR_W,False),
             (op2,x_start+FRAC_W+ARR_W+FRAC_W,True),
             (c,x_start+2*FRAC_W+2*ARR_W,False)]
        for lbl,lx,is_op in seq:
            if is_op:
                ax1=lx+4; ax2=lx+ARR_W-4
                ss(cv,PURPLE); cv.setLineWidth(1.0)
                cv.line(ax1,y_ctr,ax2,y_ctr)
                cv.line(ax2,y_ctr,ax2-5,y_ctr+4)
                cv.line(ax2,y_ctr,ax2-5,y_ctr-4)
                sf(cv,PURPLE); cv.setFont("Helvetica-Bold",8)
                cv.drawCentredString(lx+ARR_W/2,y_ctr+8,lbl)
            elif "___" in lbl:
                by=y_ctr-BOX_H/2
                sf(cv,WHITE); ss(cv,(0.40,0.40,0.40)); cv.setLineWidth(0.9)
                cv.setDash([3,3])
                cv.roundRect(lx,by,BOX_W,BOX_H,3,fill=1,stroke=1)
                cv.setDash([])
                parte=lbl.replace("___","")
                sf(cv,(0.60,0.60,0.60)); cv.setFont("Helvetica",8)
                cv.drawCentredString(lx+BOX_W/2,y_ctr-4,parte)
            else:
                sf(cv,BLACK); cv.setFont("Helvetica-Bold",11)
                cv.drawCentredString(lx+FRAC_W/2,y_ctr-4,lbl)
    return y_top-h-GAP


# -----------------------------------------------------------------------------
# TIPO F -- CONFRONTO STESSO NUMERATORE  h=96  spazio=53  margine=+6pt
# -----------------------------------------------------------------------------
def b_confronto_num(cv,y_top,num_blocco=5):
    h=96
    yc=block_open(cv,y_top,h,
        f"● {num_blocco}   CONFRONTO stesso NUMERATORE -- scrivi  >  <  =",
        TEAL,TEALL)
    sf(cv,BLACK); cv.setFont("Helvetica",9)
    cv.drawString(X0,yc-2,"Con lo stesso numeratore: denominatore minore = frazione piu' grande.")
    coppie=[("2/5","2/7"),("3/4","3/8"),("1/3","1/6"),
            ("4/5","4/9"),("5/8","5/12"),("3/7","3/7")]
    N=len(coppie); sp_c=CW/N; SQ=20
    for idx,(a,b) in enumerate(coppie):
        cx=X0+sp_c*idx+sp_c/2
        sf(cv,TEAL); cv.setFont("Helvetica-Bold",10)
        tx_a=max(X0,cx-SQ/2-26); tx_b=min(X1-26,cx+SQ/2+6)
        cv.drawCentredString(tx_a+13,yc-36,a)
        sq_x=max(X0,min(cx-SQ/2,X1-SQ))
        sf(cv,WHITE); ss(cv,(0.3,0.3,0.3)); cv.setLineWidth(0.9)
        cv.rect(sq_x,yc-47,SQ,SQ,fill=1,stroke=1)
        sf(cv,TEAL); cv.setFont("Helvetica-Bold",10)
        cv.drawCentredString(tx_b+13,yc-36,b)
    return y_top-h-GAP


# -----------------------------------------------------------------------------
# TIPO G -- BARRE CONFRONTO  h=166  spazio=123  margine=0pt (esatto)
# 3 coppie di barre affiancate + box [>][<][=] a destra
# BAR_MAX=200, BAR_H=12, ROW_H=37, PAD_TOP=12
# -----------------------------------------------------------------------------
def b_barre_confronto(cv,y_top,num_blocco=5):
    h=166
    yc=block_open(cv,y_top,h,
        f"● {num_blocco}   CONFRONTA le frazioni -- cerchia il simbolo giusto",
        ORANGE,ORANGEL)
    sf(cv,BLACK); cv.setFont("Helvetica",9)
    cv.drawString(X0,yc-2,
        "Osserva le barre colorate e cerchia  >  <  oppure  =  tra le due frazioni.")
    coppie=[((3,8),(5,8)),((2,5),(3,5)),((1,4),(1,3))]
    BAR_MAX=200; BAR_H=12; ROW_H=37; PAD_TOP=12
    FRAC_W=36; SYM_W=26; SYM_GAP=4
    for ri,(fA,fB) in enumerate(coppie):
        nA,dA=fA; nB,dB=fB
        y_top_row=yc-PAD_TOP-ri*ROW_H
        lenA=int(BAR_MAX*nA/dA); lenB=int(BAR_MAX*nB/dB)
        bar_x=X0+FRAC_W+8
        y_A=y_top_row-4
        sf(cv,ORANGE); cv.setFont("Helvetica-Bold",9)
        cv.drawRightString(bar_x-4,y_A-BAR_H/2-2,f"{nA}/{dA}")
        sf(cv,ORANGE)
        cv.roundRect(bar_x,y_A-BAR_H,lenA,BAR_H,2,fill=1,stroke=0)
        ss(cv,(0.70,0.35,0.02)); cv.setLineWidth(0.6)
        cv.roundRect(bar_x,y_A-BAR_H,BAR_MAX,BAR_H,2,fill=0,stroke=1)
        y_B=y_A-BAR_H-5
        sf(cv,NAVY); cv.setFont("Helvetica-Bold",9)
        cv.drawRightString(bar_x-4,y_B-BAR_H/2-2,f"{nB}/{dB}")
        sf(cv,NAVY)
        cv.roundRect(bar_x,y_B-BAR_H,lenB,BAR_H,2,fill=1,stroke=0)
        ss(cv,(0.10,0.18,0.50)); cv.setLineWidth(0.6)
        cv.roundRect(bar_x,y_B-BAR_H,BAR_MAX,BAR_H,2,fill=0,stroke=1)
        sym_x=bar_x+BAR_MAX+12
        sym_y=(y_A+y_B)/2-BAR_H
        for si,sym in enumerate([">","<","="]):
            bsx=sym_x+si*(SYM_W+SYM_GAP)
            sf(cv,WHITE); ss(cv,(0.40,0.40,0.40)); cv.setLineWidth(0.9)
            cv.roundRect(bsx,sym_y,SYM_W,SYM_W,4,fill=1,stroke=1)
            sf(cv,(0.25,0.25,0.25)); cv.setFont("Helvetica-Bold",11)
            cv.drawCentredString(bsx+SYM_W/2,sym_y+SYM_W*0.25,sym)
    return y_top-h-GAP


# -----------------------------------------------------------------------------
# TIPO H -- ADDIZIONI STESSO DEN  h=118  spazio=75  margine=+9pt
# 6 op in 3col*2righe. y0=yc-20-row_i*32. Risposta: linea puntinata.
# -----------------------------------------------------------------------------
def b_addizioni_stesso_den(cv,y_top,num_blocco=6):
    h=118
    yc=block_open(cv,y_top,h,
        f"● {num_blocco}   ADDIZIONI e SOTTRAZIONI stesso DENOMINATORE",
        NAVY,NAVYL)
    sf(cv,BLACK); cv.setFont("Helvetica",9)
    cv.drawString(X0,yc-2,"Regola: tieni il denominatore uguale e opera solo sui numeratori.")
    ops=[("1/5 + 2/5 =",None),("3/8 + 2/8 =",None),("2/6 + 3/6 =",None),
         ("5/7 - 2/7 =",None),("7/9 - 4/9 =",None),("4/5 - 1/5 =",None)]
    COLS=3; col_w=CW/COLS
    for idx,(expr,_) in enumerate(ops):
        col_i=idx%COLS; row_i=idx//COLS
        x0c=X0+col_w*col_i; y0=yc-20-row_i*32
        bx=x0c; bw=col_w-4
        sf(cv,WHITE); ss(cv,NAVY); cv.setLineWidth(0.8)
        cv.roundRect(bx,y0-14,bw,28,4,fill=1,stroke=1)
        cv.saveState(); clip_box(cv,bx+2,y0-14,bw-4,28)
        sf(cv,NAVY); cv.setFont("Helvetica-Bold",10)
        cv.drawString(bx+5,y0,expr)
        ss(cv,(0.55,0.55,0.55)); cv.setLineWidth(0.7); cv.setDash([2,3])
        cv.line(bx+100,y0-3,bx+bw-8,y0-3)
        cv.setDash([])
        cv.restoreState()
    return y_top-h-GAP


# -----------------------------------------------------------------------------
# TIPO I -- ADDIZIONI IN RIGA CON FRAC()  h=123  spazio=80  margine=0pt (esatto)
# 6 op in 3col*2righe. USA SEMPRE frac() per le frazioni, MAI stringhe "n/d"!
# ROW_H=34, PAD=12
# -----------------------------------------------------------------------------
def b_addizioni_riga_frac(cv,y_top,num_blocco=6):
    h=123
    yc=block_open(cv,y_top,h,
        f"● {num_blocco}   CALCOLA -- scrivi il risultato nella casella",
        NAVY,NAVYL)
    sf(cv,BLACK); cv.setFont("Helvetica",9)
    cv.drawString(X0,yc-2,"Somma o sottrai i numeratori. Il denominatore rimane uguale.")
    ops=[(3,"+",2,7),(4,"+",3,9),(5,"+",2,8),
         (6,"-",2,7),(7,"-",3,9),(8,"-",3,8)]
    COLS=3; col_w=CW/COLS
    FSZ=11; BOX_W=36; BOX_H=20; ROW_H=34; PAD=12
    for idx,(n1,op,n2,den) in enumerate(ops):
        col_i=idx%COLS; row_i=idx//COLS
        x0_col=X0+col_i*col_w
        yc_row=yc-PAD-row_i*ROW_H-ROW_H//4
        item_w=20+6+10+6+20+6+10+6+BOX_W   # 114pt < col_w=173pt OK
        x=x0_col+(col_w-item_w)/2
        frac(cv,x+10,yc_row,n1,den,fsz=FSZ,col=NAVY); x+=26
        sf(cv,ORANGE); cv.setFont("Helvetica-Bold",12)
        cv.drawCentredString(x+5,yc_row-4,op); x+=16
        frac(cv,x+10,yc_row,n2,den,fsz=FSZ,col=NAVY); x+=26
        sf(cv,BLACK); cv.setFont("Helvetica-Bold",12)
        cv.drawCentredString(x+5,yc_row-4,"="); x+=16
        by=yc_row-BOX_H/2
        sf(cv,WHITE); ss(cv,(0.35,0.35,0.35)); cv.setLineWidth(0.9)
        cv.roundRect(x,by,BOX_W,BOX_H,3,fill=1,stroke=1)
        ss(cv,NAVY); cv.setLineWidth(0.7)
        cv.line(x+4,by+BOX_H/2,x+BOX_W-4,by+BOX_H/2)
    return y_top-h-GAP


# -----------------------------------------------------------------------------
# TIPO J -- SEMPLIFICA ÷N  h=133  spazio=90  margine=+6pt
# 8 fraz in 2col*4righe. ROW_H=20, PAD_TOP=8.
# -----------------------------------------------------------------------------
def b_semplifica(cv,y_top,num_blocco=7):
    h=133
    yc=block_open(cv,y_top,h,
        f"● {num_blocco}   SEMPLIFICA la frazione -- dividi per il numero indicato",
        ORANGE,ORANGEL)
    sf(cv,BLACK); cv.setFont("Helvetica",9)
    cv.drawString(X0,yc-2,
        "Dividi numeratore E denominatore per il numero sopra la freccia.")
    frazioni=[("4/8",4),("6/9",3),("10/15",5),("8/12",4),
              ("9/12",3),("6/10",2),("15/20",5),("12/16",4)]
    COLS=2; col_w=CW/COLS; BOX_W=40; BOX_H=16; ROW_H=20; PAD=8
    FRAC_ZONE=44; ARR_ZONE=36; GAP_INNER=6
    for idx,(fraz,mcd) in enumerate(frazioni):
        col_i=idx%COLS; row_i=idx//COLS
        yc_row=yc-PAD-ROW_H//2-row_i*ROW_H
        x_col=X0+col_i*col_w
        sf(cv,ORANGE); cv.setFont("Helvetica-Bold",11)
        cv.drawCentredString(x_col+FRAC_ZONE/2,yc_row-4,fraz)
        ax1=x_col+FRAC_ZONE+GAP_INNER; ax2=ax1+ARR_ZONE
        ss(cv,ORANGE); cv.setLineWidth(1.1)
        cv.line(ax1,yc_row,ax2,yc_row)
        cv.line(ax2,yc_row,ax2-5,yc_row+4)
        cv.line(ax2,yc_row,ax2-5,yc_row-4)
        sf(cv,ORANGE); cv.setFont("Helvetica-Bold",8)
        cv.drawCentredString((ax1+ax2)/2,yc_row+7,f"\u00f7{mcd}")
        bx=ax2+GAP_INNER; by=yc_row-BOX_H/2
        sf(cv,WHITE); ss(cv,(0.45,0.45,0.45)); cv.setLineWidth(0.9)
        cv.roundRect(bx,by,BOX_W,BOX_H,3,fill=1,stroke=1)
        ss(cv,ORANGE); cv.setLineWidth(0.8)
        cv.line(bx+4,by+BOX_H/2,bx+BOX_W-4,by+BOX_H/2)
    return y_top-h-GAP


# -----------------------------------------------------------------------------
# TIPO K -- ABBINAMENTO 2 COLONNE  h=131  spazio=88  margine=+2pt
# y_start=yc-36  (NON yc-22 ne yc-30!)
# NON disegnare linee separatrici. row_h=12.
# -----------------------------------------------------------------------------
def b_abbinamento(cv,y_top,num_blocco=8):
    h=131
    yc=block_open(cv,y_top,h,
        f"● {num_blocco}   ABBINA la frazione alla sua equivalente",
        BROWN,BROWNL)
    sf(cv,BLACK); cv.setFont("Helvetica",9)
    cv.drawString(X0,yc-2,"Scrivi nella casella la lettera della colonna B corrispondente.")
    col_A=["1.  1/2","2.  2/3","3.  3/4","4.  1/3","5.  2/5"]
    col_B=["A.  4/6","B.  6/10","C.  3/6","D.  2/6","E.  9/12"]
    col_ax=X0+30; col_bx=X0+CW/2+30; SQ=12; row_h=12
    y_start=yc-36   # intestaz. a yc-24, prima riga a yc-36, gap=12pt ✓
    sf(cv,BROWN); cv.setFont("Helvetica-Bold",8.5)
    cv.drawString(col_ax-20,y_start+12,"Colonna A")
    cv.drawString(col_bx-20,y_start+12,"Colonna B")
    # NON disegnare linee separatrici!
    for i,(a,b) in enumerate(zip(col_A,col_B)):
        y_row=y_start-i*row_h
        sf(cv,BLACK); cv.setFont("Helvetica-Bold",9.5)
        cv.drawString(col_ax,y_row,a)
        sf(cv,WHITE); ss(cv,(0.45,0.45,0.45)); cv.setLineWidth(0.8)
        cv.rect(col_ax+68,y_row-2,SQ,SQ,fill=1,stroke=1)
        sf(cv,BROWN); cv.setFont("Helvetica-Bold",9.5)
        cv.drawString(col_bx,y_row,b)
    return y_top-h-GAP


# -----------------------------------------------------------------------------
# TIPO L -- CERCHI SETTORI  h=155  spazio=112  margine=0pt (esatto)
# CY_ROW=[24,78] -- NON calcolare con cell_h generico!
# gap righe: top_row1(yc-65) - linee_bot_row0(yc-58) = 7pt OK
# -----------------------------------------------------------------------------
def b_cerchi(cv,y_top,num_blocco=9):
    h=155
    yc=block_open(cv,y_top,h,
        f"● {num_blocco}   OSSERVA i settori colorati -> SCRIVI la frazione",
        RED,REDL)
    sf(cv,BLACK); cv.setFont("Helvetica",9)
    cv.drawString(X0,yc-2,"I settori colorati = numeratore; settori totali = denominatore.")
    R_OUT=13; R_IN=6; CY_ROW=[24,78]
    items_row1=[(1,4),(3,5),(2,6),(1,8)]
    items_row2=[(3,4),(2,5),(5,6),(3,8)]
    COLS=4; cell_w=BW/COLS
    for row_i,items_row in enumerate([items_row1,items_row2]):
        cy_off=CY_ROW[row_i]
        for col_i,(num,den) in enumerate(items_row):
            cx=ML+cell_w*col_i+cell_w/2
            cy=yc-cy_off
            cx=max(ML+R_OUT+4,min(cx,ML+BW-R_OUT-4))
            aper=360.0/max(den,1)
            for i in range(den):
                sa=90+i*aper
                col_fill=(0.85,0.18,0.18) if i<num else (1.0,0.88,0.88)
                sf(cv,col_fill)
                p=cv.beginPath(); p.moveTo(cx,cy)
                steps=max(10,int(aper/3))
                for s in range(steps+1):
                    a=math.radians(sa+s*aper/steps)
                    p.lineTo(cx+R_OUT*math.cos(a),cy+R_OUT*math.sin(a))
                p.close(); cv.drawPath(p,fill=1,stroke=0)
            ss(cv,(0.50,0.10,0.10)); cv.setLineWidth(0.5)
            for i in range(den):
                a=math.radians(90+i*aper)
                cv.line(cx+R_IN*math.cos(a),cy+R_IN*math.sin(a),
                        cx+R_OUT*math.cos(a),cy+R_OUT*math.sin(a))
            cv.setLineWidth(1.1); cv.circle(cx,cy,R_OUT,fill=0,stroke=1)
            sf(cv,WHITE); ss(cv,(0.50,0.10,0.10)); cv.setLineWidth(0.7)
            cv.circle(cx,cy,R_IN,fill=1,stroke=1)
            ln=cy-R_OUT-5; LW=13
            ss(cv,(0.55,0.55,0.55)); cv.setLineWidth(0.5); cv.setDash([2,3])
            cv.line(cx-LW,ln,cx+LW,ln)
            cv.setDash([]); ss(cv,RED); cv.setLineWidth(1.0)
            cv.line(cx-LW,ln-8,cx+LW,ln-8)
            ss(cv,(0.55,0.55,0.55)); cv.setLineWidth(0.5); cv.setDash([2,3])
            cv.line(cx-LW,ln-16,cx+LW,ln-16)
            cv.setDash([])
    return y_top-h-GAP


# -----------------------------------------------------------------------------
# TIPO M -- VERO/FALSO  h variabile: 3 aff=116  4=137  5=158  6=179
# ROW_H=21
# -----------------------------------------------------------------------------
def b_vero_falso(cv,y_top,num_blocco=10):
    affermazioni=[
        "2/4 e 1/2 sono frazioni equivalenti perche' 2x2 = 4x1.",
        "Con lo stesso numeratore, la frazione con denominatore maggiore e' la piu' grande.",
        "Per semplificare 6/8 si divide per 2: si ottiene 3/4.",
        "La frazione 3/7 e' maggiore di 3/9 perche' 7 e' minore di 9.",
    ]
    ROW_H=21; h=TH+9+8+len(affermazioni)*ROW_H+10
    yc=block_open(cv,y_top,h,
        f"● {num_blocco}   VERO o FALSO? -- Cerchia la risposta giusta",
        TEAL,TEALL)
    VF_W=36; VF_GAP=4
    box_v_x=X1-(VF_W*2+VF_GAP); box_f_x=box_v_x+VF_W+VF_GAP
    for i,frase in enumerate(affermazioni):
        y_l=yc-8-i*ROW_H
        cv.saveState(); clip_box(cv,X0,y_l-4,box_v_x-8-X0,ROW_H)
        sf(cv,BLACK); cv.setFont("Helvetica",9)
        cv.drawString(X0,y_l,f"{i+1}.  {frase}")
        cv.restoreState()
        sf(cv,(0.82,1.0,0.82)); ss(cv,(0.10,0.52,0.10)); cv.setLineWidth(0.9)
        cv.rect(box_v_x,y_l-3,VF_W,15,fill=1,stroke=1)
        sf(cv,(0.04,0.40,0.04)); cv.setFont("Helvetica-Bold",7.5)
        cv.drawCentredString(box_v_x+VF_W/2,y_l+4,"VERO")
        sf(cv,(1.0,0.86,0.86)); ss(cv,(0.65,0.10,0.10))
        cv.rect(box_f_x,y_l-3,VF_W,15,fill=1,stroke=1)
        sf(cv,(0.65,0.05,0.05))
        cv.drawCentredString(box_f_x+VF_W/2,y_l+4,"FALSO")
    return y_top-h-GAP


# -----------------------------------------------------------------------------
# TIPO N -- PROBLEMI  h=133  spazio=90  margine=0pt (esatto)
# 2 problemi. step: r1=-13  r2=-12  risposta=-16
# -----------------------------------------------------------------------------
def b_problemi(cv,y_top,num_blocco=11):
    h=133
    yc=block_open(cv,y_top,h,f"● {num_blocco}  LEGGI e RISOLVI",BROWN,BROWNL)
    problemi=[
        ("Sara ha mangiato 2/8 di una torta, Luca ne ha mangiata 1/4.",
         "Chi ne ha mangiata di piu'? (Suggerimento: trova la fraz. equiv. di 1/4 con den. 8.)"),
        ("Una bottiglia e' piena per 3/4. Ne bevo 1/2.",
         "Quanta acqua rimane? (Suggerimento: trova il denominatore comune 4.)"),
    ]
    y_cur=yc-8
    for idx,(r1,r2) in enumerate(problemi):
        sf(cv,BLACK); cv.setFont("Helvetica-Bold",9.5)
        cv.drawString(X0,y_cur,f"{idx+1}.  {r1}")
        y_cur-=13
        cv.setFont("Helvetica",9)
        cv.drawString(X0+10,y_cur,r2)
        y_cur-=12
        cv.drawString(X0+10,y_cur,"Risposta:  __________________________")
        y_cur-=16
    return y_top-h-GAP


# =============================================================================
# GENERA PDF
# =============================================================================
def generate():
    # Verifica layout prima di generare
    _H=H; _GAP=GAP; _avnf=_H-104; _avf=_H-104-20
    _p1=208+_GAP+(TH+9+16+5*84+8)
    _p2=293+_GAP+175+_GAP+96+_GAP+118
    _p3=131+_GAP+155+_GAP+(TH+9+8+4*21+10)+_GAP+133
    for lbl,tot,av in [("PAG1",_p1,_avnf),("PAG2",_p2,_avf),("PAG3",_p3,_avf)]:
        assert tot<=av, f"{lbl} OVERFLOW: {tot:.0f} > {av:.0f}"
        print(f"{lbl}: {tot:.0f}/{av:.0f}  margine={av-tot:.0f}pt OK")

    os.makedirs("/mnt/user-data/outputs",exist_ok=True)
    cv=canvas.Canvas(OUT,pagesize=A4)

    # PAG1 (NO footer):
    draw_header(cv)
    y=TOP
    y=b_theory(cv,y)
    y=b_pizze_scrivi(cv,y,num_blocco=2)
    cv.showPage()

    # PAG2 (footer):
    draw_header(cv); draw_footer(cv)
    y=TOP
    y=b_pizze_colora(cv,y,num_blocco=3)
    y=b_equivalenti(cv,y,num_blocco=4)
    y=b_confronto_num(cv,y,num_blocco=5)
    y=b_addizioni_stesso_den(cv,y,num_blocco=6)
    cv.showPage()

    # PAG3 (footer):
    draw_header(cv); draw_footer(cv)
    y=TOP
    y=b_abbinamento(cv,y,num_blocco=7)
    y=b_cerchi(cv,y,num_blocco=8)
    y=b_vero_falso(cv,y,num_blocco=9)
    y=b_problemi(cv,y,num_blocco=10)
    cv.showPage()

    cv.save()
    print(f"OK -> {OUT}")

if __name__=="__main__":
    generate()
