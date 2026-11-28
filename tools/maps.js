// Usage: node maps.js items.json > maps.json
const fs = require('fs');
const d3 = require('d3-geo');
const topo = require('topojson-client');
const items = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const simp = require('topojson-simplify');
let t50 = require('world-atlas/land-50m.json');
t50 = simp.presimplify(t50);
t50 = simp.simplify(t50, simp.quantile(t50, 0.93));
const land50 = topo.feature(t50, 'land');
const land110 = topo.feature(require('world-atlas/land-110m.json'), 'land');

// ── automatic layout (Nov 2026): no two pins overlap, and labels go where they fit ─────────────────────────────
// 1. Pins closer than one diameter are pushed apart; a pin moved off its place gets a thin line to a small dot on
//    the true spot. 2. Each label tries right, left, above, below (the item's "left"/"pos" hint first) and takes the
//    spot that covers no pin, no other label and stays inside the map; if none is clear, the label is dropped (the
//    numbered key under the map names every place). "label": "" still hides a label; "dx"/"dy" still nudge a pin.
const FS = 15, CH = 8.6;                                  // label font size and average character width (Figtree 600)
function layout(pts, r, W, H) {
  const num = pts.filter(p => p.n !== '' && p.n !== undefined);
  num.forEach(p => { p.ax = p.x; p.ay = p.y; });
  const gap = 2 * r + 3;
  for (let it = 0; it < 200; it++) {
    let moved = false;
    for (let i = 0; i < num.length; i++) for (let j = i + 1; j < num.length; j++) {
      const a = num[i], b = num[j];
      let dx = b.x - a.x, dy = b.y - a.y, d = Math.hypot(dx, dy);
      if (d >= gap) continue;
      if (d < 0.01) { const t = (j * 2.39996); dx = Math.cos(t); dy = Math.sin(t); d = 1; }
      const push = (gap - d) / 2 + 0.2, ux = dx / d, uy = dy / d;
      a.x -= ux * push; a.y -= uy * push; b.x += ux * push; b.y += uy * push; moved = true;
    }
    num.forEach(p => { p.x = Math.min(Math.max(p.x, r + 2), W - r - 2); p.y = Math.min(Math.max(p.y, r + 2), H - r - 2); });
    if (!moved) break;
  }
  num.forEach(p => { p.moved = Math.hypot(p.x - p.ax, p.y - p.ay) > r * 0.5; });
  // obstacles: every pin circle (as a box) and every true-spot dot
  const boxes = pts.map(p => [p.x - r, p.y - r, p.x + r, p.y + r]);
  num.filter(p => p.moved).forEach(p => boxes.push([p.ax - 4, p.ay - 4, p.ax + 4, p.ay + 4]));
  const ov = (a, b) => Math.max(0, Math.min(a[2], b[2]) - Math.max(a[0], b[0])) * Math.max(0, Math.min(a[3], b[3]) - Math.max(a[1], b[1]));
  const crowd = p => pts.filter(q => q !== p && Math.hypot(q.x - p.x, q.y - p.y) < 6 * r).length;
  const placed = [];
  [...pts].filter(p => p.label).sort((a, b) => crowd(b) - crowd(a)).forEach(p => {
    const w = p.label.length * CH + 4, h = FS + 2;
    const cand = {
      right: { box: [p.x + r + 4, p.y - h / 2, p.x + r + 4 + w, p.y + h / 2], tx: p.x + r + 5, ty: p.y + 5, anchor: 'start' },
      left: { box: [p.x - r - 4 - w, p.y - h / 2, p.x - r - 4, p.y + h / 2], tx: p.x - r - 5, ty: p.y + 5, anchor: 'end' },
      above: { box: [p.x - w / 2, p.y - r - 3 - h, p.x + w / 2, p.y - r - 3], tx: p.x, ty: p.y - r - 7, anchor: 'middle' },
      below: { box: [p.x - w / 2, p.y + r + 3, p.x + w / 2, p.y + r + 3 + h], tx: p.x, ty: p.y + r + 3 + FS, anchor: 'middle' },
    };
    const order = p.pos === 'br' ? ['below', 'right', 'left', 'above'] : p.left ? ['left', 'right', 'above', 'below'] : ['right', 'left', 'above', 'below'];
    let best = null;
    for (const k of order) {
      const c = cand[k], b = c.box;
      let cost = boxes.reduce((s, o) => s + ov(b, o), 0) + placed.reduce((s, o) => s + ov(b, o), 0);
      if (b[0] < 0 || b[2] > W || b[1] < 0 || b[3] > H) cost += 1e6;
      if (!best || cost < best.cost) best = { ...c, cost };
      if (cost === 0) break;
    }
    if (best && best.cost === 0) { p.lb = best; placed.push(best.box); }
  });
  return pts;
}

