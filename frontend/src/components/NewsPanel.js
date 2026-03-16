import React from 'react';
import '../styles/NewsPanel.css';
const ago = s => { try { const d=(Date.now()-new Date(s).getTime())/1000; if(d<3600)return`${Math.floor(d/60)}m ago`; if(d<86400)return`${Math.floor(d/3600)}h ago`; return`${Math.floor(d/86400)}d ago`; } catch{return'';} };
export default function NewsPanel({ data, loading }) {
  if (loading&&!data) return (
    <div className="news-panel card">
      <div className="panel-head"><div className="skeleton" style={{width:120,height:20}}/></div>
      {[...Array(4)].map((_,i)=><div key={i} style={{padding:'14px 0',borderBottom:'1px solid var(--border)',display:'flex',flexDirection:'column',gap:6}}><div className="skeleton" style={{width:'30%',height:10}}/><div className="skeleton" style={{width:'85%',height:14,marginTop:4}}/><div className="skeleton" style={{width:'70%',height:11,marginTop:4}}/></div>)}
    </div>
  );
  if (!data) return null;
  const articles = data.articles||[];
  return (
    <div className="news-panel card">
      <div className="panel-head">
        <h3 className="panel-title">Recent News</h3>
        <span className="news-count-badge">{articles.length} articles</span>
      </div>
      <div className="news-list">
        {!articles.length
          ? <div className="no-news">No recent news found for this stock.</div>
          : articles.map((a,i)=>(
            <div key={i} className="news-item" onClick={()=>a.url&&window.open(a.url,'_blank')}>
              <div className="n-meta">
                <span className="n-source">{a.source}</span>
                <span className="n-sep"/>
                <span className="n-time">{ago(a.published_at)}</span>
                {a.relevant&&<span className="n-rel">Relevant</span>}
              </div>
              <div className="news-title">{a.title}</div>
              {a.summary&&a.summary!==a.title&&<div className="news-summary">{a.summary.slice(0,170)}{a.summary.length>170?'…':''}</div>}
            </div>
          ))
        }
      </div>
      <div className="panel-foot">Moneycontrol · Economic Times · Business Standard · Livemint · Zee Business</div>
    </div>
  );
}
