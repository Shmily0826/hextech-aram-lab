#!/usr/bin/env python3
"""
重新生成审核工具 HTML，使用最新的候选数据。
"""
import json, sys, os, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CANDIDATES_PATH = os.path.join(PROJECT, "pipeline", "output", "augment_import_candidates.json")
TOOLS_PATH = os.path.join(PROJECT, "tools", "review_candidates.html")

with open(CANDIDATES_PATH, "r", encoding="utf-8") as f:
    candidates = json.load(f)

# Build compact JSON for embedding (only fields needed by the review tool)
review_data = []
for c in candidates:
    entry = {
        "id": c["id"],
        "name": c["name"],
        "name_en": c["name_en"],
        "tier": c["tier"],
        "effect": c.get("effect", ""),
        "effect_en": c.get("effect_en", ""),
        "has_zh": bool(c.get("effect", "")),
        "src": c.get("source", {}).get("type", "unknown")
    }
    review_data.append(entry)

data_json = json.dumps(review_data, ensure_ascii=False, separators=(',', ':'))

html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>增强导入审核工具 - Hex ARAM Lab</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: -apple-system, "Segoe UI", "Microsoft YaHei", sans-serif; background: #0f1117; color: #e0e0e0; min-height: 100vh; padding: 20px; }
  .header { text-align: center; margin-bottom: 24px; }
  .header h1 { font-size: 24px; color: #c8aa6e; margin-bottom: 6px; }
  .header .subtitle { color: #8b8b8b; font-size: 14px; }
  .stats-bar { display: flex; justify-content: center; gap: 24px; margin-bottom: 16px; flex-wrap: wrap; }
  .stat { text-align: center; padding: 8px 16px; background: #1a1d28; border-radius: 8px; min-width: 80px; }
  .stat .num { font-size: 22px; font-weight: bold; }
  .stat .label { font-size: 11px; color: #8b8b8b; margin-top: 2px; }
  .num-total { color: #c8aa6e; } .num-approved { color: #4caf50; } .num-skipped { color: #f44336; } .num-remaining { color: #ff9800; }
  .progress-wrap { max-width: 700px; margin: 0 auto 20px; background: #1a1d28; border-radius: 10px; height: 8px; overflow: hidden; }
  .progress-bar { height: 100%; background: linear-gradient(90deg, #4caf50, #c8aa6e); transition: width 0.3s ease; border-radius: 10px; }
  .filter-bar { display: flex; justify-content: center; gap: 8px; margin-bottom: 20px; flex-wrap: wrap; }
  .filter-btn { padding: 6px 16px; border: 1px solid #333; background: #1a1d28; color: #aaa; border-radius: 20px; cursor: pointer; font-size: 13px; transition: all 0.2s; }
  .filter-btn:hover { border-color: #c8aa6e; color: #c8aa6e; }
  .filter-btn.active { background: #c8aa6e; color: #0f1117; border-color: #c8aa6e; font-weight: 600; }
  .card-container { max-width: 700px; margin: 0 auto; }
  .card { background: #1a1d28; border: 1px solid #2a2d38; border-radius: 12px; padding: 24px; position: relative; transition: border-color 0.2s; }
  .card:hover { border-color: #3a3d48; }
  .tier-badge { display: inline-block; padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: 600; margin-bottom: 8px; }
  .tier-silver { background: #9e9e9e30; color: #bdbdbd; border: 1px solid #9e9e9e50; }
  .tier-gold { background: #ffc10730; color: #ffc107; border: 1px solid #ffc10750; }
  .tier-prismatic { background: #e040fb30; color: #e040fb; border: 1px solid #e040fb50; }
  .src-badge { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 10px; margin-left: 8px; }
  .src-blitz { background: #ff6b3520; color: #ff6b35; border: 1px solid #ff6b3540; }
  .src-wiki { background: #4a90d920; color: #4a90d9; border: 1px solid #4a90d940; }
  .name-zh { font-size: 22px; font-weight: bold; color: #fff; margin-bottom: 4px; }
  .name-en { font-size: 14px; color: #8b8b8b; margin-bottom: 16px; }
  .effect-section { background: #12141c; border-radius: 8px; padding: 14px; margin-bottom: 12px; }
  .effect-label { font-size: 11px; color: #666; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; }
  .effect-text { font-size: 13px; line-height: 1.6; color: #ccc; }
  .effect-zh { color: #e8d5a3; }
  .effect-edit { width: 100%; min-height: 60px; background: #0f1117; border: 1px solid #333; border-radius: 6px; color: #e0e0e0; padding: 10px; font-size: 13px; font-family: inherit; resize: vertical; }
  .effect-edit:focus { outline: none; border-color: #c8aa6e; }
  .effect-edit::placeholder { color: #555; }
  .name-edit-row { display: flex; gap: 8px; margin-bottom: 12px; align-items: center; }
  .name-edit { flex: 1; background: #0f1117; border: 1px solid #333; border-radius: 6px; color: #e0e0e0; padding: 6px 10px; font-size: 15px; font-family: inherit; }
  .name-edit:focus { outline: none; border-color: #c8aa6e; }
  .name-edit-label { font-size: 11px; color: #666; white-space: nowrap; }
  .source-link { font-size: 12px; color: #5588cc; text-decoration: none; display: inline-block; margin-bottom: 16px; }
  .source-link:hover { color: #77aaee; text-decoration: underline; }
  .actions { display: flex; gap: 10px; justify-content: center; margin-top: 8px; }
  .btn { padding: 10px 28px; border: none; border-radius: 8px; font-size: 14px; font-weight: 600; cursor: pointer; transition: all 0.2s; }
  .btn-approve { background: #4caf50; color: #fff; } .btn-approve:hover { background: #66bb6a; transform: translateY(-1px); }
  .btn-skip { background: #333; color: #aaa; } .btn-skip:hover { background: #444; color: #ddd; transform: translateY(-1px); }
  .btn-undo { background: transparent; border: 1px solid #555; color: #888; padding: 10px 16px; }
  .btn-undo:hover { border-color: #ff9800; color: #ff9800; }
  .btn-batch { background: #2196f3; color: #fff; padding: 8px 20px; font-size: 13px; }
  .btn-batch:hover { background: #42a5f5; }
  .key-hint { text-align: center; margin-top: 14px; font-size: 12px; color: #555; }
  .key-hint kbd { display: inline-block; padding: 2px 6px; background: #222; border: 1px solid #444; border-radius: 3px; font-family: monospace; font-size: 11px; color: #888; }
  .empty-state { text-align: center; padding: 60px 20px; color: #666; }
  .empty-state .icon { font-size: 48px; margin-bottom: 16px; }
  .empty-state h2 { color: #c8aa6e; margin-bottom: 8px; }
  .export-section { max-width: 700px; margin: 30px auto 0; text-align: center; }
  .btn-export { padding: 12px 36px; background: #c8aa6e; color: #0f1117; border: none; border-radius: 8px; font-size: 15px; font-weight: 700; cursor: pointer; }
  .btn-export:hover { background: #d4bb82; } .btn-export:disabled { background: #444; color: #666; cursor: not-allowed; }
  .export-note { font-size: 12px; color: #666; margin-top: 8px; }
  .summary { max-width: 700px; margin: 20px auto; background: #1a1d28; border-radius: 12px; padding: 24px; }
  .summary h2 { color: #c8aa6e; font-size: 18px; margin-bottom: 16px; text-align: center; }
  .summary-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #2a2d38; font-size: 14px; }
  .summary-row:last-child { border-bottom: none; }
  .nav-row { display: flex; justify-content: center; gap: 10px; margin-top: 12px; }
  .btn-nav { padding: 6px 14px; background: #222; border: 1px solid #333; color: #888; border-radius: 6px; font-size: 12px; cursor: pointer; }
  .btn-nav:hover { border-color: #c8aa6e; color: #c8aa6e; } .btn-nav:disabled { opacity: 0.3; cursor: not-allowed; }
  .history-section { max-width: 700px; margin: 20px auto 0; }
  .history-toggle { width: 100%; padding: 10px; background: #1a1d28; border: 1px solid #2a2d38; border-radius: 8px; color: #8b8b8b; cursor: pointer; font-size: 13px; text-align: center; }
  .history-toggle:hover { border-color: #c8aa6e; color: #c8aa6e; }
  .history-list { display: none; margin-top: 8px; background: #1a1d28; border-radius: 8px; padding: 12px; max-height: 300px; overflow-y: auto; }
  .history-list.open { display: block; }
  .history-item { display: flex; justify-content: space-between; align-items: center; padding: 6px 8px; border-bottom: 1px solid #2a2d38; font-size: 13px; }
  .history-item:last-child { border-bottom: none; }
  .batch-bar { display: flex; justify-content: center; gap: 8px; margin-bottom: 16px; flex-wrap: wrap; }
  .no-effect-warn { background: #ff980020; border: 1px solid #ff980040; border-radius: 6px; padding: 8px 12px; margin-bottom: 12px; font-size: 12px; color: #ff9800; }
</style>
</head>
<body>
<div class="header">
  <h1>增强导入审核工具</h1>
  <div class="subtitle" id="subtitle"></div>
</div>
<div class="stats-bar">
  <div class="stat"><div class="num num-total" id="stat-total">0</div><div class="label">总计</div></div>
  <div class="stat"><div class="num num-approved" id="stat-approved">0</div><div class="label">已通过</div></div>
  <div class="stat"><div class="num num-skipped" id="stat-skipped">0</div><div class="label">已跳过</div></div>
  <div class="stat"><div class="num num-remaining" id="stat-remaining">0</div><div class="label">待审核</div></div>
</div>
<div class="progress-wrap"><div class="progress-bar" id="progress-bar" style="width:0%"></div></div>
<div class="filter-bar">
  <button class="filter-btn active" data-filter="all">全部</button>
  <button class="filter-btn" data-filter="silver">银色 Silver</button>
  <button class="filter-btn" data-filter="gold">金色 Gold</button>
  <button class="filter-btn" data-filter="prismatic">棱彩 Prismatic</button>
  <button class="filter-btn" data-filter="has_zh">有中文描述</button>
  <button class="filter-btn" data-filter="no_zh">无中文描述</button>
</div>
<div class="batch-bar">
  <button class="btn btn-batch" onclick="batchApproveHasZh()">全部通过「有中文描述」的</button>
</div>
<div class="card-container" id="card-container"></div>
<div class="export-section">
  <button class="btn-export" id="btn-export" disabled>导出已批准的增强 (JSON)</button>
  <div class="export-note">导出后可用于导入 data/augments.json</div>
</div>
<div class="history-section">
  <button class="history-toggle" id="history-toggle">查看审核历史</button>
  <div class="history-list" id="history-list"></div>
</div>
<script>
const C = ''' + data_json + ''';
let currentIndex = 0, currentFilter = 'all', decisions = {}, history = [];

function getFiltered() {
  if (currentFilter === 'all') return C;
  if (currentFilter === 'has_zh') return C.filter(c => c.effect);
  if (currentFilter === 'no_zh') return C.filter(c => !c.effect);
  return C.filter(c => c.tier === currentFilter);
}
function getStats() {
  const a = Object.values(decisions).filter(d=>d.approved).length;
  const s = Object.values(decisions).filter(d=>!d.approved).length;
  return { total: C.length, approved: a, skipped: s, remaining: C.length-a-s };
}
function updateStats() {
  const s = getStats();
  document.getElementById('stat-total').textContent = s.total;
  document.getElementById('stat-approved').textContent = s.approved;
  document.getElementById('stat-skipped').textContent = s.skipped;
  document.getElementById('stat-remaining').textContent = s.remaining;
  document.getElementById('progress-bar').style.width = ((s.approved+s.skipped)/s.total*100)+'%';
  document.getElementById('btn-export').disabled = s.approved === 0;
}
function tierLabel(t) { return {silver:'银色 Silver',gold:'金色 Gold',prismatic:'棱彩 Prismatic'}[t]||t; }
function srcBadge(s) { return s==='blitz_gg'?'<span class="src-badge src-blitz">blitz.gg</span>':'<span class="src-badge src-wiki">wiki</span>'; }
function esc(s) { return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }

function renderCard() {
  const container = document.getElementById('card-container');
  const filtered = getFiltered();
  if (currentIndex >= filtered.length) currentIndex = Math.max(0, filtered.length-1);
  const undecided = filtered.filter(c=>!(c.id in decisions));
  if (undecided.length === 0) {
    const allUndecided = C.filter(c=>!(c.id in decisions));
    if (allUndecided.length === 0) { renderComplete(); return; }
    currentFilter = 'all';
    document.querySelectorAll('.filter-btn').forEach(b=>b.classList.toggle('active',b.dataset.filter==='all'));
    currentIndex = C.findIndex(c=>!(c.id in decisions));
    if (currentIndex < 0) { renderComplete(); return; }
  }
  let c = filtered[currentIndex];
  if (!c) { renderComplete(); return; }
  if (c.id in decisions) {
    let next = filtered.findIndex((x,i)=>i>currentIndex&&!(x.id in decisions));
    if (next<0) next = filtered.findIndex((x,i)=>i<currentIndex&&!(x.id in decisions));
    if (next>=0) { currentIndex=next; renderCard(); return; }
    renderComplete(); return;
  }

  const hasZhEffect = !!c.effect;
  const hasEnEffect = !!c.effect_en;

  let effectHtml = '';
  if (hasZhEffect) {
    effectHtml += '<div class="effect-section"><div class="effect-label">中文效果描述 (来自 blitz.gg)</div><div class="effect-text effect-zh">'+esc(c.effect)+'</div></div>';
  }
  if (hasEnEffect) {
    effectHtml += '<div class="effect-section"><div class="effect-label">英文效果描述</div><div class="effect-text">'+esc(c.effect_en)+'</div></div>';
  }
  if (!hasZhEffect && !hasEnEffect) {
    effectHtml += '<div class="no-effect-warn">此增强暂无效果描述，建议在 arammayhem.com 上确认后再决定。</div>';
  }

  container.innerHTML = '<div class="card">'+
    '<span class="tier-badge tier-'+c.tier+'">'+tierLabel(c.tier)+'</span>'+srcBadge(c.src)+
    '<div class="name-zh">'+esc(c.name)+'</div>'+
    '<div class="name-en">'+esc(c.name_en)+'</div>'+
    '<div class="name-edit-row"><span class="name-edit-label">中文名修改:</span><input class="name-edit" id="name-edit" value="'+esc(c.name)+'" /></div>'+
    effectHtml+
    '<div class="effect-section"><div class="effect-label">中文效果描述 '+(hasZhEffect?'(可修改)':'(可选填)')+'</div>'+
    '<textarea class="effect-edit" id="effect-edit" placeholder="输入或修改中文效果描述...">'+esc(c.effect||'')+'</textarea></div>'+
    '<a class="source-link" href="https://arammayhem.com/zh-cn/augments/'+c.id.replace(/_/g,'-')+'" target="_blank">在 arammayhem.com 查看 &rarr;</a> '+
    '<a class="source-link" href="https://blitz.gg/zh-CN/lol/aram-mayhem-augments" target="_blank">在 blitz.gg 查看 &rarr;</a>'+
    '<div class="actions">'+
    '<button class="btn btn-approve" onclick="approve()">通过 (A)</button>'+
    '<button class="btn btn-skip" onclick="skip()">跳过 (S)</button>'+
    (history.length>0?'<button class="btn btn-undo" onclick="undoLast()">撤销 (Z)</button>':'')+
    '</div>'+
    '<div class="key-hint"><kbd>A</kbd> 通过 &nbsp; <kbd>S</kbd> 跳过 &nbsp; <kbd>Z</kbd> 撤销 &nbsp; <kbd>&larr;</kbd><kbd>&rarr;</kbd> 翻页</div>'+
    '<div class="nav-row">'+
    '<button class="btn-nav" onclick="navPrev()" '+(currentIndex<=0?'disabled':'')+'>← 上一条</button>'+
    '<span style="color:#555;font-size:12px;line-height:30px;">'+undecided.length+' 条待审核</span>'+
    '<button class="btn-nav" onclick="navNext()" '+(currentIndex>=filtered.length-1?'disabled':'')+'>下一条 →</button>'+
    '</div></div>';
}

function renderComplete() {
  const s = getStats();
  const ct = (t) => C.filter(c=>c.tier===t&&decisions[c.id]?.approved).length;
  document.getElementById('card-container').innerHTML =
    '<div class="empty-state"><div class="icon">&#10003;</div><h2>审核完成!</h2>'+
    '<p>已通过 '+s.approved+' 个，跳过 '+s.skipped+' 个。</p></div>'+
    '<div class="summary"><h2>审核摘要</h2>'+
    '<div class="summary-row"><span>总候选数</span><span>'+s.total+'</span></div>'+
    '<div class="summary-row"><span>已通过</span><span style="color:#4caf50">'+s.approved+'</span></div>'+
    '<div class="summary-row"><span>已跳过</span><span style="color:#f44336">'+s.skipped+'</span></div>'+
    '<div class="summary-row"><span>银色通过</span><span>'+ct('silver')+'</span></div>'+
    '<div class="summary-row"><span>金色通过</span><span>'+ct('gold')+'</span></div>'+
    '<div class="summary-row"><span>棱彩通过</span><span>'+ct('prismatic')+'</span></div></div>';
}

function approve() {
  const c = getFiltered()[currentIndex];
  if (!c || c.id in decisions) return;
  const n = document.getElementById('name-edit'), e = document.getElementById('effect-edit');
  decisions[c.id] = { approved:true, nameEdited: n&&n.value.trim()!==c.name?n.value.trim():null, effectEdited: e?e.value.trim():null };
  history.push({id:c.id, name:n?.value.trim()||c.name, action:'approved'});
  updateStats(); advanceToNext(); updateHistory();
}
function skip() {
  const c = getFiltered()[currentIndex];
  if (!c || c.id in decisions) return;
  decisions[c.id] = { approved:false };
  history.push({id:c.id, name:c.name, action:'skipped'});
  updateStats(); advanceToNext(); updateHistory();
}
function undoLast() {
  if (!history.length) return;
  const last = history.pop();
  delete decisions[last.id];
  const f = getFiltered(), idx = f.findIndex(x=>x.id===last.id);
  if (idx>=0) currentIndex=idx;
  updateStats(); renderCard(); updateHistory();
}
function batchApproveHasZh() {
  if (!confirm('确认批量通过所有「有中文效果描述」的候选？\\n你仍可以之后在历史中逐条撤销。')) return;
  let count = 0;
  C.forEach(c => {
    if (c.effect && !(c.id in decisions)) {
      decisions[c.id] = { approved:true, nameEdited:null, effectEdited:c.effect };
      history.push({id:c.id, name:c.name, action:'approved'});
      count++;
    }
  });
  updateStats();
  const f = getFiltered();
  const next = f.findIndex(c=>!(c.id in decisions));
  if (next>=0) currentIndex=next;
  renderCard(); updateHistory();
  alert('已批量通过 '+count+' 个候选。');
}
function advanceToNext() {
  const f = getFiltered();
  let n = f.findIndex((c,i)=>i>currentIndex&&!(c.id in decisions));
  if (n<0) n = f.findIndex((c,i)=>i<currentIndex&&!(c.id in decisions));
  if (n>=0) currentIndex=n;
  renderCard();
}
function navPrev() { const f=getFiltered(); for(let i=currentIndex-1;i>=0;i--) if(!(f[i].id in decisions)){currentIndex=i;renderCard();return;} }
function navNext() { const f=getFiltered(); for(let i=currentIndex+1;i<f.length;i++) if(!(f[i].id in decisions)){currentIndex=i;renderCard();return;} }
function exportApproved() {
  const approved = C.filter(c=>decisions[c.id]?.approved).map(c => {
    const d = decisions[c.id];
    return { id:c.id, name:d.nameEdited||c.name, name_en:c.name_en, tier:c.tier, status:"active",
      effect:d.effectEdited||c.effect||"", effect_en:c.effect_en||"", source_status:"import_candidate",
      source:{type:c.src||"arammayhem_wiki", url:"https://arammayhem.com/zh-cn/augments/"+c.id.replace(/_/g,"-")} };
  });
  const blob = new Blob([JSON.stringify(approved,null,2)],{type:'application/json'});
  const a = document.createElement('a'); a.href=URL.createObjectURL(blob); a.download='approved_augments.json'; a.click();
}
function updateHistory() {
  const el = document.getElementById('history-list');
  if (!history.length) { el.innerHTML='<div style="color:#555;text-align:center;padding:12px;">暂无记录</div>'; return; }
  el.innerHTML = history.slice().reverse().map(h=>
    '<div class="history-item"><span>'+esc(h.name)+'</span><span style="color:'+(h.action==='approved'?'#4caf50':'#f44336')+'">'+(h.action==='approved'?'通过':'跳过')+'</span></div>'
  ).join('');
}

document.getElementById('subtitle').textContent = '审核 '+C.length+' 个增强候选 ('+C.filter(c=>c.effect).length+' 个有中文描述)';
document.querySelectorAll('.filter-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    currentFilter = btn.dataset.filter;
    document.querySelectorAll('.filter-btn').forEach(b=>b.classList.remove('active'));
    btn.classList.add('active');
    const f = getFiltered(), first = f.findIndex(c=>!(c.id in decisions));
    currentIndex = first>=0?first:0;
    renderCard();
  });
});
document.getElementById('btn-export').addEventListener('click', exportApproved);
document.getElementById('history-toggle').addEventListener('click', () => document.getElementById('history-list').classList.toggle('open'));
document.addEventListener('keydown', e => {
  if (e.target.tagName==='INPUT'||e.target.tagName==='TEXTAREA') return;
  if (e.key==='a'||e.key==='A') { e.preventDefault(); approve(); }
  if (e.key==='s'||e.key==='S') { e.preventDefault(); skip(); }
  if (e.key==='z'||e.key==='Z') { e.preventDefault(); undoLast(); }
  if (e.key==='ArrowLeft') { e.preventDefault(); navPrev(); }
  if (e.key==='ArrowRight') { e.preventDefault(); navNext(); }
});
updateStats(); renderCard(); updateHistory();
</script>
</body>
</html>'''

with open(TOOLS_PATH, "w", encoding="utf-8") as f:
    f.write(html)

print(f"[OK] 审核工具已更新: {TOOLS_PATH}")
print(f"     候选数: {len(review_data)}, 有中文描述: {sum(1 for d in review_data if d['has_zh'])}")
