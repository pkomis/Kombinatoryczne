import { useState, useEffect, useRef, useCallback } from "react";

// ─────────────────────────────────────────────────────────────────────────────
// SIMULATION LOGIC
// ─────────────────────────────────────────────────────────────────────────────
function createBamboos(rates) {
  return rates.map((h, i) => ({ id: i, h, height: 0 }));
}
function oracleReduceMax(bamboos) {
  let best = -1, bh = -1;
  bamboos.forEach((b, i) => { if (b.height > bh) { bh = b.height; best = i; } });
  return best;
}
function oracleReduceFastest(x) {
  return function(bamboos) {
    let best = -1, br = -1;
    bamboos.forEach((b, i) => { if (b.height >= x && b.h > br) { br = b.h; best = i; } });
    if (best === -1) return oracleReduceMax(bamboos);
    return best;
  };
}
function oracleOptimal(bamboos) {
  let best = -1, bs = -1;
  bamboos.forEach((b, i) => {
    const s = b.height * b.h * 4;
    if (s > bs) { bs = s; best = i; }
  });
  return best;
}

const PRESETS = [
  { name: "Near-worst case", rates: [0.95, 0.05] },
  { name: "Uniform (4)", rates: [0.25, 0.25, 0.25, 0.25] },
  { name: "Geometric", rates: [0.5, 0.25, 0.125, 0.125] },
  { name: "One dominant", rates: [0.7, 0.1, 0.1, 0.1] },
  { name: "Five stalks", rates: [0.4, 0.2, 0.15, 0.15, 0.1] },
];

const ALGO_META = {
  reduceMax:     { label: "Reduce-Max",          color: "#1a7a3a", bound: "9" },
  reduceFastest: { label: "Reduce-Fastest(x)",   color: "#b45309", bound: "2.62" },
  optimal:       { label: "Makespan-2 oracle",   color: "#1d4ed8", bound: "2" },
};

