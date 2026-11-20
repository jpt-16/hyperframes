// node stills.js <root> <outdir> <port> t1 t2 ...  -> outdir/s_<t>.png
const { chromium } = require('playwright'); const http = require('http'), fs = require('fs'), path = require('path');
const [root, outdir, port, ...times] = process.argv.slice(2);
fs.mkdirSync(outdir, { recursive: true });
const srv = http.createServer((q, r) => { let f = path.join(root, decodeURIComponent(q.url.split('?')[0])); if (f.endsWith('/')) f += 'index.html';
  const ty = f.endsWith('.js') ? 'text/javascript' : f.endsWith('.html') ? 'text/html' : f.endsWith('.woff2') ? 'font/woff2' : 'application/octet-stream';
  fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); r.end(); return; } r.writeHead(200, { 'Content-Type': ty }); r.end(d); }); }).listen(+port);
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] }); const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  p.on('pageerror', (e) => console.log('pageerror:', e.message.slice(0, 400))); p.on('console', (m) => { if (m.type() === 'error') console.log('console:', m.text().slice(0, 300)); });
  await p.goto(`http://localhost:${port}/`, { waitUntil: 'domcontentloaded' }); for (let i = 0; i < 240 && !(await p.evaluate(() => !!(window.__fieldRender && window.__timelines && window.__timelines.main))); i++) await p.waitForTimeout(500);
  await p.evaluate(() => document.fonts.ready); await p.waitForTimeout(800);
  await p.evaluate(() => { document.querySelectorAll('audio').forEach((a) => a.remove());
    window.__go = (t) => { for (const el of document.querySelectorAll('.clip')) { const s = +el.dataset.start, d = +el.dataset.duration; el.style.visibility = t >= s && t < s + d ? 'visible' : 'hidden'; }
      window.__timelines.main.seek(t, false); window.__fieldRender(t); }; });
  for (const t of times) { await p.evaluate((t) => window.__go(t), +t - 0.05); await p.evaluate((t) => window.__go(t), +t); await p.screenshot({ path: path.join(outdir, `s_${(+t).toFixed(2)}.png`) }); }
  await b.close(); srv.close(); console.log('done'); })();
