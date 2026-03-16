import React, { useMemo } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import '../styles/PriceChart.css';

const Tip = ({ active, payload, label }) => {
  if (!active||!payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="ct">
      <div className="ct-date">{label}</div>
      <div className="ct-row"><span>Open</span><span>₹{d.open?.toLocaleString('en-IN')}</span></div>
      <div className="ct-row"><span>High</span><span style={{color:'var(--pos)'}}>₹{d.high?.toLocaleString('en-IN')}</span></div>
      <div className="ct-row"><span>Low</span><span style={{color:'var(--neg)'}}>₹{d.low?.toLocaleString('en-IN')}</span></div>
      <div className="ct-row"><span>Close</span><span style={{color:'var(--accent2)',fontWeight:700}}>₹{d.close?.toLocaleString('en-IN')}</span></div>
    </div>
  );
};

export default function PriceChart({ data, loading, symbol }) {
  const chart = useMemo(()=>(data||[]).map(d=>({...d,date:new Date(d.date).toLocaleDateString('en-IN',{day:'numeric',month:'short'})})),[data]);
  const isUp = useMemo(()=>chart.length<2||chart[chart.length-1].close>=chart[0].close,[chart]);
  const color = isUp ? '#3D9970' : '#C0392B';
  const [lo,hi] = useMemo(()=>{
    if(!chart.length) return [0,0];
    const vals=chart.flatMap(d=>[d.low,d.high]).filter(Boolean);
    const mn=Math.min(...vals),mx=Math.max(...vals),p=(mx-mn)*0.06;
    return [mn-p,mx+p];
  },[chart]);

  if (loading&&!data) return (
    <div className="price-chart card">
      <div className="skeleton" style={{width:'40%',height:20,marginBottom:20}}/>
      <div className="skeleton" style={{height:280}}/>
    </div>
  );
  if (!chart.length) return (
    <div className="price-chart card">
      <div className="chart-top">
        <div className="chart-title-block">
          <div className="chart-title">30-Day Price History</div>
          <div className="chart-meta">{symbol} · NSE · Daily close</div>
        </div>
      </div>
      <div className="chart-placeholder">
        <div style={{color:'var(--text-muted)',fontSize:13}}>Chart data loading…</div>
      </div>
    </div>
  );

  const mtd = ((chart[chart.length-1]?.close-chart[0]?.close)/chart[0]?.close*100).toFixed(2);

  return (
    <div className="price-chart card">
      <div className="chart-top">
        <div className="chart-title-block">
          <div className="chart-title">30-Day Price History</div>
          <div className="chart-meta">{symbol} · NSE · Daily close</div>
        </div>
        <div style={{display:'flex',alignItems:'center',gap:8}}>
          <div className={`chart-badge ${isUp?'up':'dn'}`}>{isUp?'+':''}{mtd}% MTD</div>
        </div>
      </div>
      <div className="chart-wrap">
        <ResponsiveContainer width="100%" height={280}>
          <AreaChart data={chart} margin={{top:10,right:4,left:0,bottom:0}}>
            <defs>
              <linearGradient id="cg" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={color} stopOpacity={0.2}/>
                <stop offset="95%" stopColor={color} stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" vertical={false}/>
            <XAxis dataKey="date" tick={{fill:'#5C5550',fontSize:10,fontFamily:'DM Sans'}} tickLine={false} axisLine={false} interval={4}/>
            <YAxis domain={[lo,hi]} tick={{fill:'#5C5550',fontSize:10,fontFamily:'JetBrains Mono'}} tickLine={false} axisLine={false} tickFormatter={v=>`₹${Math.round(v).toLocaleString('en-IN')}`} width={76}/>
            <Tooltip content={<Tip/>}/>
            <ReferenceLine y={chart[0]?.close} stroke="rgba(255,255,255,0.08)" strokeDasharray="4 4"/>
            <Area type="monotone" dataKey="close" stroke={color} strokeWidth={2} fill="url(#cg)" dot={false} activeDot={{r:5,fill:color,stroke:'var(--bg1)',strokeWidth:2}}/>
          </AreaChart>
        </ResponsiveContainer>
      </div>
      <div className="chart-footer">
        <span>Start: <strong>₹{chart[0]?.close?.toLocaleString('en-IN')}</strong></span>
        <span>Latest: <strong style={{color}}>₹{chart[chart.length-1]?.close?.toLocaleString('en-IN')}</strong></span>
        <span>{chart.length} sessions</span>
      </div>
    </div>
  );
}
