"""
BRAZILIAN E-COMMERCE | GERA dashboard_integrated.html

Lê dashboard.html (NUNCA o altera) e grava uma cópia em que:
  * os dados embutidos (DATA/PAYMENTS, ~44 MB) são removidos;
  * a página Comercial busca KPIs, séries e rankings em /api/commercial
    (filtros e opções em /api/filters);
  * os valores fixos das páginas Logística e Investigação vêm de
    /api/logistics e /api/investigation;
  * layout, tema, gráficos, filtros, anotações e textos são preservados.
Mudanças de comportamento aprovadas:
  * comparação com o mês anterior usa a mesma regra de pagamento do filtro
    principal (pedido com ao menos um pagamento do tipo);
  * % de pedidos entregues calculado pela API (97,0%, não 97,8%).

Uso (na raiz do projeto):
    python Scripts\\build_integrated_dashboard.py
A API é procurada em http://127.0.0.1:8000 (ou ?api=URL na barra de endereço).
"""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SRC = sys.argv[1] if len(sys.argv) > 1 else BASE_DIR / "dashboard.html"
DST = sys.argv[2] if len(sys.argv) > 2 else BASE_DIR / "dashboard_integrated.html"
assert Path(SRC).resolve() != Path(DST).resolve(), "O destino não pode ser o dashboard original."
html = open(SRC, encoding="utf-8").read()
lines = html.split("\n")


def rep(text, old, new, count=1):
    assert text.count(old) == count, (old[:80], text.count(old))
    return text.replace(old, new)


# ------------------------------------------------------------------
# HTML estático: ids nos valores fixos das páginas 2 e 3 ("—" até carregar)
# ------------------------------------------------------------------
l15 = lines[15]
l15 = rep(l15, '<div class="value">96.470</div>', '<div class="value" id="log_n">—</div>')
l15 = rep(l15, '<div class="value">91,89%</div>', '<div class="value" id="log_ontime">—</div>')
l15 = rep(l15, '<div class="value">12,56 dias</div>', '<div class="value" id="log_avg">—</div>')
l15 = rep(l15, '<div class="value">11,18 dias</div>', '<div class="value" id="log_early">—</div>')
l15 = rep(l15, '<div class="insight-value">AL · 76,07%</div>', '<div class="insight-value" id="log_ins_state">—</div>')
l15 = rep(l15, '<div class="insight-value">8,11%</div>', '<div class="insight-value" id="log_ins_late">—</div>')
lines[15] = l15

lines[20] = rep(lines[20], '<div class="value">95.994</div>', '<div class="value" id="p3_n">—</div>')
lines[21] = rep(lines[21], '<div class="value">0,543</div>', '<div class="value" id="p3_spearman">—</div>')
lines[22] = rep(lines[22], '<div class="value">13,66%</div>', '<div class="value" id="p3_late2000">—</div>')
lines[23] = rep(lines[23], '<div class="value">R$ 39,88</div>', '<div class="value" id="p3_freight2000">—</div>')
lines[35] = ('<article class="insight"><div class="insight-label">DISTÂNCIA</div>'
             '<div class="insight-value" id="p3_ins_dist">—</div><p id="p3_ins_dist_p">—</p></article>')
lines[36] = ('<article class="insight"><div class="insight-label">RISCO DE ATRASO</div>'
             '<div class="insight-value" id="p3_ins_late">—</div><p>A taxa de atraso é mais que o dobro '
             'nas entregas acima de 2.000 km comparada à faixa até 100 km.</p></article>')
lines[37] = ('<article class="insight"><div class="insight-label">FRETE</div>'
             '<div class="insight-value" id="p3_ins_freight">—</div><p>O frete médio é quase 3 vezes maior '
             'acima de 2.000 km. Distância afeta custo e duração, mas não explica sozinha o atraso.</p></article>')
lines[39] = rep(lines[39], "dias de entrega = 0,543; distância e dias de atraso = −0,179.",
                'dias de entrega = <span id="p3_note_sp1">—</span>; distância e dias de atraso = '
                '<span id="p3_note_sp2">—</span>.')