// ── callout style (Nov 2026, owner's choice): small dots at the exact places, never moved; each label is a number
// chip + place name set just off the dot with a hairline, placed where it covers no dot and no other label. Stories in
// the same place share one label ("6 7 Sudan"). opts.fs = label font size (larger on the world map, which is scaled down).
function callouts(pts, W, H, fs) {
  const cr = fs * 0.62, dotR = Math.max(4, fs * 0.3), ch = fs * 0.56;
  // group same-label points that sit close together
  const groups = [];
  pts.forEach(p => {
    const g = p.label && groups.find(g => g.label === p.label && g.pts.some(q => Math.hypot(q.x - p.x, q.y - p.y) < fs * 1.2));
    if (g) g.pts.push(p); else groups.push({ label: p.label, sev: p.sev, pts: [p] });
  });
  groups.forEach(g => { g.x = g.pts.reduce((s, p) => s + p.x, 0) / g.pts.length; g.y = g.pts.reduce((s, p) => s + p.y, 0) / g.pts.length;
    g.w = g.pts.length * (2 * cr + 3) + (g.label ? g.label.length * ch + 6 : 0) + 4; g.h = 2 * cr + 4; });
  const dots = pts.map(p => [p.x - dotR - 3, p.y - dotR - 3, p.x + dotR + 3, p.y + dotR + 3]);
  const ov = (a, b) => Math.max(0, Math.min(a[2], b[2]) - Math.max(a[0], b[0])) * Math.max(0, Math.min(a[3], b[3]) - Math.max(a[1], b[1]));
  const placed = [];
  const crowd = g => groups.filter(o => o !== g && Math.hypot(o.x - g.x, o.y - g.y) < fs * 8).length;
  [...groups].sort((a, b) => crowd(b) - crowd(a)).forEach(g => {
    let best = null;
    for (const d of [6, 16, 30, 48, 70, 95]) {
      for (const a of [0, 180, -35, 35, 145, -145, -70, 70, 110, -110, -90, 90]) {
        const t = a * Math.PI / 180, cx = g.x + Math.cos(t) * (d + g.w / 2 * Math.abs(Math.cos(t)) + dotR), cy = g.y + Math.sin(t) * (d + g.h / 2 + dotR);
        const b = [cx - g.w / 2, cy - g.h / 2, cx + g.w / 2, cy + g.h / 2];
        let cost = dots.reduce((s, o) => s + ov(b, o), 0) * 3 + placed.reduce((s, o) => s + ov(b, o), 0) * 3;
        if (b[0] < 2 || b[2] > W - 2 || b[1] < 2 || b[3] > H - 2) cost += 1e6;
        cost += d * 0.5;
        if (!best || cost < best.cost) best = { b, cost };
      }
      if (best && best.cost < 1e3 && best.cost <= d * 0.5 + 0.01) break;
    }
    g.box = best.b; placed.push(best.b);
  });
  const near = (b, x, y) => [Math.min(Math.max(x, b[0]), b[2]), Math.min(Math.max(y, b[1]), b[3])];
  const lines = [], dotsSvg = [], labels = [];
  groups.forEach(g => {
    g.pts.forEach(p => {
      const [nx, ny] = near(g.box, p.x, p.y);
      if (Math.hypot(nx - p.x, ny - p.y) > dotR + 2) lines.push(`<line class="lead" x1="${p.x.toFixed(1)}" y1="${p.y.toFixed(1)}" x2="${nx.toFixed(1)}" y2="${ny.toFixed(1)}"/>`);
      dotsSvg.push(`<circle class="dot ${p.sev}" cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="${dotR.toFixed(1)}"/>`);
    });
    const [x0, y0, x1, y1] = g.box, my = (y0 + y1) / 2;
    let x = x0 + 2 + cr, chips = '';
    g.pts.forEach(p => {
      chips += `<a class="pinl" href="#i${p.n}" aria-label="${p.label || 'Story ' + p.n}"><circle class="chip ${p.sev}" cx="${x.toFixed(1)}" cy="${my.toFixed(1)}" r="${cr.toFixed(1)}"/><text class="cn" x="${x.toFixed(1)}" y="${(my + fs * 0.33).toFixed(1)}" text-anchor="middle" style="font-size:${(fs * 0.8).toFixed(1)}px">${p.n}</text></a>`;
      x += 2 * cr + 3;
    });
    const tx = g.label ? `<a href="#i${g.pts[0].n}" tabindex="-1"><text class="pl" x="${(x - cr + 4).toFixed(1)}" y="${(my + fs * 0.35).toFixed(1)}" style="font-size:${fs}px">${g.label}</text></a>` : '';
    labels.push(`<g class="callout"><rect class="lbg" x="${x0.toFixed(1)}" y="${y0.toFixed(1)}" width="${(x1 - x0).toFixed(1)}" height="${(y1 - y0).toFixed(1)}" rx="${((y1 - y0) / 2).toFixed(1)}"/>${chips}${tx}</g>`);
  });
  const all = [...placed, ...dots];
  const bb = [Math.min(...all.map(b => b[0])), Math.min(...all.map(b => b[1])), Math.max(...all.map(b => b[2])), Math.max(...all.map(b => b[3]))].map(v => v.toFixed(0)).join(' ');
  return { svg: `<g class="callouts">${lines.join('')}${dotsSvg.join('')}${labels.join('')}</g>`, bb };
}

