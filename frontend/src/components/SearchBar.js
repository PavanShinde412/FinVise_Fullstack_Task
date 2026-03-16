import React, { useState, useRef } from 'react';
import '../styles/SearchBar.css';

export default function SearchBar({ onSearch, loading }) {
  const [val, setVal] = useState('');
  const ref = useRef(null);
  const go = () => { const s=val.trim().toUpperCase(); if(s&&!loading) onSearch(s); };
  return (
    <div className="search-wrapper">
      <div className={`search-box ${loading?'loading':''}`}>
        <div className="search-icon">
          {loading ? <div className="spinner"/> : (
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/></svg>
          )}
        </div>
        <input ref={ref} type="text" className="search-input"
          placeholder="Enter ticker — RELIANCE, TCS, INFY…"
          value={val} onChange={e=>setVal(e.target.value.toUpperCase())}
          onKeyDown={e=>e.key==='Enter'&&go()}
          disabled={loading} autoFocus />
        {val && <button className="search-clear" onClick={()=>{setVal('');ref.current?.focus();}}>✕</button>}
        <button className={`search-btn ${!val.trim()||loading?'disabled':''}`} onClick={go} disabled={!val.trim()||loading}>
          {loading ? 'Analysing…' : 'Analyse →'}
        </button>
      </div>
      {loading && <div className="search-hint"><span className="hint-dot"/><span>Fetching live data from NSE…</span></div>}
    </div>
  );
}
