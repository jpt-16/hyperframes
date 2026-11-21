// node camtest.js <episode dir> <port> <outdir> '<scene json: {"fn":"C"|"S"|"H"|"G","t":..,"s":{...}}>' '<cameras json: [[[cx,cy,cz],[lx,ly,lz],fov,close?,paneWidthPx?], ...]>'
// A pane width (e.g. 540) renders a half-width tall pane at the left of the 1080x1920 image.
// Renders one setSceneC / setSceneS scene from each candidate camera -> outdir/cam_<i>.png (1080x1920), and prints the catcher's hand position.
const { chromium } = require('playwright'); const http = require('http'), fs = require('fs'), path = require('path');
const [root, port, outdir, sceneJson, camsJson] = process.argv.slice(2);
fs.mkdirSync(outdir, { recursive: true });
const srv = http.createServer((q, r) => { let f = path.join(root, decodeURIComponent(q.url.split('?')[0])); if (f.endsWith('/')) f += 'index.html';
  const ty = f.endsWith('.js') ? 'text/javascript' : f.endsWith('.html') ? 'text/html' : 'application/octet-stream';
  fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); r.end(); return; } r.writeHead(200, { 'Content-Type': ty }); r.end(d); }); }).listen(+port);
(async () => { const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] }); const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  p.on('pageerror', (e) => console.log('pageerror:', e.message.slice(0, 400)));
  await p.goto(`http://localhost:${port}/`); for (let i = 0; i < 240 && !(await p.evaluate(() => !!window.__dbg && !!window.__fieldRender)); i++) await p.waitForTimeout(500);
  await p.evaluate(() => document.querySelectorAll('.clip').forEach((e) => (e.style.visibility = 'hidden')));
  const scene = JSON.parse(sceneJson), cams = JSON.parse(camsJson);
  for (let i = 0; i < cams.length; i++) {
    const out = await p.evaluate(([scene, cam]) => { const D = window.__dbg; window.__fieldRender(7.0); ({ S: D.setSceneS, H: D.setSceneH, G: D.setSceneG }[scene.fn] ?? D.setSceneC)(scene.t, scene.s, 0);
      const V = D.v3, c = D.cam, [pos, look, fov, close, pw] = cam, W_ = pw ?? 1080; D.renderer.setScissorTest(!!pw); D.renderer.setViewport(0, 0, W_, 1920); if (pw) D.renderer.setScissor(0, 0, W_, 1920);
      c.up.set(0, 1, 0); D.frame(c, V(...pos), V(...look), fov, W_ / 1920); D.setBokeh(0); D.closeLights(!!close, V(...look)); D.renderer.render(D.scene, c);
      const w = (o) => { const q = D.wpos(o); return [+q.x.toFixed(2), +q.y.toFixed(2), +q.z.toFixed(2)]; };
      return { img: document.getElementById('field-gl').toDataURL('image/png'), handR: w(D.C.handR), handL: w(D.C.handL), pelvis: w(D.C.pelvis) }; }, [scene, cams[i]]);
    fs.writeFileSync(path.join(outdir, `cam_${i}.png`), Buffer.from(out.img.split(',')[1], 'base64')); if (i === 0) console.log(JSON.stringify({ handR: out.handR, handL: out.handL, pelvis: out.pelvis }));
  }
  await b.close(); srv.close(); console.log('done'); })();
