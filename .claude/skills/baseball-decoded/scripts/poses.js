// node poses.js <root> <port> <out.png> k1 k2 ...  : the pitcher at each k from the side (top row) and from home (bottom row)
const { chromium } = require('playwright'); const http = require('http'), fs = require('fs'), path = require('path');
const [root, port, out, ...ks] = process.argv.slice(2);
const srv = http.createServer((q, r) => { let f = path.join(root, decodeURIComponent(q.url.split('?')[0])); if (f.endsWith('/')) f += 'index.html';
  const ty = f.endsWith('.js') ? 'text/javascript' : f.endsWith('.html') ? 'text/html' : 'application/octet-stream';
  fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); r.end(); return; } r.writeHead(200, { 'Content-Type': ty }); r.end(d); }); }).listen(+port);
(async () => { const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] }); const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  p.on('pageerror', (e) => console.log('pageerror:', e.message.slice(0, 400)));
  await p.goto(`http://localhost:${port}/`); for (let i = 0; i < 240 && !(await p.evaluate(() => !!window.__dbg && !!window.__fieldRender)); i++) await p.waitForTimeout(500);
  await p.evaluate(() => document.querySelectorAll('.clip').forEach((e) => (e.style.visibility = 'hidden')));
  const tiles = [];
  for (const k of ks) for (const view of ['side', 'home']) {
    const data = await p.evaluate(([k, view]) => { const D = window.__dbg; window.__fieldRender(7.0); D.posePitcher(+k);
      const BB = null; const V = D.v3, c = D.cam;
      D.renderer.setScissorTest(false); D.renderer.setViewport(0, 0, 1080, 1920);
      if (view === 'side') D.frame(c, V(-15, 4.2, -57.4), V(0, 3.4, -57.4), 42, 1080 / 1920); else D.frame(c, V(-2.5, 4.5, -40), V(0, 3.4, -57.4), 30, 1080 / 1920);
      D.setBokeh(0); D.closeLights(false, V(0, 3, -57)); D.renderer.render(D.scene, c); return document.getElementById('field-gl').toDataURL('image/png'); }, [k, view]);
    const f = path.join(path.dirname(out), `pz_${k}_${view}.png`); fs.writeFileSync(f, Buffer.from(data.split(',')[1], 'base64')); tiles.push(f);
  }
  console.log(tiles.join(' ')); await b.close(); srv.close(); })();
