#!/usr/bin/env python3
"""Build a self-contained, fixture-only TAP journey mockup (v1 and v2)."""
import argparse
import hashlib
import json
import re
from pathlib import Path

SCREEN_ID = re.compile(r"screen-\d{2,}$")
LANE_KINDS = {"happy-path", "empty-state", "error-fallback", "alternate"}

def validate(s):
    for key in ("title",):
        if not s.get(key): raise ValueError(f"scenario thiếu trường: {key}")
    if "screens" not in s:
        for key in ("chat", "display", "transitions"):
            if key not in s: raise ValueError(f"scenario v1 thiếu trường: {key}")
        return 1
    screens, flow = s["screens"], s.get("flowMap", {})
    if not screens or not flow.get("startScreenId") or not flow.get("lanes") or "transitions" not in flow:
        raise ValueError("scenario v2 cần screens và flowMap (startScreenId, lanes, transitions)")
    ids = {x.get("id") for x in screens}
    if len(ids) != len(screens) or not all(isinstance(x, str) and SCREEN_ID.fullmatch(x) for x in ids):
        raise ValueError("screen id phải duy nhất và có dạng screen-01")
    if sorted(x.get("number") for x in screens) != list(range(1, len(screens) + 1)):
        raise ValueError("screen number phải liên tiếp từ 1")
    lane_ids = {x.get("id") for x in flow["lanes"]}
    if not lane_ids or any(x.get("kind") not in LANE_KINDS for x in flow["lanes"]): raise ValueError("lane không hợp lệ")
    if flow["startScreenId"] not in ids: raise ValueError("startScreenId không tồn tại")
    for t in flow["transitions"]:
        if not {"id","fromScreenId","toScreenId","laneId","trigger","ctaLabel","expectedResult"} <= set(t): raise ValueError("transition thiếu field bắt buộc")
        if t["fromScreenId"] not in ids or t["toScreenId"] not in ids or t["laneId"] not in lane_ids: raise ValueError("transition tham chiếu không hợp lệ")
        if t.get("fallback") and t["fallback"] not in ids: raise ValueError("fallback không tồn tại")
    if not s.get("fixtures"): raise ValueError("scenario v2 cần fixtures fixture-only")
    return 2