# ------------------------------------------------------------------
# Script 1: remove DATA/PAYMENTS embutidos; cliente da API
# ------------------------------------------------------------------
l41 = lines[41]
helpers = l41[l41.index("];const $=") + 2:]
assert helpers.startswith("const $=")
lines[41] = "<script>" + r"""
// ===== Integração com a API (FastAPI) =====
// Base da API: padrão http://127.0.0.1:8000; outra pode ser passada em ?api=URL
const API_BASE=(new URLSearchParams(location.search).get('api')||'http://127.0.0.1:8000').replace(/\/$/,'');
async function api(path,params={}){const q=new URLSearchParams(Object.entries(params).filter(([,v])=>v!==undefined&&v!==null&&v!==''));const r=await fetch(API_BASE+path+(q.toString()?'?'+q:''));if(!r.ok)throw new Error('HTTP '+r.status+' em '+path);return r.json()}
function apiError(err){let b=document.getElementById('apiError');if(!b){b=document.createElement('div');b.id='apiError';b.style.cssText='margin:8px 14px;padding:10px 14px;border:1px solid #875078;border-radius:10px;background:#2a1830;color:#fda4af;font-size:12px';document.querySelector('header').after(b)}b.textContent='Não foi possível carregar os dados da API ('+API_BASE+'). Verifique se ela está rodando: uvicorn api.main:app --reload — '+err.message;console.error(err)}
const pct2=v=>v.toFixed(2).replace('.',',');
""" + helpers

# fill(): mantém a função; as opções passam a vir de /api/filters
l42 = lines[42]
lines[42] = l42[:l42.index("fill('period'")]

lines[50] = "// Filtro de pagamento aplicado pela API: pedidos com ao menos um pagamento do tipo (mesma regra no mês anterior)."

orig_53, orig_54, orig_55 = lines[53], lines[54], lines[55]
draw_monthly = orig_53[orig_53.index("let mk=Object.keys(m).sort();"):]
draw_payments = orig_55[orig_55.index("draw('payments'"):]
orig_63 = lines[63]
ins_payment = orig_63[orig_63.index("$('ins-payment')"):]

new_update = (
    "let reqSeq=0;\n"
    "async function update(){const seq=++reqSeq;let a=$('period').value,b=$('state').value,c=$('category').value,e=$('payment').value;let res;"
    "try{res=await api('/api/commercial',{period:a,state:b,category:c,payment:e})}catch(err){apiError(err);return}if(seq!==reqSeq)return;"
    "let k=res.kpis,rev=k.revenue;$('revenue').textContent=fmt(rev);$('orders').textContent=num(k.orders);$('ticket').textContent=fmt(k.average_ticket);\n"
    "if(a==='2018-09'){$('revenueDelta').textContent='Set/2018 parcial (até 03/09) — comparação não exibida';$('revenueDelta').style.color='#fbbf24'}"
    "else if(a){let cmp=res.comparison;if(cmp){let pct=cmp.change_pct;$('revenueDelta').textContent=pct===null?'Sem base para comparação':`${pct>=0?'▲':'▼'} ${Math.abs(pct).toFixed(1).replace('.',',')}% vs ${monthPt(cmp.previous_period)}`;"
    "$('revenueDelta').style.color=pct===null?'#9aabc8':pct>=0?'#6ee7b7':'#fda4af'}else{$('revenueDelta').textContent='Sem mês anterior disponível';$('revenueDelta').style.color='#9aabc8'}}"
    "else{$('revenueDelta').textContent='Selecione um mês para comparar';$('revenueDelta').style.color='#9aabc8'}$('customers').textContent=num(k.customers);\n"
    "let m={},cat={},st={};res.monthly.forEach(x=>{m[x.year_month]=x.revenue});res.categories.forEach(x=>{cat[x.category_label]=x.revenue});res.states.forEach(x=>{st[x.state]=x.revenue});"
    + draw_monthly + "\n"
    + orig_54 + "\n"
    + "let pays={};res.payments.forEach(x=>{let key=paymentLabel(x.payment_type);pays[key]=(pays[key]||0)+x.value});" + draw_payments + "\n"
    + "\n".join(lines[56:62]) + "\n"
    + "// Pagamentos já vêm da API na granularidade de pagamento (sem multiplicar por itens).\n"
    + "let paymentTotals=pays;let topPayment=Object.entries(paymentTotals).sort((x,y)=>y[1]-x[1])[0],paymentGrandTotal=Object.values(paymentTotals).reduce((a,b)=>a+b,0);"
    + ins_payment
)
assert lines[64] == "}", lines[64]
lines[51:64] = [new_update]
# após a substituição, os índices abaixo de 64 deslocam: recalcula por conteúdo
idx65 = next(i for i, l in enumerate(lines) if l.startswith("['period','state','category','payment'].forEach"))
lines[idx65] = rep(lines[idx65], "update()};update();",
                   "update()};\n"
                   "async function init(){try{const f=await api('/api/filters');fill('period',f.periods);fill('state',f.states);"
                   "fill('category',f.categories.map(x=>x.value));fill('payment',f.payment_types)}catch(err){apiError(err);return}update()}init();")

