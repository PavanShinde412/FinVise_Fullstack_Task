import React from 'react';
export default function ErrorBanner({ errors }) {
  const msgs = Object.entries(errors).filter(([,v])=>v);
  if (!msgs.length) return null;
  return (
    <div style={{background:'rgba(192,57,43,0.08)',border:'1px solid rgba(192,57,43,0.25)',borderRadius:10,padding:'14px 20px',marginBottom:20,display:'flex',flexDirection:'column',gap:6}}>
      {msgs.map(([k,v])=>(
        <div key={k} style={{display:'flex',gap:10,fontSize:13}}>
          <span style={{color:'var(--neg)',fontWeight:700,textTransform:'capitalize',flexShrink:0}}>{k}:</span>
          <span style={{color:'var(--t2)'}}>{v}</span>
        </div>
      ))}
    </div>
  );
}
