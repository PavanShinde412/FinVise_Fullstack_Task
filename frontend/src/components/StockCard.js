import React, { useEffect, useRef } from 'react';
import '../styles/StockCard.css';

const f = (n,d=2) => n==null||n===0?'—':Number(n).toLocaleString('en-IN',{minimumFractionDigits:d,maximumFractionDigits:d});
const fCap = n => { if(!n)return'—'; if(n>=1e12)return`₹${(n/1e12).toFixed(2)}T`; if(n>=1e9)return`₹${(n/1e9).toFixed(2)}B`; return`₹${(n/1e7).toFixed(2)} Cr`; };
const fVol = n => { if(!n)return'—'; if(n>=1e7)return`${(n/1e7).toFixed(2)} Cr`; if(n>=1e5)return`${(n/1e5).toFixed(2)} L`; return n.toLocaleString('en-IN'); };
const SK = ({w='100%',h=14,mt=0}) => <div className="skeleton" style={{width:w,height:h,marginTop:mt,borderRadius:6}}/>;

export default function StockCard({ data, loading }) {
  const priceRef = useRef(null);
  useEffect(() => {
    if (data && priceRef.current) {
      priceRef.current.classList.remove('flash');
      void priceRef.current.offsetWidth;
      priceRef.current.classList.add('flash');
    }
  }, [data?.current_price]);

  if (loading && !data) return (
    <div className="stock-card card">
      <SK w="50%" h={12}/><SK w="75%" h={24} mt={10}/><SK w="40%" h={44} mt={12}/>
      <div style={{marginTop:20,marginBottom:4}}><SK w="100%" h={3}/></div>
      {[...Array(4)].map((_,i)=><div key={i} style={{display:'flex',justifyContent:'space-between',marginTop:12}}><SK w="40%" h={12}/><SK w="30%" h={12}/></div>)}
    </div>
  );
  if (!data) return null;

  const pos = data.pct_change >= 0;
  const pct52 = data.week_52_high > data.week_52_low
    ? ((data.current_price - data.week_52_low)/(data.week_52_high-data.week_52_low))*100 : 50;
  const clamp = v => Math.min(97, Math.max(3, v));

  const metrics = [
    ['Open',`₹${f(data.open)}`],['Day High',`₹${f(data.day_high)}`],
    ['Day Low',`₹${f(data.day_low)}`],['Volume',fVol(data.volume)],
    ['Market Cap',fCap(data.market_cap)],['P/E Ratio',f(data.pe_ratio)],
    ['Prev Close',`₹${f(data.previous_close)}`],['Beta',f(data.beta)],
  ];

  return (
    <div className="stock-card card">
      <div className="stock-top">
        <div className="stock-badges">
          <span className="exchange-badge">{data.exchange}</span>
          {data.sector&&data.sector!=='N/A'&&<span className="sector-badge">{data.sector}</span>}
        </div>
        <div className="company-name">{data.company_name}</div>
        <div className="company-sym">{data.symbol} · {data.exchange}</div>
      </div>

      <div className="price-section">
        <span className="price-main" ref={priceRef}>₹{f(data.current_price)}</span>
        <div className="price-row">
          <span className={`pill ${pos?'pill-pos':'pill-neg'}`}>
            {pos?'▲':'▼'} {pos?'+':''}{f(data.pct_change)}%
          </span>
          <span className={`price-change ${pos?'positive':'negative'}`} style={{fontFamily:'var(--mono)',fontSize:14,fontWeight:600}}>
            {pos?'+':''}₹{f(data.price_change)}
          </span>
        </div>
      </div>

      <div className="range-section">
        <div className="range-labels">
          <span>52W Low <strong>₹{f(data.week_52_low)}</strong></span>
          <span>52W High <strong>₹{f(data.week_52_high)}</strong></span>
        </div>
        <div className="range-track">
          <div className="range-fill" style={{width:`${clamp(pct52)}%`}}/>
          <div className="range-thumb" style={{left:`${clamp(pct52)}%`}}/>
        </div>
        <div style={{position:'relative',height:20}}>
          <div className="range-cur" style={{left:`${clamp(pct52)}%`}}>₹{f(data.current_price)}</div>
        </div>
      </div>

      <div className="metrics-grid">
        {metrics.map(([l,v])=>(
          <div key={l} className="metric-row">
            <span className="m-label">{l}</span>
            <span className="m-val">{v}</span>
          </div>
        ))}
      </div>

      <div className="stock-footer">
        <span className="stock-ts">Updated {new Date(data.timestamp).toLocaleTimeString('en-IN')}</span>
        <span className={`sentiment-chip ${pos?'pill-pos':'pill-neg'}`} style={{fontSize:11,padding:'3px 10px',borderRadius:100,fontWeight:700}}>
          {pos?'📈 Bullish':'📉 Bearish'}
        </span>
      </div>
    </div>
  );
}
