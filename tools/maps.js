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
  const r = opts.r;
  const pins = points.map(p => {
    let [x, y] = proj([p.lon, p.lat]);
    x += p.dx || 0; y += p.dy || 0;
    return `<g class="pin ${p.sev}"><circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${r}"/><text x="${x.toFixed(1)}" y="${(y + r * 0.36).toFixed(1)}" text-anchor="middle">${p.n}</text>${p.label ? (p.pos === 'br' ? `<text class="pl" x="${(x + 4).toFixed(1)}" y="${(y + r + 18).toFixed(1)}" text-anchor="start">${p.label}</text>` : `<text class="pl" x="${(x + (p.left ? -1 : 1) * (r + 6)).toFixed(1)}" y="${(y + 6).toFixed(1)}" text-anchor="${p.left ? 'end' : 'start'}">${p.label}</text>`) : ''}</g>`;
  }).join('');
  return `<svg class="map" viewBox="0 0 ${W} ${H}" role="img" aria-label="${opts.aria}"><path class="land" d="${land}"/>${pins}</svg>`;
}

const out = {
  india: render(items.india, { w: 380, h: 340, land: land50, minPad: 3, r: 14, box: [68, 97, 8, 35], aria: 'Map of India with numbered locations' }),
  world: render(items.world, { w: 860, h: 440, land: land110, minPad: 8, r: 16, aria: 'World map with numbered locations' }),
};
process.stdout.write(JSON.stringify(out));

