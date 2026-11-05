#!/usr/bin/env python3
"""following/index.html: the threads this reader follows (owner's request, 5 Nov 2026).

Follows live only in the reader's browser (localStorage "rd.follow"; no accounts, nothing leaves the device), so this page
is the same static file for everyone: it lists every thread (photo, name, latest update and its date) and the inline
script shows only the followed ones. Threads that moved since the reader last saw them get a "New" tag and come first;
quiet ones are greyed with the date of their last update. Tapping a card plays the thread in the story player (assets/rd.js).
With no follows, the page shows the threads as chips to follow with one tap. publish.py builds it every day.

Usage (from the repo root): python3 tools/following.py [YYYY-MM-DD]   (default: latest edition)
"""
import os, sys, json, html, datetime
import rdsite as S
import threads as T

E = html.escape
root = S.root


def build(date=None):
    date = date or S.editions()[-1]
    prefix = "../"
    ups = T.all_updates(date)
    reg = T.registry()
    rows, chips = [], []
    for t in reg:
        u = ups.get(t["slug"], [])
        last = u[0] if u else None
        p = T.photo_of(t, u[:6])
        ring = f'<img class="washed" src="{E(S.rel(p["src"], prefix))}" alt="" loading="lazy" decoding="async">' if p else "<i></i>"
        when = last["date"] if last else ""
        quiet = when != date
        line = E(last["t"]) if last else "No updates yet"
        d = E(last["d"]) if last else ""
        rows.append(
            f'<div class="rd-frow" data-slug="{E(t["slug"])}" data-last="{E(when)}" hidden>'
            f'<a class="rd-thread{" is-quiet" if quiet else ""}" data-thread="{E(t["slug"])}" href="{T.link(t, prefix)}">'
            f'<span class="rd-ring">{ring}</span><span class="rd-tx"><span class="rd-tx-top"><h3>{E(t["name"])}</h3>'
            f'<span class="tag tag-accent rd-new" hidden>New</span></span><p>{line}</p><span class="rd-fdate">{d}</span></span></a>'
            f'<button type="button" class="rd-unf" data-rd-follow="{E(t["slug"])}" data-on="Following ✓" data-off="Follow">Following ✓</button></div>')
        chips.append(f'<button type="button" class="rd-chip" data-rd-follow="{E(t["slug"])}" data-on="✓ {E(t["name"])}" data-off="+ {E(t["name"])}">+ {E(t["name"])}</button>')
    pdata = {"date": date, "order": [t["slug"] for t in reg], "threads": T.player_data(date, prefix, ups)}
    body = (S.nav(prefix)
            + '<header><h1 class="rd-fh">Following</h1></header>'
            + f'<section class="rd-flist" data-rd-flist>{"".join(rows)}</section>'
            + '<section class="rd-fempty" data-rd-fempty hidden><p>Follow a thread to keep it here.</p>'
            + f'<div class="rd-chips">{"".join(chips)}</div></section>'
            + '<script type="application/json" id="rd-threads">' + json.dumps(pdata, ensure_ascii=False).replace("</", "<\\/") + '</script>'
            + """<script>
(function(){
  var read=function(k,d){try{var v=JSON.parse(localStorage.getItem(k));return v==null?d:v}catch(e){return d}};
  var follow=read('rd.follow',[]), seen=read('rd.seen',{});
  var list=document.querySelector('[data-rd-flist]'), empty=document.querySelector('[data-rd-fempty]');
  var rows=[].slice.call(list.querySelectorAll('.rd-frow'));
  rows.forEach(function(r){
    var s=r.dataset.slug, last=r.dataset.last, isNew=!!last && (!seen[s] || seen[s] < last);
    r.dataset.new=isNew?'1':''; r.querySelector('.rd-new').hidden=!isNew;
    r.hidden=follow.indexOf(s)<0;
  });
  rows.sort(function(a,b){return (b.dataset.new>a.dataset.new)-(b.dataset.new<a.dataset.new) || (b.dataset.last>a.dataset.last)-(b.dataset.last<a.dataset.last)})
      .forEach(function(r){list.appendChild(r)});
  empty.hidden=follow.length>0;
  // Unfollowing greys the card but keeps it until the next visit, so a slip can be undone.
  document.addEventListener('click',function(e){
    var b=e.target.closest('[data-rd-follow]'); if(!b) return;
    setTimeout(function(){
      var f=read('rd.follow',[]), s=b.dataset.rdFollow, r=list.querySelector('.rd-frow[data-slug="'+s+'"]');
      if(r){ if(f.indexOf(s)>=0) r.hidden=false; r.classList.toggle('is-off', f.indexOf(s)<0); }
    },0);
  });
})();
</script>""")
    page = S.head("Following · Resistance Daily", "The Resistance Daily threads you follow. Stored only on your device.",
                  prefix, f"{S.SITE}following/", "", noindex=True) + body + S.footer(prefix)
    os.makedirs(os.path.join(root, "following"), exist_ok=True)
    open(os.path.join(root, "following", "index.html"), "w").write(page)


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else None)
    print("built following/index.html")
