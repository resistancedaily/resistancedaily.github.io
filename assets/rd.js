/* Resistance Daily · thread player + reader state (vanilla JS, no build step). Adapted from the design handoff's
   reference/rd-player.js. Reader state lives only in localStorage on this device: rd.follow (slugs), rd.seen
   ({slug: edition date}). No accounts, no cookies, nothing leaves the device.
   Page hooks: #rd-threads (JSON: {date, order, threads}), .rd-thread[data-thread] cards, [data-rd-play-all],
   [data-rd-follow-count], [data-rd-caught-up], #rd-player, [data-rd-follow="slug"], [data-rd-map] + dialog.rd-mapd,
   details.rd-stories (opened when the URL points at one story, #iN). */
(function () {
  const K = { follow: 'rd.follow', seen: 'rd.seen' };
  const read = (k, d) => { try { const v = JSON.parse(localStorage.getItem(k)); return v == null ? d : v; } catch (e) { return d; } };
  const write = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} };
  const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  let follow = new Set(read(K.follow, []));
  let seen = read(K.seen, {});
  const saveFollow = () => write(K.follow, [...follow]);
  const paintCount = () => document.querySelectorAll('[data-rd-follow-count]').forEach(el => { el.textContent = follow.size; });

  // Follow buttons on thread / focus / accountability pages (work without the player).
  document.querySelectorAll('[data-rd-follow]').forEach(b => {
    const s = b.dataset.rdFollow, lab = () => { b.textContent = follow.has(s) ? 'Following' : 'Follow this thread'; b.setAttribute('aria-pressed', follow.has(s)); };
    lab(); b.addEventListener('click', () => { follow.has(s) ? follow.delete(s) : follow.add(s); saveFollow(); lab(); paintCount(); });
  });
  paintCount();

  // A link to one story (#iN) opens the folded "All stories" list.
  function openStory() {
    const m = location.hash.match(/^#i\d+$/); if (!m) return;
    const el = document.querySelector(location.hash); const d = el && el.closest('details');
    if (d && !d.open) { d.open = true; el.scrollIntoView(); }
  }
  // Refresh starts at the top of the page (owner's request, 5 Nov 2026); Back/Forward return readers to where they were;
  // a link to one story (#iN) still lands on that story. Scroll is handled here, not by the browser.
  try {
    const key = 'rd.y:' + location.pathname;
    const nav = performance.getEntriesByType('navigation')[0], type = nav ? nav.type : 'navigate';
    if ('scrollRestoration' in history) history.scrollRestoration = 'manual';
    window.addEventListener('pagehide', () => { try { sessionStorage.setItem(key, String(scrollY)); } catch (e) {} });
    let y = null;
    if (type === 'back_forward') { const v = sessionStorage.getItem(key); if (v !== null) y = +v; }
    else if (!location.hash || type === 'reload') {
      if (location.hash && !/^#i\d+$/.test(location.hash)) history.replaceState(null, '', location.pathname + location.search);
      if (!/^#i\d+$/.test(location.hash)) y = 0;
    }
    if (y !== null) { const go = () => window.scrollTo(0, y); go(); window.addEventListener('load', () => { go(); setTimeout(go, 50); }); }
  } catch (e) {}
  window.addEventListener('hashchange', openStory); openStory();
  // "How we report" in the top menu opens the fold, not just scrolls to it (owner's request, 5 Nov 2026).
  function openHow(scroll) {
    const d = document.getElementById('how'); if (!d || d.tagName !== 'DETAILS') return false;
    d.open = true; if (scroll) d.scrollIntoView({ behavior: 'smooth', block: 'start' }); return true;
  }
  if (location.hash === '#how') openHow(true);
  window.addEventListener('hashchange', () => { if (location.hash === '#how') openHow(true); });
  document.querySelectorAll('a[href$="#how"]').forEach(a => a.addEventListener('click', e => {
    if (new URL(a.href).pathname === location.pathname && openHow(true)) { e.preventDefault(); history.replaceState(null, '', '#how'); }
  }));
  // "Hide all stories −" at the end of the long list: close it and return to its header.
  document.querySelectorAll('[data-rd-collapse]').forEach(b => b.addEventListener('click', () => {
    const d = b.closest('details'); if (!d) return; d.open = false; d.scrollIntoView({ block: 'start' });
    if (/^#i\d+$/.test(location.hash)) history.replaceState(null, '', location.pathname + location.search);
  }));

  // Map dialog.
  const mapd = document.querySelector('dialog.rd-mapd');
  document.querySelectorAll('[data-rd-map]').forEach(b => b.addEventListener('click', () => { if (mapd && mapd.showModal) mapd.showModal(); }));
  if (mapd) {
    mapd.addEventListener('click', e => { if (e.target === mapd || e.target.closest('[data-close]')) mapd.close(); });
    mapd.querySelectorAll('a.pinl').forEach(a => a.addEventListener('click', () => mapd.close()));
  }

  const dataEl = document.getElementById('rd-threads');
  const player = document.getElementById('rd-player');
  if (!dataEl || !player) return;
  const DATA = JSON.parse(dataEl.textContent);
  let cur = null, step = 0, playAll = false, lastFocus = null;
  const isNew = s => DATA.threads[s] && DATA.threads[s].updates.some(u => u.isNew);
  const moved = () => DATA.order.filter(isNew);

  function paintCards() {
    document.querySelectorAll('.rd-thread[data-thread]').forEach(el => {
      const s = el.dataset.thread, t = DATA.threads[s]; if (!t) return;
      const done = seen[s] === DATA.date, mv = isNew(s), n = t.updates.filter(u => u.isNew).length;
      el.classList.toggle('is-seen', done && mv);
      el.classList.toggle('is-following', follow.has(s));
      if (!mv) el.hidden = true;                        // only threads that moved today (the ones in Play today) show
      el.querySelectorAll('.rd-state').forEach(st => { st.textContent = !mv ? 'Quiet' : done ? 'Seen' : `${n} new`; });
    });
    paintCount();
    const grid = document.querySelector('[data-rd-thread-grid]');
    if (grid) [...grid.children].sort((a, b) => (follow.has(b.dataset.thread) - follow.has(a.dataset.thread))).forEach(c => grid.appendChild(c));
    const cu = document.querySelector('[data-rd-caught-up]');
    if (cu && moved().length && moved().every(s => seen[s] === DATA.date)) cu.hidden = false;
  }

  function render(keep) {
    const t = DATA.threads[cur], u = t.updates[step];
    // Play today: one bar segment per story across every thread that moved (like a stories reel); one thread: its updates.
    let total = t.updates.length, at = step;
    if (playAll) {
      const mv = moved(), n = x => DATA.threads[x].updates.filter(y => y.isNew).length;
      total = mv.reduce((a, x) => a + n(x), 0); at = mv.slice(0, mv.indexOf(cur)).reduce((a, x) => a + n(x), 0) + step;
    }
    const segs = Array.from({ length: total }, (_, i) => `<i class="${i < at ? 'on' : i === at ? 'cur' : ''}"><b></b></i>`).join('');
    const src = (u.src || []).map(([n, url]) => `<a href="${esc(url)}">${esc(n)}</a>`).join(' · ');
    const fol = follow.has(cur) ? 'Following' : 'Follow';
    player.innerHTML = `
      <div class="rd-p-card">
        <div class="rd-p-segs" aria-hidden="true">${segs}</div>
        <div class="rd-p-head"><h2 id="rd-p-name">${esc(t.name)}</h2>
          <div class="rd-p-actions"><button class="btn btn-secondary" data-act="follow" aria-pressed="${follow.has(cur)}">${fol}</button>
          <button class="rd-p-close" data-act="close" aria-label="Close">✕</button></div></div>
        <div class="rd-p-body${t.img ? '' : ' nophoto'}">
          ${t.img ? `<figure class="rd-p-photo"><img class="washed" src="${esc(t.img)}" alt="">
            <span class="rd-p-ptag">${esc(t.photoTag)}</span>
            <details><summary aria-label="About this photo">i</summary><figcaption>Photo: <a href="${esc(t.creditUrl)}">${esc(t.credit)}</a></figcaption></details></figure>` : ''}
          <div class="rd-p-text">
            <div class="rd-p-tags"><span class="tag tag-neutral">${esc(u.d)}</span>${u.isNew ? '<span class="tag tag-accent rd-p-desk">New today</span>' : ''}${u.upheld ? '<span class="tag tag-accent-2">Right upheld</span>' : ''}</div>
            <h3>${esc(u.t)}</h3>
            ${u.text ? `<p class="rd-p-desk">${esc(u.text)}</p><details class="rd-p-mob"><summary>Details</summary><p>${esc(u.text)}</p>${src ? `<span class="rd-p-src">Source: ${src}</span>` : ''}</details>` : ''}
            ${src ? `<span class="rd-p-src rd-p-desk">Source: ${src}</span>` : ''}
            ${t.stat ? `<span class="rd-p-stat">${esc(t.stat)}</span>` : ''}
            ${t.focusUrl ? `<a class="rd-p-focus" href="${esc(t.focusUrl)}">${esc(t.focusLabel || 'Read the full story')} →</a>` : `<a class="rd-p-focus" href="${esc(t.page)}">Every update in this thread →</a>`}
            <div class="rd-p-nav"><button class="btn btn-ghost" data-act="prev"${step || (playAll && moved().indexOf(cur) > 0) ? '' : ' disabled'}>← Back</button>
              <button class="btn btn-secondary rd-p-fm" data-act="follow">${fol}</button>
              <button class="btn btn-primary" data-act="next">Next →</button></div>
          </div></div></div>`;
    if (!keep) startTimer();
  }

  // Stories-style autoplay (owner's request, 5 Nov 2026): each update shows for a few seconds (longer for longer
  // text), the current segment fills, then the player moves on by itself and closes after the last one.
  // Hold the card (or switch tabs) to pause; tap Next / Back, swipe or use the arrow keys to skip.
  let timer = null, t0 = 0, spent = 0, dur = 0, paused = false;
  function stopTimer() { if (timer) cancelAnimationFrame(timer); timer = null; }
  function startTimer() {
    stopTimer();
    const u = DATA.threads[cur].updates[step];
    const phone = window.matchMedia && matchMedia('(max-width: 720px)').matches;   // phones show the headline only
    const words = ((u.t || '') + ' ' + (phone ? '' : (u.text || ''))).split(/\s+/).length;
    dur = Math.min(12000, Math.max(5000, 3000 + words * 230)); spent = 0; t0 = performance.now(); paused = false;
    const tick = now => {
      if (!cur) return;
      const el = player.querySelector('.rd-p-segs i.cur b');
      const p = paused ? spent : spent + (now - t0);
      if (el) el.style.transform = `scaleX(${Math.min(1, p / dur)})`;
      if (p >= dur) { timer = null; return next(); }
      timer = requestAnimationFrame(tick);
    };
    timer = requestAnimationFrame(tick);
  }
  function pause() { if (!paused && cur) { spent += performance.now() - t0; paused = true; } }
  function resume() { if (paused && cur) { t0 = performance.now(); paused = false; } }
  player.addEventListener('pointerdown', e => { if (!e.target.closest('button, a, summary')) pause(); });
  ['pointerup', 'pointercancel', 'pointerleave'].forEach(ev => player.addEventListener(ev, resume));
  player.addEventListener('toggle', e => { if (e.target.matches && e.target.matches('.rd-p-mob')) (e.target.open ? pause : resume)(); }, true);
  document.addEventListener('visibilitychange', () => { document.hidden ? pause() : resume(); });

  function open(slug, all) {
    if (!DATA.threads[slug] || !DATA.threads[slug].updates.length) return;
    lastFocus = document.activeElement; cur = slug; step = 0; playAll = !!all;
    player.hidden = false; document.documentElement.classList.add('rd-noscroll');
    history.replaceState(null, '', '#t=' + slug);
    render(); player.querySelector('[data-act="next"]').focus();
  }
  function markSeen(slug) { seen[slug] = DATA.date; write(K.seen, seen); }
  function close(done) {
    stopTimer();
    if (cur) markSeen(cur);
    player.hidden = true; player.innerHTML = ''; cur = null;
    document.documentElement.classList.remove('rd-noscroll');
    history.replaceState(null, '', location.pathname + location.search);
    const cu = document.querySelector('[data-rd-caught-up]'); if (cu && done) cu.hidden = false;
    paintCards(); if (lastFocus) lastFocus.focus();
  }
  function next() {
    const t = DATA.threads[cur];
    // One thread opened: walk back through its recent updates. "Play today": only today's updates, then the next thread.
    if (step < t.updates.length - 1 && (!playAll || t.updates[step + 1].isNew)) { step++; return render(); }
    markSeen(cur);
    const mv = moved(), i = mv.indexOf(cur);
    if (playAll && mv[i + 1]) { cur = mv[i + 1]; step = 0; render(); return player.querySelector('[data-act="next"]').focus(); }
    close(playAll || mv.every(s => seen[s] === DATA.date));
  }
  function prev() {
    if (step > 0) { step--; return render(); }
    const mv = moved(), i = mv.indexOf(cur);                 // Play today: Back from a thread's first update goes to the previous thread
    if (playAll && i > 0) { cur = mv[i - 1]; step = 0; render(); }
  }

  player.addEventListener('click', e => {
    if (e.target === player) return close(false);           // backdrop
    const a = e.target.closest('[data-act]'); if (!a) return;
    ({ next, prev, close: () => close(false),
       follow: () => { follow.has(cur) ? follow.delete(cur) : follow.add(cur); saveFollow(); render(true); paintCards(); } })[a.dataset.act]();
  });
  document.addEventListener('keydown', e => {
    if (player.hidden) return;
    if (e.key === 'ArrowRight') next(); else if (e.key === 'ArrowLeft') prev(); else if (e.key === 'Escape') close(false);
  });
  let x0 = null;                                              // swipe left / right
  player.addEventListener('touchstart', e => { x0 = e.touches[0].clientX; }, { passive: true });
  player.addEventListener('touchend', e => { if (x0 == null) return; const dx = e.changedTouches[0].clientX - x0; if (Math.abs(dx) > 50) (dx < 0 ? next : prev)(); x0 = null; });

  document.querySelectorAll('.rd-thread[data-thread]').forEach(el => el.addEventListener('click', e => {
    if (e.metaKey || e.ctrlKey || e.shiftKey || e.button === 1) return;   // modified clicks open the thread page
    if (!DATA.threads[el.dataset.thread] || !DATA.threads[el.dataset.thread].updates.length) return;
    e.preventDefault(); open(el.dataset.thread, false);
  }));
  document.querySelectorAll('[data-rd-play-all]').forEach(b => b.addEventListener('click', () => {
    const first = moved().find(s => seen[s] !== DATA.date) || moved()[0]; if (first) open(first, true);
  }));

  paintCards();
  const m = location.hash.match(/^#t=([\w-]+)/); if (m) open(m[1], false);
})();