// ─────────────────────────────────────────────────────────────────────────────
// PANDA SVG (simplified, paper-style)
// ─────────────────────────────────────────────────────────────────────────────
function PandaSVG({ flipped, cutting }) {
  return (
    <svg viewBox="0 0 48 56" width="48" height="56" style={{ display: "block", transform: flipped ? "scaleX(-1)" : "none" }}>
      {/* Body */}
      <ellipse cx="24" cy="38" rx="13" ry="12" fill="#f0f0f0" stroke="#222" strokeWidth="1.2"/>
      {/* Head */}
      <circle cx="24" cy="20" r="11" fill="#f0f0f0" stroke="#222" strokeWidth="1.2"/>
      {/* Ears */}
      <circle cx="14" cy="11" r="5" fill="#222"/>
      <circle cx="34" cy="11" r="5" fill="#222"/>
      {/* Eye patches */}
      <ellipse cx="19" cy="19" rx="4" ry="3.5" fill="#222" transform="rotate(-10,19,19)"/>
      <ellipse cx="29" cy="19" rx="4" ry="3.5" fill="#222" transform="rotate(10,29,19)"/>
      {/* Eyes */}
      <circle cx="19" cy="19" r="1.5" fill="#fff"/>
      <circle cx="29" cy="19" r="1.5" fill="#fff"/>
      {/* Nose */}
      <ellipse cx="24" cy="23.5" rx="2.5" ry="1.5" fill="#444"/>
      {/* Mouth */}
      <path d="M21 25.5 Q24 27.5 27 25.5" fill="none" stroke="#444" strokeWidth="0.8" strokeLinecap="round"/>
      {/* Arms */}
      <ellipse cx="11" cy="38" rx="5" ry="8" fill="#222" stroke="#222" strokeWidth="0.8" transform="rotate(-15,11,38)"/>
      <ellipse cx="37" cy="38" rx="5" ry="8" fill="#222" stroke="#222" strokeWidth="0.8" transform="rotate(15,37,38)"/>
      {/* Legs */}
      <ellipse cx="18" cy="49" rx="5" ry="4" fill="#222"/>
      <ellipse cx="30" cy="49" rx="5" ry="4" fill="#222"/>
      {/* Scissors when cutting */}
      {cutting && (
        <g transform="translate(32,28) rotate(-30)">
          <line x1="0" y1="0" x2="10" y2="0" stroke="#888" strokeWidth="1.5" strokeLinecap="round"/>
          <line x1="0" y1="3" x2="10" y2="3" stroke="#888" strokeWidth="1.5" strokeLinecap="round"/>
          <circle cx="0" cy="1.5" r="2.5" fill="none" stroke="#888" strokeWidth="1"/>
        </g>
      )}
    </svg>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// BAMBOO GARDEN SVG — faithful to paper Fig 1
// ─────────────────────────────────────────────────────────────────────────────
function BambooGarden({
  bamboos, maxDisplayH, lastCut, pandaAt, interactive, onCut, dayFrac = 0
}) {
  const W = 540, H = 280;
  const groundY = 220;
  const leftPad = 56;
  const rightPad = 70; // space for panda
  const usableW = W - leftPad - rightPad;
  const n = bamboos.length;
  const slotW = usableW / n;
  const stalkW = Math.max(14, Math.min(28, slotW * 0.38));
  const maxH = Math.max(maxDisplayH, 1.5, ...bamboos.map(b => b.height));
  const scale = (H - groundY - 20) === 0 ? 1 : (groundY - 30) / maxH;

  function stalkX(i) { return leftPad + slotW * i + slotW / 2; }

  // Smooth heights with fractional day growth
  function displayH(b) {
    return b.height - b.h * (1 - dayFrac);
  }

  // Height-bracket label (left side, like the paper)
  const maxBamboo = bamboos.reduce((a, b) => b.height > a.height ? b : a, bamboos[0]);
  const bracketH = displayH(maxBamboo) * scale;

  // Panda x position (animate to cut target)
  const pandaX = pandaAt !== null ? stalkX(pandaAt) : W - rightPad + 10;

  return (
    <svg
      viewBox={`0 0 ${W} ${H + 30}`}
      style={{ width: "100%", display: "block", cursor: interactive ? "pointer" : "default" }}
      onClick={e => {
        if (!interactive || !onCut) return;
        const rect = e.currentTarget.getBoundingClientRect();
        const px = (e.clientX - rect.left) * (W / rect.width);
        const i = Math.floor((px - leftPad) / slotW);
        if (i >= 0 && i < n) onCut(i);
      }}
    >
      {/* Paper-style background */}
      <rect width={W} height={H + 30} fill="#fafaf7" rx="6"/>

      {/* Height reference bracket on left (like paper h1 bracket) */}
      {bracketH > 10 && (
        <g>
          <line x1="18" y1={groundY - bracketH} x2="18" y2={groundY} stroke="#555" strokeWidth="0.8"/>
          <line x1="14" y1={groundY - bracketH} x2="22" y2={groundY - bracketH} stroke="#555" strokeWidth="0.8"/>
          <line x1="14" y1={groundY} x2="22" y2={groundY} stroke="#555" strokeWidth="0.8"/>
          <text x="10" y={groundY - bracketH / 2 + 4} textAnchor="middle" fontSize="11"
            fontFamily="'CMU Serif', 'Computer Modern', Georgia, serif" fontStyle="italic" fill="#333">
            h
          </text>
          <text x="13" y={groundY - bracketH / 2 + 10} fontSize="7"
            fontFamily="'CMU Serif', 'Computer Modern', Georgia, serif" fill="#333">
            max
          </text>
        </g>
      )}

      {/* Thin horizontal guide lines */}
      {[0.5, 1.0, 1.5, 2.0, 2.5].map(v => {
        const y = groundY - v * scale;
        if (y < 10 || y > groundY) return null;
        return (
          <g key={v}>
            <line x1={leftPad - 4} y1={y} x2={W - rightPad + 4} y2={y}
              stroke="#ccc" strokeWidth="0.5" strokeDasharray="3 4"/>
            <text x={leftPad - 6} y={y + 3.5} textAnchor="end" fontSize="8.5"
              fontFamily="'CMU Serif', 'Computer Modern', Georgia, serif" fill="#aaa">
              {v.toFixed(1)}
            </text>
          </g>
        );
      })}

      {/* Bamboo stalks */}
      {bamboos.map((b, i) => {
        const cx = stalkX(i);
        const dh = Math.max(0, displayH(b));
        const pixH = dh * scale;
        const top = groundY - pixH;
        const isLastCut = lastCut === i;
        const isTarget = pandaAt === i;

        // Color: slightly more yellow-green for tall ones, classic green otherwise
        const green1 = isLastCut ? "#22c55e" : "#2d8a3e";
        const green2 = isLastCut ? "#16a34a" : "#1f6b2e";
        const green3 = isLastCut ? "#bbf7d0" : "#a7d9a0";

        return (
          <g key={i}>
            {/* Glow ring for interactive hover target */}
            {interactive && (
              <rect x={cx - stalkW / 2 - 3} y={top - 3} width={stalkW + 6} height={pixH + 6}
                rx="8" fill="none" stroke={isTarget ? "#f59e0b" : "transparent"} strokeWidth="1.5"
                strokeDasharray="3 2" opacity="0.7"/>
            )}

            {/* Main stalk body */}
            {pixH > 0 && (
              <rect x={cx - stalkW / 2} y={top} width={stalkW} height={pixH}
                rx={stalkW / 2} fill={green1} stroke={green2} strokeWidth="0.8"/>
            )}

            {/* Highlight stripe */}
            {pixH > 4 && (
              <rect x={cx - stalkW / 2 + 3} y={top + 2} width={stalkW * 0.25} height={Math.max(0, pixH - 4)}
                rx={2} fill={green3} opacity="0.5"/>
            )}

            {/* Bamboo joints (horizontal lines) */}
            {pixH > 0 && Array.from({ length: Math.max(1, Math.floor(dh * 3)) }).map((_, j) => {
              const jy = groundY - ((j + 1) / (Math.floor(dh * 3) + 1)) * pixH;
              return (
                <line key={j}
                  x1={cx - stalkW / 2} y1={jy} x2={cx + stalkW / 2} y2={jy}
                  stroke={green2} strokeWidth="1.2" opacity="0.6"/>
              );
            })}

            {/* Round ball on top — key visual from paper */}
            {pixH > 0 && (
              <circle cx={cx} cy={top} r={stalkW / 2 + 1}
                fill={green1} stroke={green2} strokeWidth="0.8"/>
            )}
            {pixH > 0 && (
              <circle cx={cx - stalkW * 0.15} cy={top - stalkW * 0.1} r={stalkW * 0.12}
                fill={green3} opacity="0.6"/>
            )}

            {/* Height label above ball */}
            <text x={cx} y={Math.min(top - stalkW / 2 - 4, groundY - 4)} textAnchor="middle"
              fontSize="9" fontFamily="'CMU Serif', 'Computer Modern', Georgia, serif"
              fill={isLastCut ? "#16a34a" : "#444"} fontWeight={isLastCut ? "bold" : "normal"}>
              {dh.toFixed(2)}
            </text>
          </g>
        );
      })}

      {/* Ground line */}
      <rect x={leftPad - 8} y={groundY} width={W - leftPad - rightPad + 16} height={3} rx="1" fill="#8B6914"/>
      {/* Ground texture */}
      <rect x={leftPad - 8} y={groundY + 3} width={W - leftPad - rightPad + 16} height={8} rx="1" fill="#a07830" opacity="0.4"/>

      {/* b_i labels below ground */}
      {bamboos.map((_, i) => (
        <text key={i} x={stalkX(i)} y={groundY + 18} textAnchor="middle"
          fontSize="11" fontFamily="'CMU Serif', 'Computer Modern', Georgia, serif"
          fontStyle="italic" fill="#333">
          b
          <tspan fontSize="8" baselineShift="-4">{i + 1}</tspan>
        </text>
      ))}

      {/* Panda gardener — positioned at cut target or resting right */}
      <g transform={`translate(${pandaX - 24}, ${groundY - 50})`} style={{ transition: "transform 0.4s ease" }}>
        <PandaSVG flipped={pandaAt !== null && pandaAt < n / 2} cutting={pandaAt !== null}/>
      </g>

      {/* Cut flash effect */}
      {lastCut !== null && (
        <g>
          {[0,1,2,3,4,5].map(k => {
            const angle = (k / 6) * Math.PI * 2;
            const r = stalkW + 6;
            return (
              <line key={k}
                x1={stalkX(lastCut)} y1={groundY - displayH(bamboos[lastCut]) * scale - stalkW / 2}
                x2={stalkX(lastCut) + Math.cos(angle) * r}
                y2={groundY - displayH(bamboos[lastCut]) * scale - stalkW / 2 + Math.sin(angle) * r}
                stroke="#fbbf24" strokeWidth="1" opacity="0.6"/>
            );
          })}
        </g>
      )}

      {/* "interactive click" hint */}
      {interactive && (
        <text x={W / 2} y={H + 22} textAnchor="middle" fontSize="9.5"
          fontFamily="'CMU Serif', 'Computer Modern', Georgia, serif" fill="#999" fontStyle="italic">
          Click a bamboo stalk to trim it
        </text>
      )}
    </svg>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// SPARKLINE
// ─────────────────────────────────────────────────────────────────────────────
function Sparkline({ data, color, height = 52, maxVal = 3 }) {
  if (!data || data.length < 2) return <div style={{ height }} />;
  const W = 400, H = height;
  const max = Math.max(maxVal, ...data);
  const pts = data.map((v, i) => `${(i / (data.length - 1)) * W},${H - (v / max) * (H - 2) - 1}`).join(" ");
  // Bound lines
  const bounds = { "9": "#dc2626", "2.62": "#b45309", "2": "#1d4ed8" };
  return (
    <svg viewBox={`0 0 ${W} ${H}`} style={{ width: "100%", height, display: "block" }}>
      {Object.entries(bounds).map(([v, c]) => {
        const y = H - (parseFloat(v) / max) * (H - 2) - 1;
        if (y < 0 || y > H) return null;
        return <line key={v} x1={0} y1={y} x2={W} y2={y} stroke={c} strokeWidth="0.6" strokeDasharray="3 3" opacity="0.5"/>;
      })}
      <polyline points={pts} fill="none" stroke={color} strokeWidth="1.8" strokeLinejoin="round"/>
      <polyline points={`0,${H} ${pts} ${W},${H}`} fill={color} opacity="0.08" stroke="none"/>
    </svg>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// RATE EDITOR
// ─────────────────────────────────────────────────────────────────────────────
function RateEditor({ rates, onChange }) {
  const [raw, setRaw] = useState(rates.map(r => r.toFixed(3)));
  const sum = raw.reduce((a, r) => a + (parseFloat(r) || 0), 0);
  const valid = Math.abs(sum - 1) < 0.002 && raw.every(r => parseFloat(r) > 0);

  function update(i, v) {
    const next = [...raw]; next[i] = v; setRaw(next);
    const nums = next.map(r => parseFloat(r) || 0);
    if (Math.abs(nums.reduce((a,b)=>a+b,0)-1)<0.002 && nums.every(n=>n>0)) onChange(nums);
  }
  function normalize() {
    const nums = raw.map(r => parseFloat(r)||0);
    const s = nums.reduce((a,b)=>a+b,0);
    if (s>0) { const n = nums.map(v=>v/s); onChange(n); setRaw(n.map(r=>r.toFixed(3))); }
  }
  function add() {
    const n = raw.length+1;
    const nr = Array(n).fill((1/n).toFixed(3));
    setRaw(nr); onChange(Array(n).fill(1/n));
  }
  function remove(i) {
    if (raw.length<=2) return;
    const nr = raw.filter((_,j)=>j!==i);
    setRaw(nr);
    const nums = nr.map(r=>parseFloat(r)||0);
    const s = nums.reduce((a,b)=>a+b,0);
    if (s>0) { const nn=nums.map(v=>v/s); onChange(nn); setRaw(nn.map(r=>r.toFixed(3))); }
  }

  return (
    <div>
      {raw.map((r,i) => (
        <div key={i} style={{ display:"flex", alignItems:"center", gap:6, marginBottom:5 }}>
          <span style={{ fontFamily:"'CMU Serif',Georgia,serif", fontStyle:"italic", fontSize:12, color:"#555", width:20, flexShrink:0 }}>b<sub>{i+1}</sub></span>
          <input value={r} onChange={e=>update(i,e.target.value)}
            style={{ width:64, border:"1px solid #ccc", borderRadius:3, padding:"3px 6px", fontSize:12, fontFamily:"Georgia,serif", background:"#fff" }}/>
          <input type="range" min="0.01" max="0.99" step="0.01" value={parseFloat(r)||0}
            onChange={e=>update(i,parseFloat(e.target.value).toFixed(3))}
            style={{ flex:1, accentColor:"#2d8a3e" }}/>
          {raw.length>2 && <button onClick={()=>remove(i)} style={{ border:"1px solid #ccc", borderRadius:3, background:"#fff", cursor:"pointer", fontSize:11, padding:"2px 7px", color:"#888" }}>×</button>}
        </div>
      ))}
      <div style={{ display:"flex", gap:6, marginTop:8, alignItems:"center" }}>
        <button onClick={add} disabled={raw.length>=8} style={btnStyle("#2d8a3e", false)}>+ stalk</button>
        <button onClick={normalize} style={btnStyle("#555", true)}>normalize</button>
        <span style={{ marginLeft:"auto", fontSize:11, color: valid?"#16a34a":"#dc2626", fontFamily:"Georgia,serif" }}>
          Σ = {sum.toFixed(3)} {valid?"✓":"≠1"}
        </span>
      </div>
    </div>
  );
}

function btnStyle(color, outline) {
  return {
    padding:"4px 12px", borderRadius:3, border:`1px solid ${color}`,
    background: outline ? "#fff" : color, color: outline ? color : "#fff",
    cursor:"pointer", fontSize:11, fontFamily:"Georgia,serif",
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// PANEL WRAPPER (paper card style)
// ─────────────────────────────────────────────────────────────────────────────
function Panel({ title, children, accent }) {
  return (
    <div style={{ background:"#fff", border:"1px solid #d1c9b8", borderRadius:4, marginBottom:14,
      boxShadow:"0 1px 3px rgba(0,0,0,0.07)", overflow:"hidden" }}>
      {title && (
        <div style={{ background: accent || "#f4f0e8", borderBottom:"1px solid #d1c9b8",
          padding:"7px 14px", display:"flex", alignItems:"center", gap:8 }}>
          {accent && <div style={{ width:8, height:8, borderRadius:"50%", background:accent, flexShrink:0 }}/>}
          <span style={{ fontSize:11, fontWeight:700, letterSpacing:"0.06em",
            textTransform:"uppercase", color:"#555", fontFamily:"Georgia,serif" }}>{title}</span>
        </div>
      )}
      <div style={{ padding:"12px 14px" }}>{children}</div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// SANDBOX MODE
// ─────────────────────────────────────────────────────────────────────────────
function SandboxMode() {
  const [rates, setRates] = useState([0.5, 0.3, 0.2]);
  const [algo, setAlgo] = useState("reduceMax");
  const [xParam, setXParam] = useState(1.618);
  const [bamboos, setBamboos] = useState(()=>createBamboos([0.5,0.3,0.2]));
  const [day, setDay] = useState(0);
  const [msHistory, setMsHistory] = useState([]);
  const [lastCut, setLastCut] = useState(null);
  const [pandaAt, setPandaAt] = useState(null);
  const [running, setRunning] = useState(false);
  const [speed, setSpeed] = useState(700);
  const intervalRef = useRef();

  const getOracle = useCallback(()=>{
    if (algo==="reduceMax") return oracleReduceMax;
    if (algo==="reduceFastest") return oracleReduceFastest(xParam);
    return oracleOptimal;
  },[algo,xParam]);

  function reset(r) {
    setBamboos(createBamboos(r||rates));
    setDay(0); setMsHistory([]); setLastCut(null); setPandaAt(null); setRunning(false);
  }

  function tick() {
    setBamboos(prev => {
      const grown = prev.map(b=>({...b, height:b.height+b.h}));
      const cut = getOracle()(grown);
      setLastCut(cut); setPandaAt(cut);
      setMsHistory(h=>[...h.slice(-150), Math.max(...grown.map(b=>b.height))]);
      setDay(d=>d+1);
      return grown.map((b,i)=>i===cut?{...b,height:0}:b);
    });
  }

  useEffect(()=>{
    if (running) { intervalRef.current=setInterval(tick,speed); }
    else clearInterval(intervalRef.current);
    return ()=>clearInterval(intervalRef.current);
  },[running,speed,getOracle]);

  const makespan = msHistory.length ? Math.max(...msHistory) : 0;
  const meta = ALGO_META[algo];

  return (
    <div style={{ display:"flex", gap:16, alignItems:"flex-start" }}>
      {/* Sidebar */}
      <div style={{ width:220, flexShrink:0 }}>
        <Panel title="presets">
          {PRESETS.map(p=>(
            <div key={p.name} onClick={()=>{setRates(p.rates);reset(p.rates);}}
              style={{ padding:"5px 8px", borderRadius:3, marginBottom:3, cursor:"pointer",
                border:"1px solid #ddd", background:"#fafaf7", fontSize:11,
                fontFamily:"Georgia,serif", color:"#444",
                transition:"background 0.1s" }}
              onMouseOver={e=>e.currentTarget.style.background="#f0ece0"}
              onMouseOut={e=>e.currentTarget.style.background="#fafaf7"}>
              {p.name}
            </div>
          ))}
        </Panel>

        <Panel title="growth rates h_i">
          <RateEditor rates={rates} onChange={r=>{setRates(r);reset(r);}}/>
        </Panel>

        <Panel title="algorithm">
          {Object.entries(ALGO_META).map(([k,m])=>(
            <div key={k} onClick={()=>{setAlgo(k);reset();}}
              style={{ padding:"7px 10px", borderRadius:3, marginBottom:5, cursor:"pointer",
                border:`1px solid ${algo===k?m.color:"#ddd"}`,
                background:algo===k?m.color+"18":"#fafaf7" }}>
              <div style={{ fontSize:12, fontWeight:700, color:algo===k?m.color:"#333",
                fontFamily:"Georgia,serif" }}>{m.label}</div>
              <div style={{ fontSize:10, color:"#888", marginTop:1, fontFamily:"Georgia,serif" }}>
                makespan bound ≤ {m.bound}
              </div>
            </div>
          ))}
          {algo==="reduceFastest" && (
            <div style={{ marginTop:8, background:"#fafaf7", border:"1px solid #e5e2d8", borderRadius:3, padding:"8px 10px" }}>
              <div style={{ fontSize:11, color:"#555", marginBottom:5, fontFamily:"Georgia,serif" }}>
                threshold <i>x</i> = {xParam.toFixed(4)}
              </div>
              <input type="range" min="0.5" max="3" step="0.001" value={xParam}
                onChange={e=>setXParam(parseFloat(e.target.value))}
                style={{ width:"100%", accentColor:meta.color }}/>
              <div style={{ display:"flex", justifyContent:"space-between", fontSize:9, color:"#aaa", marginTop:2, fontFamily:"Georgia,serif" }}>
                <span>0.5</span>
                <span style={{ color:meta.color }}>1+1/√5 ≈ 1.447</span>
                <span>3.0</span>
              </div>
            </div>
          )}
        </Panel>
      </div>

      {/* Main */}
      <div style={{ flex:1, minWidth:0 }}>
        <Panel title={`Day ${day} — ${meta.label}`} accent={meta.color}>
          <BambooGarden bamboos={bamboos} maxDisplayH={Math.max(makespan,2)}
            lastCut={lastCut} pandaAt={pandaAt}/>
          <div style={{ display:"flex", gap:8, marginTop:10, alignItems:"center", justifyContent:"center", flexWrap:"wrap" }}>
            <button onClick={()=>setRunning(r=>!r)} style={btnStyle(running?"#dc2626":"#2d8a3e", false)}>
              {running?"⏸ Pause":"▶ Run"}
            </button>
            <button onClick={tick} disabled={running} style={btnStyle("#555",true)}>+1 day</button>
            <button onClick={()=>reset()} style={btnStyle("#888",true)}>Reset</button>
            <span style={{ marginLeft:8, fontSize:11, color:"#888", fontFamily:"Georgia,serif" }}>
              speed:
            </span>
            <input type="range" min="80" max="1200" step="40" value={1280-speed}
              onChange={e=>setSpeed(1280-parseInt(e.target.value))}
              style={{ width:100, accentColor:"#2d8a3e" }}/>
          </div>
        </Panel>

        {/* Stats row */}
        <div style={{ display:"grid", gridTemplateColumns:"repeat(4,1fr)", gap:10, marginBottom:14 }}>
          {[
            { label:"Makespan M", value:makespan.toFixed(3), color:makespan>2?"#dc2626":makespan>1.5?"#b45309":"#16a34a" },
            { label:"Day d", value:day, color:"#1d4ed8" },
            { label:"Stalks n", value:bamboos.length, color:"#555" },
            { label:"Max h_i", value:Math.max(...rates).toFixed(3), color:"#b45309" },
          ].map(({label,value,color})=>(
            <div key={label} style={{ background:"#fff", border:"1px solid #d1c9b8", borderRadius:4,
              padding:"10px 12px", boxShadow:"0 1px 2px rgba(0,0,0,0.05)" }}>
              <div style={{ fontSize:9, color:"#999", letterSpacing:"0.08em", textTransform:"uppercase",
                marginBottom:4, fontFamily:"Georgia,serif" }}>{label}</div>
              <div style={{ fontSize:20, fontWeight:700, color, fontFamily:"'CMU Serif',Georgia,serif", letterSpacing:"-0.02em" }}>
                {value}
              </div>
            </div>
          ))}
        </div>

        <Panel title="Makespan M over time" accent={meta.color}>
          <Sparkline data={msHistory} color={meta.color} height={60}/>
          <div style={{ display:"flex", justifyContent:"space-between", fontSize:9, color:"#aaa",
            marginTop:4, fontFamily:"Georgia,serif" }}>
            <span>← {Math.max(0,day-150)} days ago</span>
            <span>Dashed lines: bounds (red=9, orange=2.62, blue=2)</span>
            <span>now →</span>
          </div>
        </Panel>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// COMPARE MODE
// ─────────────────────────────────────────────────────────────────────────────
function CompareMode() {
  const [rates, setRates] = useState([0.5,0.25,0.15,0.1]);
  const initStates = (r) => ({
    reduceMax:     {bamboos:createBamboos(r),history:[],lastCut:null,pandaAt:null},
    reduceFastest: {bamboos:createBamboos(r),history:[],lastCut:null,pandaAt:null},
    optimal:       {bamboos:createBamboos(r),history:[],lastCut:null,pandaAt:null},
  });
  const [states, setStates] = useState(()=>initStates([0.5,0.25,0.15,0.1]));
  const [day, setDay] = useState(0);
  const [running, setRunning] = useState(false);
  const [speed, setSpeed] = useState(500);
  const intervalRef = useRef();

  const oracles = {
    reduceMax: oracleReduceMax,
    reduceFastest: oracleReduceFastest(1+1/Math.sqrt(5)),
    optimal: oracleOptimal,
  };

  function reset(r) {
    const nr = r||rates;
    setStates(initStates(nr)); setDay(0); setRunning(false);
  }

  function tick() {
    setStates(prev=>{
      const next={};
      Object.entries(prev).forEach(([k,st])=>{
        const grown=st.bamboos.map(b=>({...b,height:b.height+b.h}));
        const cut=oracles[k](grown);
        next[k]={
          bamboos:grown.map((b,i)=>i===cut?{...b,height:0}:b),
          history:[...st.history.slice(-150), Math.max(...grown.map(b=>b.height))],
          lastCut:cut, pandaAt:cut,
        };
      });
      return next;
    });
    setDay(d=>d+1);
  }

  useEffect(()=>{
    if (running) intervalRef.current=setInterval(tick,speed);
    else clearInterval(intervalRef.current);
    return ()=>clearInterval(intervalRef.current);
  },[running,speed]);

  const keys = ["reduceMax","reduceFastest","optimal"];
  const makespans = keys.map(k=>({k, ms:states[k].history.length?Math.max(...states[k].history):0}));
  const sorted = [...makespans].sort((a,b)=>a.ms-b.ms);

  return (
    <div style={{ display:"flex", gap:16, alignItems:"flex-start" }}>
      <div style={{ width:220, flexShrink:0 }}>
        <Panel title="shared garden">
          <RateEditor rates={rates} onChange={r=>{setRates(r);reset(r);}}/>
        </Panel>
        <Panel title="presets">
          {PRESETS.map(p=>(
            <div key={p.name} onClick={()=>{setRates(p.rates);reset(p.rates);}}
              style={{ padding:"5px 8px", borderRadius:3, marginBottom:3, cursor:"pointer",
                border:"1px solid #ddd", background:"#fafaf7", fontSize:11, fontFamily:"Georgia,serif", color:"#444" }}
              onMouseOver={e=>e.currentTarget.style.background="#f0ece0"}
              onMouseOut={e=>e.currentTarget.style.background="#fafaf7"}>
              {p.name}
            </div>
          ))}
        </Panel>

        {/* Leaderboard */}
        <Panel title="leaderboard" accent={day>0?ALGO_META[sorted[0].k].color:undefined}>
          {sorted.map(({k,ms},rank)=>{
            const m=ALGO_META[k];
            return (
              <div key={k} style={{ display:"flex", justifyContent:"space-between", alignItems:"center",
                padding:"6px 8px", borderRadius:3, marginBottom:4,
                background:rank===0&&day>0?m.color+"12":"#fafaf7", border:"1px solid #e5e2d8" }}>
                <div>
                  <div style={{ fontSize:11, fontWeight:700, color:rank===0&&day>0?m.color:"#333", fontFamily:"Georgia,serif" }}>
                    {rank===0&&day>0?"★ ":""}{m.label}
                  </div>
                  <div style={{ fontSize:9, color:"#999", fontFamily:"Georgia,serif" }}>bound ≤ {m.bound}</div>
                </div>
                <div style={{ fontSize:16, fontWeight:700, color:m.color, fontFamily:"'CMU Serif',Georgia,serif" }}>
                  {ms.toFixed(2)}
                </div>
              </div>
            );
          })}
        </Panel>
      </div>

      <div style={{ flex:1, minWidth:0 }}>
        <div style={{ display:"flex", gap:8, alignItems:"center", marginBottom:12, flexWrap:"wrap" }}>
          <button onClick={()=>setRunning(r=>!r)} style={btnStyle(running?"#dc2626":"#2d8a3e",false)}>
            {running?"⏸ Pause":"▶ Run all"}
          </button>
          <button onClick={tick} disabled={running} style={btnStyle("#555",true)}>+1 day</button>
          <button onClick={()=>reset()} style={btnStyle("#888",true)}>Reset</button>
          <span style={{ fontSize:11, color:"#888", fontFamily:"Georgia,serif", marginLeft:4 }}>
            Day {day}
          </span>
          <span style={{ marginLeft:"auto", fontSize:11, color:"#888", fontFamily:"Georgia,serif" }}>speed:</span>
          <input type="range" min="80" max="1000" step="40" value={1080-speed}
            onChange={e=>setSpeed(1080-parseInt(e.target.value))}
            style={{ width:90, accentColor:"#2d8a3e" }}/>
        </div>

        {keys.map(k=>{
          const m=ALGO_META[k];
          const st=states[k];
          const ms=st.history.length?Math.max(...st.history):0;
          const rank=sorted.findIndex(x=>x.k===k);
          return (
            <div key={k} style={{ background:"#fff", border:`1px solid ${rank===0&&day>0?m.color:"#d1c9b8"}`,
              borderRadius:4, marginBottom:12, boxShadow:"0 1px 3px rgba(0,0,0,0.07)", overflow:"hidden" }}>
              <div style={{ background:m.color+"14", borderBottom:"1px solid #e5e2d8",
                padding:"7px 14px", display:"flex", alignItems:"center", justifyContent:"space-between" }}>
                <div style={{ display:"flex", alignItems:"center", gap:8 }}>
                  <div style={{ width:10, height:10, borderRadius:"50%", background:m.color }}/>
                  <span style={{ fontSize:12, fontWeight:700, color:m.color, fontFamily:"Georgia,serif" }}>
                    {m.label}
                  </span>
                  <span style={{ fontSize:10, color:"#999", fontFamily:"Georgia,serif" }}>
                    bound ≤ {m.bound}
                  </span>
                </div>
                <div style={{ display:"flex", alignItems:"center", gap:16 }}>
                  {rank===0&&day>0&&<span style={{ fontSize:10, background:m.color, color:"#fff", borderRadius:3, padding:"2px 7px", fontFamily:"Georgia,serif" }}>LEADING</span>}
                  <span style={{ fontSize:16, fontWeight:700, color:ms>2?"#dc2626":ms>1.5?"#b45309":"#16a34a", fontFamily:"'CMU Serif',Georgia,serif" }}>
                    M = {ms.toFixed(3)}
                  </span>
                </div>
              </div>
              <div style={{ padding:"10px 14px", display:"grid", gridTemplateColumns:"1fr 140px", gap:12 }}>
                <BambooGarden bamboos={st.bamboos} maxDisplayH={Math.max(ms,2)}
                  lastCut={st.lastCut} pandaAt={st.pandaAt}/>
                <div>
                  <div style={{ fontSize:9, color:"#aaa", letterSpacing:"0.08em", textTransform:"uppercase",
                    marginBottom:4, fontFamily:"Georgia,serif" }}>makespan history</div>
                  <Sparkline data={st.history} color={m.color} height={110} maxVal={3}/>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// GAME MODE
// ─────────────────────────────────────────────────────────────────────────────
function GameMode() {
  const RATES = [0.45, 0.25, 0.2, 0.1];
  const LIMIT = 3.2;
  const [playerB, setPlayerB] = useState(()=>createBamboos(RATES));
  const [botB, setBotB] = useState(()=>createBamboos(RATES));
  const [day, setDay] = useState(0);
  const [pMS, setPMS] = useState(0);
  const [bMS, setBMS] = useState(0);
  const [pHist, setPHist] = useState([]);
  const [bHist, setBHist] = useState([]);
  const [lastCut, setLastCut] = useState(null);
  const [botLastCut, setBotLastCut] = useState(null);
  const [pandaAt, setPandaAt] = useState(null);
  const [phase, setPhase] = useState("idle");
  const [cutDone, setCutDone] = useState(false);
  const [msg, setMsg] = useState("");
  const [endReason, setEndReason] = useState("");

  function start() {
    setPlayerB(createBamboos(RATES)); setBotB(createBamboos(RATES));
    setDay(0); setPMS(0); setBMS(0); setPHist([]); setBHist([]);
    setLastCut(null); setBotLastCut(null); setPandaAt(null);
    setPhase("playing"); setCutDone(false);
    setMsg("Your turn — click a bamboo stalk to trim it.");
    setEndReason("");
  }

  function playerCut(i) {
    if (phase!=="playing"||cutDone) return;
    setCutDone(true);
    setPlayerB(prev=>prev.map((b,j)=>j===i?{...b,height:0}:b));
    setLastCut(i); setPandaAt(i);
    setMsg("Good cut! Now end the day to advance.");
  }

  function endDay() {
    if (phase!=="playing") return;
    // Grow
    let over = false, reason = "";
    setPlayerB(prev=>{
      const g=prev.map(b=>({...b,height:b.height+b.h}));
      const mh=Math.max(...g.map(b=>b.height));
      setPMS(m=>Math.max(m,mh)); setPHist(h=>[...h,mh]);
      if (mh>=LIMIT) { over=true; reason=`Your bamboo b reached ${mh.toFixed(2)} ≥ ${LIMIT}!`; }
      return g;
    });
    setBotB(prev=>{
      const g=prev.map(b=>({...b,height:b.height+b.h}));
      const cut=oracleReduceMax(g);
      setBotLastCut(cut);
      const mh=Math.max(...g.map(b=>b.height));
      setBMS(m=>Math.max(m,mh)); setBHist(h=>[...h,mh]);
      return g.map((b,i)=>i===cut?{...b,height:0}:b);
    });
    setDay(d=>d+1); setCutDone(false); setPandaAt(null); setLastCut(null);
    if (over) { setPhase("over"); setEndReason(reason); setMsg(reason); }
    else setMsg(cutDone?"End of day. Your turn next." : "You skipped — bamboos grew. Your turn.");
  }

  const winner = pMS <= bMS ? "You win! 🎉" : "Bot wins.";

  return (
    <div>
      {phase==="idle" && (
        <div style={{ textAlign:"center", padding:"50px 20px" }}>
          <div style={{ fontSize:24, fontWeight:700, color:"#1f6b2e", marginBottom:12,
            fontFamily:"'CMU Serif',Georgia,serif" }}>
            Bamboo Gardener Challenge
          </div>
          <div style={{ color:"#666", fontSize:13, maxWidth:480, margin:"0 auto 20px", lineHeight:1.8,
            fontFamily:"Georgia,serif" }}>
            You control the <b>left garden</b>. Your opponent, Reduce-Max, controls the right.
            Keep your makespan lower. Any bamboo exceeding height {LIMIT} loses you the game.
            You get <b>one cut per day</b> — choose wisely!
          </div>
          <button onClick={start} style={{ ...btnStyle("#2d8a3e",false), fontSize:14, padding:"10px 28px" }}>
            Start Game
          </button>
        </div>
      )}

      {phase!=="idle" && (
        <div>
          {/* Score row */}
          <div style={{ display:"grid", gridTemplateColumns:"1fr 100px 1fr", gap:10, marginBottom:12 }}>
            <div style={{ background:"#fff", border:`2px solid ${pMS<=bMS&&day>0?"#ec4899":"#d1c9b8"}`,
              borderRadius:4, padding:"10px 14px" }}>
              <div style={{ fontSize:9, color:"#aaa", textTransform:"uppercase", letterSpacing:"0.08em", marginBottom:4, fontFamily:"Georgia,serif" }}>you</div>
              <div style={{ fontSize:24, fontWeight:700, color:"#db2777", fontFamily:"'CMU Serif',Georgia,serif" }}>{pMS.toFixed(3)}</div>
            </div>
            <div style={{ textAlign:"center", display:"flex", flexDirection:"column", justifyContent:"center" }}>
              <div style={{ fontSize:9, color:"#aaa", textTransform:"uppercase", letterSpacing:"0.08em", fontFamily:"Georgia,serif" }}>day</div>
              <div style={{ fontSize:22, fontWeight:700, color:"#333", fontFamily:"'CMU Serif',Georgia,serif" }}>{day}</div>
            </div>
            <div style={{ background:"#fff", border:`2px solid ${bMS<pMS&&day>0?"#1d4ed8":"#d1c9b8"}`,
              borderRadius:4, padding:"10px 14px" }}>
              <div style={{ fontSize:9, color:"#aaa", textTransform:"uppercase", letterSpacing:"0.08em", marginBottom:4, fontFamily:"Georgia,serif" }}>reduce-max bot</div>
              <div style={{ fontSize:24, fontWeight:700, color:"#1d4ed8", fontFamily:"'CMU Serif',Georgia,serif" }}>{bMS.toFixed(3)}</div>
            </div>
          </div>

          {/* Message */}
          <div style={{ background: phase==="over"?"#fef2f2":"#f0fdf4", border:`1px solid ${phase==="over"?"#fca5a5":"#86efac"}`,
            borderRadius:4, padding:"9px 14px", marginBottom:12, textAlign:"center",
            fontFamily:"Georgia,serif", fontSize:13, color: phase==="over"?"#dc2626":"#16a34a" }}>
            {msg}
            {phase==="over" && <span style={{ fontWeight:700, marginLeft:10, color:"#b45309", fontSize:14 }}>{winner}</span>}
          </div>

          {/* Gardens */}
          <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:14, marginBottom:12 }}>
            <Panel title="Your garden — click to trim" accent="#db2777">
              <BambooGarden bamboos={playerB} maxDisplayH={LIMIT} lastCut={lastCut}
                pandaAt={pandaAt} interactive={phase==="playing"&&!cutDone} onCut={playerCut}/>
              {phase==="playing" && (
                <div style={{ textAlign:"center", marginTop:6, fontSize:11, color:cutDone?"#16a34a":"#b45309", fontFamily:"Georgia,serif" }}>
                  {cutDone ? "✓ Cut made" : "Waiting for your cut…"}
                </div>
              )}
            </Panel>
            <Panel title="Reduce-Max bot" accent="#1d4ed8">
              <BambooGarden bamboos={botB} maxDisplayH={LIMIT} lastCut={botLastCut} pandaAt={botLastCut}/>
            </Panel>
          </div>

          {/* History sparklines */}
          <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:14, marginBottom:12 }}>
            {[{hist:pHist,color:"#db2777",label:"Your makespan"},{hist:bHist,color:"#1d4ed8",label:"Bot makespan"}].map(({hist,color,label})=>(
              <Panel key={label} title={label}>
                <Sparkline data={hist} color={color} height={48} maxVal={LIMIT}/>
              </Panel>
            ))}
          </div>

          <div style={{ display:"flex", gap:8, justifyContent:"center" }}>
            {phase==="playing" && (
              <button onClick={endDay} style={btnStyle("#2d8a3e",false)}>
                {cutDone ? "End day →" : "Skip & end day →"}
              </button>
            )}
            {phase==="over" && (
              <button onClick={start} style={btnStyle("#2d8a3e",false)}>Play again</button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// ROOT
// ─────────────────────────────────────────────────────────────────────────────
export default function App() {
  const [tab, setTab] = useState("sandbox");
  const tabs = [["sandbox","Sandbox"],["compare","Compare"],["game","Game"]];

  return (
    <div style={{ fontFamily:"Georgia,'Times New Roman',serif", background:"#f4f0e8",
      minHeight:"100vh", color:"#222" }}>
      {/* Paper-style header */}
      <div style={{ background:"#fff", borderBottom:"2px solid #8B6914",
        padding:"12px 24px 10px", display:"flex", alignItems:"center", justifyContent:"space-between",
        boxShadow:"0 2px 8px rgba(0,0,0,0.08)" }}>
        <div>
          <div style={{ fontSize:17, fontWeight:700, fontFamily:"'CMU Serif',Georgia,serif",
            letterSpacing:"-0.01em", color:"#1f2937" }}>
            Bamboo Garden Trimming
          </div>
          <div style={{ fontSize:11, color:"#888", fontFamily:"Georgia,serif", marginTop:1 }}>
            
          </div>
        </div>
        <div style={{ display:"flex", gap:0, border:"1px solid #d1c9b8", borderRadius:4, overflow:"hidden" }}>
          {tabs.map(([k,l])=>(
            <button key={k} onClick={()=>setTab(k)}
              style={{ padding:"7px 18px", border:"none", borderRight:"1px solid #d1c9b8",
                background:tab===k?"#2d8a3e":"#fff", color:tab===k?"#fff":"#555",
                cursor:"pointer", fontSize:12, fontFamily:"Georgia,serif", fontWeight:tab===k?700:400,
                transition:"all 0.15s" }}>
              {l}
            </button>
          ))}
        </div>
        <div style={{ fontSize:11, color:"#aaa", fontFamily:"Georgia,serif", fontStyle:"italic" }}>
          Reduce-Max · Reduce-Fastest(x) · Optimal oracle
        </div>
      </div>

      <div style={{ padding:"20px 24px", maxWidth:1200, margin:"0 auto" }}>
        {tab==="sandbox" && <SandboxMode/>}
        {tab==="compare" && <CompareMode/>}
        {tab==="game"    && <GameMode/>}
      </div>

      {/* Footer */}
      <div style={{ borderTop:"1px solid #d1c9b8", padding:"10px 24px", textAlign:"center",
        fontSize:10, color:"#aaa", fontFamily:"Georgia,serif", fontStyle:"italic", background:"#fff" }}>
        
      </div>
    </div>
  );
}
