import React, { useEffect, useState, useRef } from 'react';
import '../styles/VideoPanel.css';

export default function VideoPanel({ job, loading, apiBase, brief, stockData, onRegenerate }) {
  const [status, setStatus] = useState(null);
  const [elapsed, setElapsed] = useState(0);
  const [polls, setPolls] = useState(0);
  const pRef = useRef(null), tRef = useRef(null);

  useEffect(() => {
    if (!job?.job_id) { setStatus(null); setElapsed(0); setPolls(0); return; }
    setStatus('processing'); setElapsed(0); setPolls(0);
    tRef.current = setInterval(() => setElapsed(e=>e+1), 1000);
    let cnt = 0;
    const poll = async () => {
      try { const r=await fetch(`${apiBase}/api/video/status/${job.job_id}`); if(r.ok){const d=await r.json();setStatus(d.status);if(d.status==='ready'||d.status==='failed'){clearInterval(pRef.current);clearInterval(tRef.current);return;}} } catch {}
      cnt++; setPolls(cnt);
      if(cnt>=60){clearInterval(pRef.current);clearInterval(tRef.current);setStatus('failed');}
    };
    poll(); pRef.current=setInterval(poll,3000);
    return ()=>{clearInterval(pRef.current);clearInterval(tRef.current);};
  },[job?.job_id,apiBase]);

  if (!job&&!loading) return null;
  const pct = Math.min(92,(polls/60)*100);
  const step = elapsed<10?'Generating voiceover…':elapsed<30?'Rendering slides…':elapsed<60?'Assembling video…':'Finalising MP4…';
  const dlUrl = job?.job_id?`${apiBase}/api/video/download/${job.job_id}`:null;

  return (
    <div className="card video-panel">
      <div className="vp-head">
        <h3 className="panel-title" style={{fontFamily:'var(--serif)'}}>90-Second Video Brief</h3>
        <div className="vp-badges"><span className="vp-tag">Auto-generated</span><span className="vp-tag">MP4 · 720p</span></div>
      </div>

      {(status==='processing'||loading)&&(
        <div className="vp-processing">
          <div className="vp-anim">
            <div className="vp-ring"/><div className="vp-ring2"/>
            <span className="vp-icon">▶</span>
          </div>
          <div className="vp-info">
            <h4>Generating your video brief</h4>
            <p>Converting the AI script to speech and assembling 5 timed slides into your 90-second MP4…</p>
            <div className="vp-bar"><div className="vp-fill" style={{width:`${pct}%`}}/></div>
            <div className="vp-meta"><span style={{fontFamily:'var(--mono)'}}>{elapsed}s elapsed</span><span className="vp-step">{step}</span></div>
          </div>
        </div>
      )}

      {status==='ready'&&dlUrl&&(
        <div className="vp-ready">
          <div className="vr-header">
            <div className="vr-check">✓</div>
            <div><div className="vr-title">Your video brief is ready</div><div className="vr-sub">{stockData?.company_name} ({stockData?.symbol}) · ~90 seconds · 720p</div></div>
          </div>
          {brief&&(
            <div className="vr-structure">
              <div className="vs-label">Script structure</div>
              <div className="vs-steps">
                {[['🎣 Hook','0–10s'],['📊 Snapshot','10–30s'],['📰 News','30–60s'],['💡 Takeaway','60–80s'],['📣 CTA','80–90s']].map(([n,t])=>(
                  <div key={n} className="vs-chip">{n}<span className="vs-time">{t}</span></div>
                ))}
              </div>
            </div>
          )}
          <div className="vp-actions">
            <a href={dlUrl} download={`finvise_${stockData?.symbol}.mp4`} className="dl-btn">↓ Download MP4</a>
            {onRegenerate&&<button className="btn btn-ghost" onClick={onRegenerate}>↺ Regenerate</button>}
          </div>
          <div className="vp-specs">
            <span className="vp-spec">▪ 1280 × 720</span>
            <span className="vp-spec">▪ H.264 / AAC</span>
            <span className="vp-spec">▪ AI voiceover (gTTS)</span>
            <span className="vp-spec">▪ 5 timed sections</span>
          </div>
        </div>
      )}

      {status==='failed'&&(
        <div className="vp-failed">
          <div style={{fontSize:32}}>⚠</div>
          <h4>Video generation failed</h4>
          <p>The AI brief above is complete and usable as a script. Ensure MoviePy, gTTS, and imageio-ffmpeg are installed on the server.</p>
          <div className="fail-tip">Run: <code>pip install moviepy==1.0.3 gTTS imageio-ffmpeg Pillow</code></div>
          {onRegenerate&&<button className="btn" style={{marginTop:16}} onClick={onRegenerate}>↺ Try again</button>}
        </div>
      )}
    </div>
  );
}
