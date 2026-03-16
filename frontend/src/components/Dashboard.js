import React, { useState, useCallback, useEffect } from 'react';
import Header from './Header';
import SearchBar from './SearchBar';
import StockCard from './StockCard';
import PriceChart from './PriceChart';
import NewsPanel from './NewsPanel';
import BriefPanel from './BriefPanel';
import VideoPanel from './VideoPanel';
import ErrorBanner from './ErrorBanner';
import '../styles/Dashboard.css';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';
console.log('[FinVise] API:', API_BASE);
const TICKERS = ['RELIANCE','TCS','INFY','HDFCBANK','BAJFINANCE','TATAMOTORS','WIPRO','ICICIBANK','ADANIENT'];

export default function Dashboard() {
  const [stockData, setStockData] = useState(null);
  const [newsData, setNewsData] = useState(null);
  const [brief, setBrief] = useState(null);
  const [videoJob, setVideoJob] = useState(null);
  const [loading, setLoading] = useState({stock:false,news:false,brief:false,video:false});
  const [errors, setErrors] = useState({});
  const [sym, setSym] = useState('');

  const setL = (k,v) => setLoading(l=>({...l,[k]:v}));
  const setE = (k,v) => setErrors(e=>({...e,[k]:v}));
  const clE = (k) => setErrors(e=>{const n={...e};delete n[k];return n;});

  // Card glow effect
  useEffect(() => {
    const cards = document.querySelectorAll('.card');
    const handler = (e) => {
      cards.forEach(c => {
        const r = c.getBoundingClientRect();
        const x = e.clientX - r.left, y = e.clientY - r.top;
        c.style.setProperty('--mouse-x', x + 'px');
        c.style.setProperty('--mouse-y', y + 'px');
      });
    };
    window.addEventListener('mousemove', handler);
    return () => window.removeEventListener('mousemove', handler);
  }, [stockData]);

  const fetchStock = useCallback(async (s) => {
    setL('stock',true); clE('stock');
    try {
      const r = await fetch(`${API_BASE}/api/stock/${s}`);
      if (!r.ok) { const e=await r.json(); throw new Error(e.detail||'Failed to fetch stock data'); }
      const d = await r.json(); setStockData(d); return d;
    } catch(e) { setE('stock',e.message); return null; }
    finally { setL('stock',false); }
  },[]);

  const fetchNews = useCallback(async (s,name) => {
    setL('news',true); clE('news');
    try {
      const r = await fetch(`${API_BASE}/api/news/${s}?company_name=${encodeURIComponent(name||s)}`);
      if (!r.ok) throw new Error('Failed to fetch news');
      const d = await r.json(); setNewsData(d); return d;
    } catch(e) { setE('news',e.message); return null; }
    finally { setL('news',false); }
  },[]);

  const generateBrief = useCallback(async (stock,news) => {
    setL('brief',true); clE('brief');
    try {
      const body = {
        stock_data:{symbol:stock.symbol,company_name:stock.company_name,current_price:stock.current_price,pct_change:stock.pct_change,price_change:stock.price_change,day_high:stock.day_high,day_low:stock.day_low,week_52_high:stock.week_52_high,week_52_low:stock.week_52_low,volume:stock.volume,market_cap:stock.market_cap,pe_ratio:stock.pe_ratio,sector:stock.sector},
        news_articles:(news?.articles||[]).slice(0,5).map(a=>({title:a.title,summary:a.summary,source:a.source})),
      };
      const r = await fetch(`${API_BASE}/api/brief/generate`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
      if (!r.ok) throw new Error('Failed to generate brief');
      const d = await r.json(); setBrief(d); return d;
    } catch(e) { setE('brief',e.message); return null; }
    finally { setL('brief',false); }
  },[]);

  const generateVideo = useCallback(async (stock,briefData) => {
    setL('video',true); clE('video'); setVideoJob(null);
    try {
      const body={company_name:stock.company_name,symbol:stock.symbol,current_price:stock.current_price,pct_change:stock.pct_change,sentiment:briefData.sentiment||'neutral',sections:briefData.sections,full_script:briefData.full_script};
      const r = await fetch(`${API_BASE}/api/video/generate`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
      if (!r.ok) throw new Error('Failed to start video generation');
      const d = await r.json(); setVideoJob(d); return d;
    } catch(e) { setE('video',e.message); return null; }
    finally { setL('video',false); }
  },[]);

  const handleSearch = useCallback(async (symbol) => {
    setSym(symbol); setStockData(null); setNewsData(null); setBrief(null); setVideoJob(null); setErrors({});
    const stock = await fetchStock(symbol); if (!stock) return;
    const news = await fetchNews(symbol, stock.company_name);
    const briefData = await generateBrief(stock, news); if (!briefData) return;
    await generateVideo(stock, briefData);
  },[fetchStock,fetchNews,generateBrief,generateVideo]);

  return (
    <div className="dashboard">
      <Header />
      <main className="dashboard-main">
        <section className="hero-section">
          <div className="hero-eyebrow">
            <span className="eyebrow-dot" />
            <span className="eyebrow-text">NSE · BSE</span>
            <span className="eyebrow-sep">·</span>
            <span className="eyebrow-sub">Real-time intelligence</span>
          </div>
          <h1 className="hero-title">
            Indian stock intelligence,<br />
            <em>explained simply.</em>
          </h1>
          <p className="hero-desc">Enter any NSE or BSE ticker to get live prices, news aggregation, AI-generated video script, and an auto-produced 90-second MP4 brief.</p>
          <div className="hero-stats">
            <div className="hero-stat"><span className="stat-num">5+</span><span className="stat-lbl">News Sources</span></div>
            <div className="hero-stat"><span className="stat-num">90s</span><span className="stat-lbl">Video Brief</span></div>
            <div className="hero-stat"><span className="stat-num">AI</span><span className="stat-lbl">Groq · Gemini</span></div>
          </div>
          <SearchBar onSearch={handleSearch} loading={loading.stock} />
          <div className="popular-row">
            <span className="popular-label">Quick pick</span>
            {TICKERS.map(t => <button key={t} className="ticker-btn" onClick={()=>handleSearch(t)}>{t}</button>)}
          </div>
        </section>

        {Object.values(errors).filter(Boolean).length > 0 && <ErrorBanner errors={errors} />}

        {(stockData || loading.stock) && (
          <div className="results-grid animate-up">
            <div className="results-top">
              <StockCard data={stockData} loading={loading.stock} />
              <PriceChart data={stockData?.chart_data} loading={loading.stock} symbol={sym} />
            </div>
            <div className="results-mid">
              <NewsPanel data={newsData} loading={loading.news} />
              <BriefPanel data={brief} loading={loading.brief} />
            </div>
            <VideoPanel job={videoJob} loading={loading.video} apiBase={API_BASE} brief={brief} stockData={stockData} onRegenerate={brief&&stockData?()=>generateVideo(stockData,brief):null} />
          </div>
        )}
      </main>
      <footer className="dash-footer">
        <span><span className="footer-logo">Fin<span>Vise</span></span> · Educational purposes only · Not financial advice · Not SEBI registered</span>
        <span>Data via NSE/BSE · Yahoo Finance · Groq · Gemini</span>
      </footer>
    </div>
  );
}