# ------------------------------------------------------------------
# Script 2: página 2 (LOG) e página 3 vindas da API
# ------------------------------------------------------------------
idx_log = next(i for i, l in enumerate(lines) if l.startswith("const LOG="))
lines[idx_log] = (
    "let LOG=null;\n"
    "async function loadLog(){if(LOG)return LOG;const r=await api('/api/logistics');"
    "LOG={n:r.kpis.orders,avg:r.kpis.avg_days,median:r.kpis.median_days,ontime:r.kpis.on_time_pct,late:r.kpis.late_pct,early:r.kpis.early_days,"
    "monthly:r.monthly.map(x=>({month:x.year_month,orders:x.orders,avg_days:x.avg_days,ontime:x.on_time})),"
    "states:r.states.map(x=>({customer_state:x.customer_state,orders:x.orders,avg_days:x.avg_days,ontime:x.on_time,late:x.late})),status:Object.fromEntries(r.status.map(x=>[x.order_status,x.orders])),total:r.total_orders};"
    "$('log_n').textContent=num(LOG.n);$('log_ontime').textContent=pct2(LOG.ontime)+'%';$('log_avg').textContent=pct2(LOG.avg)+' dias';"
    "$('log_early').textContent=pct2(LOG.early)+' dias';const worst=LOG.states[0];"
    "$('log_ins_state').textContent=worst?worst.customer_state+' · '+pct2(worst.ontime*100)+'%':'—';$('log_ins_late').textContent=pct2(LOG.late)+'%';return LOG}"
)

idx_draw = idx_log + 1
dl = lines[idx_draw]
dl = rep(dl, "function drawLog(){", "async function drawLog(){try{await loadLog()}catch(err){apiError(err);return}")
start = dl.index("document.getElementById('log_status_bar').innerHTML='")
end = dl.index("'; }", start)
dl = dl[:start] + (
    "const S=LOG.status,dshare=LOG.total?(S.delivered||0)/LOG.total*100:0;"
    "document.getElementById('log_status_bar').innerHTML=`<div style=\"padding:18px 20px;color:#a9b9dc;font-size:11px;line-height:1.55;box-sizing:border-box;overflow-y:auto;max-height:250px\">"
    "<div style=\"font-size:13px;font-weight:700;color:#e8edf9;margin-bottom:10px\">LEITURA DO STATUS</div><div style=\"display:grid;grid-template-columns:1fr 1fr;gap:8px\">"
    "<div><span style=\"color:#8b7cf6;font-weight:700\">${num(S.delivered||0)}</span><br>Pedidos entregues</div>"
    "<div><span style=\"color:#e879a7;font-weight:700\">${num(S.shipped||0)}</span><br>Pedidos enviados</div>"
    "<div><span style=\"color:#f6bd60;font-weight:700\">${num(S.canceled||0)}</span><br>Cancelados</div>"
    "<div><span style=\"color:#4f9da6;font-weight:700\">${num(S.unavailable||0)}</span><br>Indisponíveis</div></div>"
    "<hr style=\"border-color:#293149;margin:10px 0\"><div style=\"color:#e879a7;font-weight:700;font-size:12px\">${dshare.toFixed(1).replace('.',',')}% dos pedidos estão entregues</div>"
    "<div style=\"margin-top:4px\">Os demais status representam cerca de ${(100-dshare).toFixed(1).replace('.',',')}% do volume total. "
    "Acompanhe enviados e cancelados como pontos de atenção operacional.</div></div>`; }"
) + dl[end + len("'; }"):]
lines[idx_draw] = dl

