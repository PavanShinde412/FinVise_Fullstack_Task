import React, { useState } from 'react';
import '../styles/BriefPanel.css';
const SECS = [
  {key:'hook',label:'Hook',time:'0–10s',icon:'🎣'},
  {key:'stock_snapshot',label:'Stock Snapshot',time:'10–30s',icon:'📊'},
  {key:'whats_happening',label:"What's Happening",time:'30–60s',icon:'📰'},
  {key:'beginner_takeaway',label:'Beginner Takeaway',time:'60–80s',icon:'💡'},
  {key:'call_to_action',label:'Call to Action',time:'80–90s',icon:'📣'},
];
export default function BriefPanel({ data, loading }) {
  const [open, setOpen] = useState('hook');
  const [showFull, setShowFull] = useState(false);
  if (loading&&!data) return (
    <div className="brief-panel card">
      <div className="panel-head"><div className="skeleton" style={{width:140,height:20}}/></div>
      {[...Array(5)].map((_,i)=><div key={i} className="skeleton" style={{height:46,marginBottom:4,borderRadius:8}}/>)}
    </div>
  );
  if (!data) return null;
  const sm = {bullish:{cls:'pill-pos',label:'↑ Bullish'},bearish:{cls:'pill-neg',label:'↓ Bearish'},neutral:{cls:'pill-neutral',label:'→ Neutral'}};
  const s = sm[data.sentiment]||sm.neutral;
  return (
    <div className="brief-panel card">
      <div className="brief-top">
        <div className="brief-title-row">
          <h3 className="panel-title">AI Video Brief</h3>
          {data.llm_used&&<span className="llm-chip">via {data.llm_used}</span>}
        </div>
        <span className={`pill ${s.cls}`}>{s.label}</span>
      </div>
      {data.key_points?.length>0&&(
        <div className="kp-section">
          {data.key_points.map((p,i)=>(
            <div key={i} className="kp-item"><span className="kp-num">{i+1}.</span><span>{p}</span></div>
          ))}
        </div>
      )}
      <div className="script-list">
        {SECS.map(({key,label,time,icon})=>{
          const sec=data.sections?.[key]; if(!sec) return null;
          const isOpen=open===key;
          return (
            <div key={key} className={`script-item ${isOpen?'active':''}`} onClick={()=>setOpen(o=>o===key?null:key)}>
              <div className="si-head">
                <span className="si-timing">{time}</span>
                <span className="si-icon" style={{fontSize:14}}>{icon}</span>
                <span className="si-label">{label}</span>
                <span className="si-toggle">{isOpen?'−':'+'}</span>
              </div>
              {isOpen&&<div className="si-body"><div className="si-text">{sec.text}</div></div>}
            </div>
          );
        })}
      </div>
      <button className="full-script-btn" onClick={()=>setShowFull(f=>!f)}>
        {showFull?'▲ Hide full script':'▼ View complete voiceover script'}
      </button>
      {showFull&&data.full_script&&(
        <div className="full-script-box">
          <div className="fs-head"><span>Complete script</span><button className="copy-btn" onClick={()=>navigator.clipboard?.writeText(data.full_script)}>Copy</button></div>
          <p className="fs-text">{data.full_script}</p>
        </div>
      )}
      {data.disclaimer&&<div className="brief-disclaimer">{data.disclaimer}</div>}
    </div>
  );
}
