// node tools/render_chunks.js . <outdir> 30 <duration> [chunk=90] [port]  -> <outdir>/cNNN.mp4, one per chunk (video only). Resumable: finished chunks are skipped.
// For containers that restart mid-render. Join them and add the mix with ffmpeg (concat demuxer + assets/mix.wav).
const { chromium } = require('playwright'); const http = require('http'), fs = require('fs'), path = require('path'), { execFileSync } = require('child_process');
const [root, outdir, fpsS, durS, chunkS = '90', port = '8790'] = process.argv.slice(2);
const fps = +fpsS, N = Math.round(+durS * fps), CH = +chunkS;
fs.mkdirSync(outdir, { recursive: true });
const srv = http.createServer((q, r) => { let f = path.join(root, decodeURIComponent(q.url.split('?')[0])); if (f.endsWith('/')) f += 'index.html';
  const ty = f.endsWith('.js') ? 'text/javascript' : f.endsWith('.html') ? 'text/html' : f.endsWith('.css') ? 'text/css' : f.endsWith('.woff2') ? 'font/woff2' : f.endsWith('.png') ? 'image/png' : 'application/octet-stream';
  fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); r.end(); return; } r.writeHead(200, { 'Content-Type': ty }); r.end(d); }); }).listen(+port);
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  p.on('pageerror', (e) => console.log('pageerror:', e.message.slice(0, 300)));
  await p.goto(`http://localhost:${port}/`, { waitUntil: 'domcontentloaded' }); for (let i = 0; i < 360 && !(await p.evaluate(() => !!(window.__fieldRender && window.__timelines && window.__timelines.main))); i++) await p.waitForTimeout(500);
  await p.evaluate(() => document.fonts.ready); await p.waitForTimeout(1500);
  await p.evaluate(() => { document.querySelectorAll('audio').forEach((a) => a.remove());
    window.__go = (t) => { for (const el of document.querySelectorAll('.clip')) { const s = +el.dataset.start, d = +el.dataset.duration; el.style.visibility = t >= s && t < s + d ? 'visible' : 'hidden'; }
      window.__timelines.main.seek(t, false); window.__fieldRender(t); }; });
  for (let c0 = 0; c0 < N; c0 += CH) {
    const name = path.join(outdir, `c${String(c0 / CH).padStart(3, '0')}.mp4`); if (fs.existsSync(name)) continue;
    const tmp = path.join(outdir, 'tmp'); fs.rmSync(tmp, { recursive: true, force: true }); fs.mkdirSync(tmp);
    for (let k = Math.max(0, c0 - 45); k < c0; k++) await p.evaluate((t) => window.__go(t), k / fps);   // warm up the sim state
    const c1 = Math.min(N, c0 + CH);
    for (let k = c0; k < c1; k++) { await p.evaluate((t) => window.__go(t), k / fps); await p.screenshot({ path: path.join(tmp, `f${String(k - c0).padStart(4, '0')}.png`) }); }
    execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-framerate', String(fps), '-i', path.join(tmp, 'f%04d.png'), '-c:v', 'libx264', '-preset', 'medium', '-crf', '12', '-pix_fmt', 'yuv420p', '-r', String(fps), name + '.part.mp4']);
    fs.renameSync(name + '.part.mp4', name); fs.rmSync(tmp, { recursive: true, force: true }); console.log('chunk', c0 / CH, 'done', new Date().toISOString());
  }
  console.log('ALL DONE'); await b.close(); srv.close(); })();