idx_p3 = next(i for i, l in enumerate(lines) if l == "function drawPage3(){")
lines[idx_p3] = (
    "let INV=null;\n"
    "async function drawPage3(){try{if(!INV)INV=await api('/api/investigation')}catch(err){apiError(err);return}"
    "const K=INV.kpis,B=INV.distance_bands,F=INV.freight_bands,r2=v=>Math.round(v*100)/100,brl=v=>'R$ '+pct2(v);"
    "$('p3_n').textContent=num(K.orders_with_distance);$('p3_spearman').textContent=K.spearman_distance_days.toFixed(3).replace('.',',');"
    "$('p3_late2000').textContent=pct2(K.late_pct_over_2000km)+'%';$('p3_freight2000').textContent=brl(K.avg_freight_over_2000km);"
    "$('p3_note_sp1').textContent=K.spearman_distance_days.toFixed(3).replace('.',',');$('p3_note_sp2').textContent=K.spearman_distance_delay.toFixed(3).replace('.',',').replace('-','−');"
    "const b0=B[0],b5=B[B.length-1];$('p3_ins_dist').textContent=pct2(b5.avg_days)+' dias';"
    "$('p3_ins_dist_p').textContent=`Pedidos acima de 2.000 km levam, em média, ${pct2(b5.avg_days)} dias — contra ${pct2(b0.avg_days)} dias até 100 km. O tempo de entrega cresce conforme a distância.`;"
    "$('p3_ins_late').textContent=pct2(b5.late_pct)+'% versus '+pct2(b0.late_pct)+'%';$('p3_ins_freight').textContent=brl(b5.avg_freight)+' versus '+brl(b0.avg_freight);"
)
body = lines[idx_p3 + 1: idx_p3 + 13]
body_txt = "\n".join(body)
body_txt = rep(body_txt, "const days=[6.51,9.96,12.63,14.72,17.95,21.18],late=[6.43,6.37,7.77,8.45,10.76,13.66],freight=[13.35,18.83,22.39,24.85,33.09,39.88];",
               "const days=B.map(x=>r2(x.avg_days)),late=B.map(x=>r2(x.late_pct)),freight=B.map(x=>r2(x.avg_freight));")
body_txt = rep(body_txt, "const freightLabels=['Até R$ 12,83','R$ 12,83–15,64','R$ 15,64–18,59','R$ 18,59–27,38','Acima de R$ 27,38'];",
               "const fc=INV.freight_cuts.map(pct2);const freightLabels=['Até R$ '+fc[0],'R$ '+fc[0]+'–'+fc[1],'R$ '+fc[1]+'–'+fc[2],'R$ '+fc[2]+'–'+fc[3],'Acima de R$ '+fc[3]];")
body_txt = rep(body_txt, "const fm=[9.75,14.48,17.19,22.23,50.36],fl=[6.08,7.24,8.86,9.05,9.35];",
               "const fm=F.map(x=>r2(x.avg_freight)),fl=F.map(x=>r2(x.late_pct));")
body_txt = rep(body_txt, "const states=['AL','MA','PI','CE','SE','BA','RJ','TO'],rates=[23.93,19.67,15.97,15.32,15.22,14.04,13.47,12.77];",
               "const states=INV.states.map(x=>x.customer_state),rates=INV.states.map(x=>r2(x.late_pct));")
lines[idx_p3 + 1: idx_p3 + 13] = body_txt.split("\n")

out = "\n".join(lines)
out = rep(out, "<title>Brazilian E-commerce | Analytics</title>", "<title>Brazilian E-commerce | Analytics (API)</title>")
open(DST, "w", encoding="utf-8").write(out)
print("gerado", DST, len(out), "bytes")
