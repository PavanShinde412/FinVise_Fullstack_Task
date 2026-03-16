import React from 'react';
import '../styles/Header.css';

const TAPE = [
  {n:'NIFTY 50',p:'22,418',c:'+0.42%',up:true},{n:'SENSEX',p:'73,961',c:'+0.38%',up:true},
  {n:'RELIANCE',p:'₹2,847',c:'+1.22%',up:true},{n:'TCS',p:'₹3,841',c:'-0.83%',up:false},
  {n:'HDFC BANK',p:'₹1,612',c:'+0.51%',up:true},{n:'INFOSYS',p:'₹1,478',c:'+1.09%',up:true},
  {n:'BAJFINANCE',p:'₹6,932',c:'-0.31%',up:false},{n:'TATAMOTORS',p:'₹789',c:'+2.10%',up:true},
  {n:'WIPRO',p:'₹462',c:'-0.22%',up:false},{n:'ICICIBANK',p:'₹1,089',c:'+0.73%',up:true},
  {n:'ADANIENT',p:'₹2,341',c:'-1.40%',up:false},{n:'COALINDIA',p:'₹412',c:'+0.64%',up:true},
];

export default function Header() {
  const now = new Date();
  const h = (now.getUTCHours() + 5) % 24 + (now.getUTCMinutes() >= 30 ? 0.5 : 0);
  const isOpen = now.getDay()>=1 && now.getDay()<=5 && h>=9.25 && h<15.5;
  const items = [...TAPE, ...TAPE];
  return (
    <header className="header">
      <div className="header-inner">
        <a href="/" className="header-logo">
          <div className="logo-icon">
            <svg viewBox="0 0 18 18" fill="none" width="18" height="18">
              <path d="M3 13L7 8L10 11L14 5L16 7" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <circle cx="16" cy="5" r="2" fill="#FFD580"/>
            </svg>
          </div>
          <div className="logo-texts">
            <span className="logo-name">Fin<span>Vise</span></span>
            <span className="logo-tag">Market Intelligence</span>
          </div>
        </a>
        <nav className="header-nav">
          <span className="nav-item active">Dashboard</span>
          <a href="https://github.com" target="_blank" rel="noopener noreferrer" className="nav-item">GitHub ↗</a>
        </nav>
        <div className="header-actions">
          <div className="mkt-badge">
            <div className={`mkt-dot ${isOpen ? 'open' : 'closed'}`} />
            <span style={{color:'var(--t1)',fontWeight:600}}>NSE</span>
            <span>{isOpen ? 'Open' : 'Closed'}</span>
            <span className="mkt-time">{now.toLocaleTimeString('en-IN',{hour:'2-digit',minute:'2-digit',timeZone:'Asia/Kolkata'})}</span>
          </div>
        </div>
      </div>
      <div className="ticker-tape">
        <div className="ticker-inner">
          {items.map((t,i) => (
            <div key={i} className="t-item">
              <span className="t-name">{t.n}</span>
              <span className="t-price">{t.p}</span>
              <span className={`t-chg ${t.up?'up':'dn'}`}>{t.c}</span>
            </div>
          ))}
        </div>
      </div>
    </header>
  );
}