function render(points, opts) {
  const W = opts.w, H = opts.h;
  const proj = d3.geoMercator();
  const lons = points.map(p => p.lon), lats = points.map(p => p.lat);
  let [x0, x1, y0, y1] = opts.box || [Math.min(...lons), Math.max(...lons), Math.min(...lats), Math.max(...lats)];
  const padX = Math.max((x1 - x0) * 0.25, opts.minPad), padY = Math.max((y1 - y0) * 0.3, opts.minPad);
  x0 -= padX; x1 += padX; y0 -= padY; y1 += padY;
  const box = { type: 'Feature', geometry: { type: 'Polygon', coordinates: [[[x0, y0], [x0, y1], [x1, y1], [x1, y0], [x0, y0]]] } };
  proj.fitExtent([[0, 0], [W, H]], box);
  proj.clipExtent([[0, 0], [W, H]]);
  const path = d3.geoPath(proj).digits(1);
  const feats = opts.land.features || [opts.land];
  const polys = [];
  feats.forEach(f => { const g = f.geometry; if (!g) return; if (g.type === 'MultiPolygon') polys.push(...g.coordinates); else if (g.type === 'Polygon') polys.push(g.coordinates); });
  const keep = polys.filter(pc => { const b = path.bounds({type:'Polygon',coordinates:pc}); return b[1][0] > 0 && b[0][0] < W && b[1][1] > 0 && b[0][1] < H && (b[1][0]-b[0][0])*(b[1][1]-b[0][1]) > 4; });
  const land = path({type:'MultiPolygon',coordinates:keep});
  if (opts.fs) {
    const pp = points.map(p => { const [x, y] = proj([p.lon, p.lat]); return { ...p, x, y }; });
    const co = callouts(pp, W, H, opts.fs);
    return `<svg class="map map-co" data-bounds="${co.bb}" viewBox="0 0 ${W} ${H}" role="img" aria-label="${opts.aria}"><path class="land" d="${land}"/>${co.svg}</svg>`;
  }
  const r = opts.r;
  const laid = layout(points.map(p => { const [x, y] = proj([p.lon, p.lat]); return { ...p, x: x + (p.dx || 0), y: y + (p.dy || 0) }; }), r, W, H);
  const pins = laid
    .map(p => {
      const lead = p.moved ? `<line class="lead" x1="${p.ax.toFixed(1)}" y1="${p.ay.toFixed(1)}" x2="${p.x.toFixed(1)}" y2="${p.y.toFixed(1)}"/><circle class="anchor" cx="${p.ax.toFixed(1)}" cy="${p.ay.toFixed(1)}" r="3.5"/>` : '';
      const lab = p.lb ? `<text class="pl" x="${p.lb.tx.toFixed(1)}" y="${p.lb.ty.toFixed(1)}" text-anchor="${p.lb.anchor}">${p.label}</text>` : '';
      const g = `<g class="pin ${p.sev}">${lead}<circle cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="${r}"/><text x="${p.x.toFixed(1)}" y="${(p.y + r * 0.36).toFixed(1)}" text-anchor="middle">${p.n}</text>${lab}</g>`;
      // Numbered pins link to their story on the page (#iN); Focus-map dots (empty n) stay plain.
      return p.n !== '' && p.n !== undefined ? `<a class="pinl" href="#i${p.n}" aria-label="${p.label || 'Story ' + p.n}">${g}</a>` : g;
    }).join('');
  const all = [];
  laid.forEach(p => { all.push([p.x - r, p.y - r, p.x + r, p.y + r]); if (p.lb) all.push(p.lb.box); if (p.moved) all.push([p.ax - 4, p.ay - 4, p.ax + 4, p.ay + 4]); });
  const bb = all.length ? [Math.min(...all.map(b => b[0])), Math.min(...all.map(b => b[1])), Math.max(...all.map(b => b[2])), Math.max(...all.map(b => b[3]))].map(v => v.toFixed(0)).join(' ') : '';
  return `<svg class="map" data-bounds="${bb}" viewBox="0 0 ${W} ${H}" role="img" aria-label="${opts.aria}"><path class="land" d="${land}"/>${pins}</svg>`;
}

// Focus maps: {"custom": {"points": [...], "box": [lon0, lon1, lat0, lat1], "w", "h", "aria"}} -> {"custom": svg}.
// A point with an empty "n" draws a small dot instead of a numbered pin.
const c = items.custom;
const out = c ? { custom: render(c.points, { w: c.w || 860, h: c.h || 520, land: land50, minPad: 1, r: c.r || 9, box: c.box, aria: c.aria || 'Map' }) } : {
  india: !(items.india || []).length ? '' : render(items.india, { w: 380, h: 340, land: land50, minPad: 3, r: 14, fs: 14, box: [68, 97, 8, 35], aria: 'Map of India with numbered locations' }),
  world: !(items.world || []).length ? '' : render(items.world, { w: 860, h: 440, land: land110, minPad: 8, r: 16, fs: 18, aria: 'World map with numbered locations' }),
  world_m: !(items.world || []).length ? '' : render(items.world, { w: 520, h: 440, land: land110, minPad: 8, r: 16, fs: 20, aria: 'World map with numbered locations' }),
};
process.stdout.write(JSON.stringify(out));

