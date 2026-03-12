#!/usr/bin/env python3
"""
Pipeline Dashboard Generator — Nexus BDR
Reads scored Apollo JSON, outputs interactive HTML dashboard.
Self-contained: no template file needed.

Usage:
    python3 generate_dashboard.py "outputs/scored_apollo_20260304_0133.json"
    open outputs/pipeline_dashboard.html
"""
import sys, json
from pathlib import Path

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 generate_dashboard.py <scored_data.json>")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        data = json.load(f)

    leads = data.get("leads", data.get("prospects", data if isinstance(data, list) else []))
    data_json = json.dumps({"leads": leads}, default=str)

    html = TEMPLATE.replace("__DATA_PLACEHOLDER__", data_json)

    out_dir = Path(__file__).parent.resolve().parent / "outputs"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "pipeline_dashboard.html"
    out_path.write_text(html)
    print(f"  Dashboard: {out_path}")
    print(f"  Run: open \"{out_path}\"")

TEMPLATE = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Nexus BDR Pipeline Dashboard</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Outfit:wght@300;400;500;600;700;800&display=swap');
*{margin:0;padding:0;box-sizing:border-box}
:root{--bg:#0a0a0f;--s1:#12121a;--s2:#1a1a26;--s3:#22222f;--bdr:#2a2a3a;--gold:#c8a84e;--gd:#9a7d3a;--gg:rgba(200,168,78,0.15);--hot:#ff4444;--warm:#ff9f1a;--cool:#4a9eff;--cold:#666688;--grn:#22c55e;--red:#ef4444;--txt:#e8e8f0;--dim:#8888aa;--mut:#555566;--tbf:#c8a84e;--dft:#ff3333}
body{background:var(--bg);color:var(--txt);font-family:'Outfit',sans-serif;min-height:100vh}
body::before{content:'';position:fixed;inset:0;background:url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.03'/%3E%3C/svg%3E");pointer-events:none;z-index:9999}
.c{max-width:1440px;margin:0 auto;padding:40px 24px}
.hdr{text-align:center;margin-bottom:48px}
.hdr::after{content:'';display:block;width:120px;height:2px;background:linear-gradient(90deg,transparent,var(--gold),transparent);margin:20px auto 0}
.hdr h1{font-size:2.4rem;font-weight:800;letter-spacing:-0.02em;background:linear-gradient(135deg,var(--gold),#e8d088,var(--gd));-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:6px}
.hdr .sub{font-size:0.9rem;color:var(--dim);font-weight:300;letter-spacing:0.08em;text-transform:uppercase}
.hdr .dt{font-family:'JetBrains Mono',monospace;font-size:0.72rem;color:var(--mut);margin-top:6px}
.sg{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:14px;margin-bottom:36px}
.sc{background:var(--s1);border:1px solid var(--bdr);border-radius:12px;padding:18px;text-align:center;transition:all .3s}
.sc:hover{border-color:var(--gd);transform:translateY(-2px);box-shadow:0 8px 30px rgba(0,0,0,.3)}
.sv{font-size:2.1rem;font-weight:800;font-family:'JetBrains Mono',monospace}
.sl{font-size:0.7rem;color:var(--dim);text-transform:uppercase;letter-spacing:0.1em;margin-top:3px}
.sc.hot .sv{color:var(--hot)}.sc.warm .sv{color:var(--warm)}.sc.cool .sv{color:var(--cool)}.sc.cold .sv{color:var(--cold)}.sc.total .sv{color:var(--gold)}.sc.tbf .sv{color:var(--tbf)}.sc.dft .sv{color:var(--dft)}.sc.veri .sv{color:var(--grn)}
.sbc{background:var(--s1);border:1px solid var(--bdr);border-radius:12px;padding:20px;margin-bottom:36px}
.sbc h3{font-size:0.75rem;text-transform:uppercase;letter-spacing:0.1em;color:var(--dim);margin-bottom:12px}
.sb{display:flex;height:30px;border-radius:6px;overflow:hidden;gap:2px}
.ss{display:flex;align-items:center;justify-content:center;font-family:'JetBrains Mono',monospace;font-size:0.68rem;font-weight:700;color:#000;transition:all .3s}
.ss:hover{filter:brightness(1.2)}.ss.hot{background:var(--hot)}.ss.warm{background:var(--warm)}.ss.cool{background:var(--cool)}.ss.cold{background:var(--cold)}
.fl{display:flex;gap:10px;margin-bottom:20px;flex-wrap:wrap;align-items:center}
.fb{background:var(--s1);border:1px solid var(--bdr);color:var(--dim);padding:7px 14px;border-radius:8px;cursor:pointer;font-family:'Outfit',sans-serif;font-size:0.78rem;font-weight:500;transition:all .2s}
.fb:hover{border-color:var(--gd);color:var(--txt)}.fb.ac{background:var(--gold);color:#000;border-color:var(--gold);font-weight:700}
.si{background:var(--s1);border:1px solid var(--bdr);color:var(--txt);padding:7px 14px;border-radius:8px;font-family:'Outfit',sans-serif;font-size:0.82rem;width:220px;outline:none;transition:border-color .2s}
.si:focus{border-color:var(--gold)}.si::placeholder{color:var(--mut)}
.tc{background:var(--s1);border:1px solid var(--bdr);border-radius:12px;overflow:hidden;margin-bottom:36px}
.thb{display:flex;justify-content:space-between;align-items:center;padding:14px 18px;border-bottom:1px solid var(--bdr)}
.thb h3{font-size:0.8rem;text-transform:uppercase;letter-spacing:0.08em;color:var(--dim)}
.tcnt{font-family:'JetBrains Mono',monospace;font-size:0.72rem;color:var(--gold)}
table{width:100%;border-collapse:collapse}
th{text-align:left;padding:10px 14px;font-size:0.68rem;text-transform:uppercase;letter-spacing:0.1em;color:var(--mut);border-bottom:1px solid var(--bdr);cursor:pointer;user-select:none;white-space:nowrap;transition:color .2s}
th:hover{color:var(--gold)}th.so{color:var(--gold)}
th .sa{margin-left:4px;font-size:0.58rem}
td{padding:9px 14px;font-size:0.8rem;border-bottom:1px solid rgba(42,42,58,.4);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:200px}
tr{transition:background .15s}tr:hover{background:var(--s2)}
.sbd{display:inline-flex;align-items:center;gap:5px;font-family:'JetBrains Mono',monospace;font-weight:700;font-size:0.78rem}
.sd{width:8px;height:8px;border-radius:50%}.sd.hot{background:var(--hot);box-shadow:0 0 8px var(--hot)}.sd.warm{background:var(--warm);box-shadow:0 0 6px var(--warm)}.sd.cool{background:var(--cool)}.sd.cold{background:var(--cold)}
.bt{display:inline-block;padding:2px 9px;border-radius:4px;font-size:0.68rem;font-weight:700;letter-spacing:0.06em}
.bt.TBF{background:rgba(200,168,78,.12);color:var(--tbf);border:1px solid rgba(200,168,78,.25)}.bt.DFT{background:rgba(255,51,51,.08);color:var(--dft);border:1px solid rgba(255,51,51,.2)}
.tt{font-size:0.7rem;font-weight:600;text-transform:uppercase;letter-spacing:0.04em}
.tt.Hot{color:var(--hot)}.tt.Warm{color:var(--warm)}.tt.Cool{color:var(--cool)}.tt.Cold{color:var(--cold)}
.es .v{color:var(--grn)}.es .iv{color:var(--red)}.es .un{color:var(--warm)}.es .mi{color:var(--mut);font-style:italic}
.dm{font-size:0.68rem;padding:2px 7px;border-radius:4px;background:var(--s3);color:var(--dim)}
.dm.CS{color:var(--gold);background:var(--gg)}
.wfs{background:var(--s1);border:1px solid var(--bdr);border-radius:12px;padding:24px;margin-bottom:36px}
.wfs h2{font-size:1.1rem;margin-bottom:18px;color:var(--gold)}
.wc{background:var(--s2);border:1px solid var(--bdr);border-radius:8px;padding:14px 18px;margin-bottom:10px;display:flex;align-items:center;gap:14px;transition:border-color .2s}
.wc:hover{border-color:var(--gd)}
.wn{width:32px;height:32px;border-radius:50%;background:var(--gg);color:var(--gold);display:flex;align-items:center;justify-content:center;font-family:'JetBrains Mono',monospace;font-weight:700;font-size:0.8rem;flex-shrink:0}
.wi h4{font-size:0.85rem;font-weight:600}.wi p{font-size:0.72rem;color:var(--dim);margin-top:2px}
@media(max-width:768px){.sg{grid-template-columns:repeat(2,1fr)}.hdr h1{font-size:1.5rem}td,th{padding:7px 8px;font-size:0.7rem}}
</style>
</head>
<body>
<div class="c">
<div class="hdr"><h1>Nexus BDR Pipeline</h1><div class="sub">Sales Intelligence Dashboard</div><div class="dt" id="dt"></div></div>
<div class="sg" id="sg"></div>
<div class="sbc"><h3>Pipeline Distribution</h3><div class="sb" id="sb"></div></div>
<div class="fl">
<button class="fb ac" data-f="all">All</button>
<button class="fb" data-f="hot">Hot</button>
<button class="fb" data-f="warm">Warm</button>
<button class="fb" data-f="cool">Cool</button>
<button class="fb" data-f="cold">Cold</button>
<button class="fb" data-f="tbf">TBF</button>
<button class="fb" data-f="dft">DFT</button>
<button class="fb" data-f="email">Has Email</button>
<button class="fb" data-f="veri">Verified</button>
<input type="text" class="si" placeholder="Search company or name..." id="srch">
</div>
<div class="tc"><div class="thb"><h3>Pipeline Contacts</h3><span class="tcnt" id="cnt">0</span></div>
<div style="overflow-x:auto"><table><thead><tr>
<th data-s="score" class="so">Score <span class="sa">&#9660;</span></th>
<th data-s="company">Company</th>
<th data-s="name">Contact</th>
<th data-s="title">Title</th>
<th data-s="dm">Level</th>
<th data-s="brand">Brand</th>
<th data-s="temp">Temp</th>
<th data-s="email">Email</th>
<th data-s="state">State</th>
<th>Reasons</th>
</tr></thead><tbody id="tb"></tbody></table></div></div>
<div class="wfs"><h2>GHL Workflows to Build</h2><div id="wl"></div></div>
</div>
<script>
let D=[],CF='all',CS='score',SD='desc',ST='';
const R=__DATA_PLACEHOLDER__;
function init(){D=R.leads||R||[];document.getElementById('dt').textContent=new Date().toLocaleDateString('en-US',{weekday:'long',year:'numeric',month:'long',day:'numeric'});rS();rB();rT();rW();eL()}
function rS(){const h=D.filter(d=>d.nexus_lead_score>=80).length,w=D.filter(d=>d.nexus_lead_score>=60&&d.nexus_lead_score<80).length,co=D.filter(d=>d.nexus_lead_score>=40&&d.nexus_lead_score<60).length,cl=D.filter(d=>d.nexus_lead_score<40).length,tb=D.filter(d=>d.nexus_brand==='TBF').length,df=D.filter(d=>d.nexus_brand==='DFT').length,v=D.filter(d=>d.email_verification&&d.email_verification.status==='valid').length;
document.getElementById('sg').innerHTML='<div class="sc total"><div class="sv">'+D.length+'</div><div class="sl">Total</div></div><div class="sc hot"><div class="sv">'+h+'</div><div class="sl">Hot 80+</div></div><div class="sc warm"><div class="sv">'+w+'</div><div class="sl">Warm 60-79</div></div><div class="sc cool"><div class="sv">'+co+'</div><div class="sl">Cool 40-59</div></div><div class="sc cold"><div class="sv">'+cl+'</div><div class="sl">Cold &lt;40</div></div><div class="sc tbf"><div class="sv">'+tb+'</div><div class="sl">TBF</div></div><div class="sc dft"><div class="sv">'+df+'</div><div class="sl">DFT</div></div><div class="sc veri"><div class="sv">'+v+'</div><div class="sl">Verified</div></div>'}
function rB(){const h=D.filter(d=>d.nexus_lead_score>=80).length,w=D.filter(d=>d.nexus_lead_score>=60&&d.nexus_lead_score<80).length,co=D.filter(d=>d.nexus_lead_score>=40&&d.nexus_lead_score<60).length,cl=D.filter(d=>d.nexus_lead_score<40).length,t=D.length||1;
document.getElementById('sb').innerHTML='<div class="ss hot" style="width:'+h/t*100+'%">'+h+'</div><div class="ss warm" style="width:'+w/t*100+'%">'+w+'</div><div class="ss cool" style="width:'+co/t*100+'%">'+co+'</div><div class="ss cold" style="width:'+cl/t*100+'%">'+cl+'</div>'}
function gF(){let f=[...D];if(ST){const s=ST.toLowerCase();f=f.filter(d=>(d.company_name||'').toLowerCase().includes(s)||(d.contact_name||'').toLowerCase().includes(s)||(d.email||'').toLowerCase().includes(s)||(d.title||'').toLowerCase().includes(s))}
if(CF==='hot')f=f.filter(d=>d.nexus_lead_score>=80);else if(CF==='warm')f=f.filter(d=>d.nexus_lead_score>=60&&d.nexus_lead_score<80);else if(CF==='cool')f=f.filter(d=>d.nexus_lead_score>=40&&d.nexus_lead_score<60);else if(CF==='cold')f=f.filter(d=>d.nexus_lead_score<40);else if(CF==='tbf')f=f.filter(d=>d.nexus_brand==='TBF');else if(CF==='dft')f=f.filter(d=>d.nexus_brand==='DFT');else if(CF==='email')f=f.filter(d=>d.email);else if(CF==='veri')f=f.filter(d=>d.email_verification&&d.email_verification.status==='valid');
f.sort(function(a,b){var va,vb;if(CS==='score'){va=a.nexus_lead_score||0;vb=b.nexus_lead_score||0}else if(CS==='company'){va=(a.company_name||'').toLowerCase();vb=(b.company_name||'').toLowerCase()}else if(CS==='name'){va=(a.contact_name||'').toLowerCase();vb=(b.contact_name||'').toLowerCase()}else if(CS==='title'){va=(a.title||'').toLowerCase();vb=(b.title||'').toLowerCase()}else if(CS==='brand'){va=a.nexus_brand||'';vb=b.nexus_brand||''}else if(CS==='dm'){var o={'C-Suite':0,'VP':1,'Director':2,'Manager':3,'Individual':4};va=o[a.decision_maker_level]!==undefined?o[a.decision_maker_level]:5;vb=o[b.decision_maker_level]!==undefined?o[b.decision_maker_level]:5}else if(CS==='email'){va=a.email?0:1;vb=b.email?0:1}else if(CS==='state'){va=(a.state||'');vb=(b.state||'')}else{va=a.nexus_lead_score||0;vb=b.nexus_lead_score||0}
if(typeof va==='string')return SD==='asc'?va.localeCompare(vb):vb.localeCompare(va);return SD==='asc'?va-vb:vb-va});return f}
function gc(s){return s>=80?'hot':s>=60?'warm':s>=40?'cool':'cold'}
function gt(s){return s>=80?'Hot':s>=60?'Warm':s>=40?'Cool':'Cold'}
function rT(){var f=gF();document.getElementById('cnt').textContent=f.length+' contacts';
var h='';for(var i=0;i<f.length;i++){var d=f[i],s=d.nexus_lead_score||0,sc=gc(s),tp=gt(s),br=d.nexus_brand||'?',dm=d.decision_maker_level||'',dmc=dm==='C-Suite'?'CS':'';
var eh='';if(d.email){var ev=d.email_verification;if(ev&&ev.status==='valid')eh='<span class="v">'+d.email+'</span>';else if(ev&&ev.status==='invalid')eh='<span class="iv"><s>'+d.email+'</s></span>';else if(ev)eh='<span class="un">'+d.email+'</span>';else eh=d.email}else{eh='<span class="mi">\u2014</span>'}
var rs=(d.score_reasons||[]).slice(0,3).join(', ');
h+='<tr><td><div class="sbd"><span class="sd '+sc+'"></span>'+s+'</div></td><td>'+( d.company_name||'?')+'</td><td>'+(d.contact_name||'?')+'</td><td>'+(d.title||'').substring(0,28)+'</td><td><span class="dm '+dmc+'">'+dm+'</span></td><td><span class="bt '+br+'">'+br+'</span></td><td><span class="tt '+tp+'">'+tp+'</span></td><td class="es">'+eh+'</td><td>'+(d.state||'').substring(0,2).toUpperCase()+'</td><td style="font-size:0.66rem;color:var(--mut);max-width:240px">'+rs+'</td></tr>'}
document.getElementById('tb').innerHTML=h}
function rW(){var w=[{n:1,t:'Auto-Tag by Score',d:'Categorize contacts into hot/warm/cool/cold tags'},{n:2,t:'TBF Outreach Sequence',d:'4-touch email sequence for hot/warm TBF leads'},{n:3,t:'DFT Outreach Sequence',d:'Edgy 4-touch sequence for hot/warm DFT leads'},{n:4,t:'Engagement Escalation',d:'Alert on 3+ opens or clicks'},{n:5,t:'Reply Handler',d:'Instant alert + CRM update on reply'},{n:6,t:'Re-engagement',d:'Re-engage stale leads after 30 days'},{n:7,t:'Sample Follow-Up',d:'Auto follow-up after samples sent'},{n:8,t:'Trade Show Pre-Event',d:'Warm outreach before events'},{n:9,t:'Weekly Pipeline Report',d:'Monday morning summary'},{n:10,t:'Hot Lead Alert',d:'Instant SMS for 80+ score leads'}];
var h='';for(var i=0;i<w.length;i++){h+='<div class="wc"><div class="wn">'+w[i].n+'</div><div class="wi"><h4>'+w[i].t+'</h4><p>'+w[i].d+'</p></div></div>'}
document.getElementById('wl').innerHTML=h}
function eL(){var btns=document.querySelectorAll('.fb');for(var i=0;i<btns.length;i++){btns[i].addEventListener('click',function(){for(var j=0;j<btns.length;j++)btns[j].classList.remove('ac');this.classList.add('ac');CF=this.getAttribute('data-f');rT()})}
var ths=document.querySelectorAll('th[data-s]');for(var i=0;i<ths.length;i++){ths[i].addEventListener('click',function(){var c=this.getAttribute('data-s');if(CS===c)SD=SD==='desc'?'asc':'desc';else{CS=c;SD='desc'}for(var j=0;j<ths.length;j++){ths[j].classList.remove('so');var a=ths[j].querySelector('.sa');if(a)a.textContent=''}this.classList.add('so');var ar=this.querySelector('.sa');if(ar)ar.textContent=SD==='desc'?'\u25BC':'\u25B2';rT()})}
document.getElementById('srch').addEventListener('input',function(e){ST=e.target.value;rT()})}
init();
</script>
</body>
</html>'''

if __name__ == "__main__":
    main()