def main():
    p = argparse.ArgumentParser(); p.add_argument("--scenario", required=True); p.add_argument("--out", required=True); a = p.parse_args()
    s = json.loads(Path(a.scenario).read_text(encoding="utf-8")); version = validate(s)
    payload = json.dumps(s, ensure_ascii=False).replace("<", "\\u003c")
    fingerprint = hashlib.sha256(json.dumps(s, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:12]
    html = f'''<!doctype html><html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{s['title']} — Mockup</title><style>
*{{box-sizing:border-box}}body{{margin:0;background:#f4f7fb;color:#172033;font:15px system-ui,sans-serif}}header{{padding:14px 22px;background:#172033;color:white;font-weight:750}}small{{float:right;color:#c7d3e6}}#assumptions,#flow,#screens{{padding:12px 22px;background:white;border-bottom:1px solid #d9e1ec}}.lane,.screen-nav,button{{margin:3px;padding:6px 9px;border:1px solid #b8c8e4;border-radius:7px;background:white;color:#1647cf;font:inherit;cursor:pointer}}.happy-path{{border-left:4px solid #198754}}.empty-state{{border-left:4px solid #d08a00}}.error-fallback{{border-left:4px solid #c43c45}}.alternate{{border-left:4px solid #725ac1}}#flow p{{margin:7px 0;padding:7px;background:#f7f9fc}}main{{display:grid;grid-template-columns:1fr 1fr;min-height:480px}}section{{padding:20px;background:white}}#display{{background:#f7f9fc;border-left:1px solid #d9e1ec}}.card{{margin:10px 0;padding:12px;border:1px solid #d9e1ec;border-radius:10px}}#timeline{{position:fixed;right:14px;bottom:14px;width:min(420px,90vw);max-height:180px;overflow:auto;background:#172033;color:#e5edf8;padding:10px;border-radius:9px;font:12px ui-monospace,monospace}}@media(max-width:700px){{main{{grid-template-columns:1fr}}#display{{border-left:0;border-top:1px solid #d9e1ec}}small{{float:none;display:block}}}}
</style><body><header>Mockup journey · Fixture-only · no MCP/upstream write <small>v{version} · fingerprint {fingerprint}</small></header><div id="assumptions"></div><div id="flow" aria-label="Flow map"></div><nav id="screens" aria-label="Screen index"></nav><main><section><h2>Chat</h2><div id="chat"></div></section><section id="display"><h2>Display panel</h2><div id="panel"></div></section></main><aside id="timeline" aria-label="Event timeline"></aside><script>const S={payload},V=S.screens?2:1;let current=V===2?S.flowMap.startScreenId:'screen-01',events=[];const esc=x=>String(x??'');function log(kind,d={{}}){{events.unshift({{kind,screenId:current,...d}});timeline.innerHTML=events.map(e=>`<div>${{e.kind}} · screenId=${{e.screenId}} · laneId=${{e.laneId||'-'}} · transitionId=${{e.transitionId||'-'}}</div>`).join('')}}function screen(){{return V===2?S.screens.find(x=>x.id===current):{{id:'screen-01',number:1,name:S.title,goal:S.title,chat:S.chat,display:S.display}}}}function go(id,t){{current=id;log('transition',{{laneId:t?.laneId,transitionId:t?.id}});render()}}function render(){{const x=screen();screens.innerHTML=V===2?S.screens.map(q=>`<button class="screen-nav" aria-label="Screen ${{String(q.number).padStart(2,'0')}} — ${{esc(q.name)}}" onclick="go('${{q.id}}')">Screen ${{String(q.number).padStart(2,'0')}} — ${{esc(q.name)}}</button>`).join(''):'';assumptions.innerHTML=(S.assumptions||[]).map(a=>`<div>${{esc(a.id)}}: ${{esc(a.text)}}</div>`).join('');if(V===2){{flow.innerHTML='<strong>Flow map</strong><div>'+S.flowMap.lanes.map(l=>`<button class="lane ${{l.kind}}" aria-label="${{esc(l.label)}}">${{esc(l.label)}}: ${{esc(l.description)}}</button>`).join('')+'</div>'+S.flowMap.transitions.map(t=>`<p class="${{S.flowMap.lanes.find(l=>l.id===t.laneId).kind}}">Screen ${{S.screens.find(q=>q.id===t.fromScreenId).number.toString().padStart(2,'0')}} → CTA “${{esc(t.ctaLabel)}}” → Screen ${{S.screens.find(q=>q.id===t.toScreenId).number.toString().padStart(2,'0')}}${{t.fallback?' · fallback → '+t.fallback:''}}</p>`).join('')}}else flow.innerHTML='';chat.innerHTML=(x.chat?.messages||[]).map(m=>`<p><b>${{esc(m.role||'assistant')}}:</b> ${{esc(m.text)}}</p>`).join('')||'<p>Fixture chat</p>';panel.innerHTML=`<h3>Screen ${{String(x.number).padStart(2,'0')}} — ${{esc(x.name)}}</h3><p><b>Goal:</b> ${{esc(x.goal)}}</p><h4>${{esc(x.display?.title||S.title)}}</h4>`+(x.display?.cards||[]).map(c=>`<div class="card"><b>${{esc(c.title)}}</b><br>${{esc(c.price)}} · ${{esc(c.meta)}}</div>`).join('');if(V===2)S.flowMap.transitions.filter(t=>t.fromScreenId===current).forEach(t=>{{let b=document.createElement('button');b.textContent=`Screen ${{String(x.number).padStart(2,'0')}} → CTA “${{t.ctaLabel}}” → Screen ${{String(S.screens.find(q=>q.id===t.toScreenId).number).padStart(2,'0')}}`;b.setAttribute('aria-label',b.textContent);b.onclick=()=>go(t.toScreenId,t);panel.append(b)}});}}log('init');render()</script></body></html>'''
    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(html, encoding="utf-8"); print(out.resolve())
if __name__ == "__main__": main()
