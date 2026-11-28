#!/usr/bin/env python3
"""Ajoute un épisode, ne garde que les plus récents et régénère feed.xml.
Usage : python3 tools/publish.py <fichier.mp3> <AAAA-MM-JJ> "<titre>" "<description>" [--trailer]
À lancer depuis la racine du dépôt (branche gh-pages)."""
import sys, os, json, shutil, subprocess, datetime, email.utils
from xml.sax.saxutils import escape

BASE = "https://bnbfbfcxhj-hash.github.io/matinale-nautilus"
KEEP = 14
SHOW_TITLE = "La Matinale du Nautilus"
SHOW_DESC = ("Chaque matin, Jules et le capitaine Nemo font le tour de ce qui compte : le monde, la France, "
             "les marchés, la tech, le sport, une rubrique pour apprendre quelque chose et un texte à méditer. "
             "Podcast privé, voix de synthèse.")

def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                         capture_output=True, text=True).stdout.strip()
    return int(float(out)) if out else 0

def main():
    args = [a for a in sys.argv[1:] if a != "--trailer"]
    trailer = "--trailer" in sys.argv
    db_path = "episodes.json"
    eps = json.load(open(db_path, encoding="utf-8")) if os.path.exists(db_path) else []
    if args:
        src, date, title, desc = args[0], args[1], args[2], args[3]
        name = "La-Matinale-du-Nautilus-" + ("bande-annonce" if trailer else date) + ".mp3"
        dst = os.path.join("episodes", name)
        os.makedirs("episodes", exist_ok=True)
        if os.path.abspath(src) != os.path.abspath(dst):
            shutil.copyfile(src, dst)
        eps = [e for e in eps if e["file"] != name]
        eps.append({"file": name, "date": date, "title": title, "description": desc,
                    "seconds": duration(dst), "bytes": os.path.getsize(dst), "trailer": trailer})
    eps.sort(key=lambda e: (e["date"], not e.get("trailer", False)), reverse=True)
    regular = [e for e in eps if not e.get("trailer")]
    for old in regular[KEEP:]:
        p = os.path.join("episodes", old["file"])
        if os.path.exists(p):
            os.remove(p)
    eps = [e for e in eps if e.get("trailer") or e in regular[:KEEP]]
    json.dump(eps, open(db_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    items = []
    for e in eps:
        y, m, d = map(int, e["date"].split("-"))
        pub = email.utils.format_datetime(datetime.datetime(y, m, d, 6, 0, tzinfo=datetime.timezone.utc))
        s = e["seconds"]
        url = f"{BASE}/episodes/{e['file']}"
        items.append(f"""  <item>
   <title>{escape(e['title'])}</title>
   <description>{escape(e['description'])}</description>
   <itunes:summary>{escape(e['description'])}</itunes:summary>
   <guid isPermaLink="false">matinale-nautilus-{escape(e['file'])}</guid>
   <pubDate>{pub}</pubDate>
   <enclosure url="{url}" length="{e['bytes']}" type="audio/mpeg"/>
   <itunes:duration>{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}</itunes:duration>
   <itunes:episodeType>{'trailer' if e.get('trailer') else 'full'}</itunes:episodeType>
   <itunes:explicit>false</itunes:explicit>
  </item>""")
    now = email.utils.format_datetime(datetime.datetime.now(datetime.timezone.utc))
    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" xmlns:atom="http://www.w3.org/2005/Atom">
 <channel>
  <title>{SHOW_TITLE}</title>
  <link>{BASE}/</link>
  <atom:link href="{BASE}/feed.xml" rel="self" type="application/rss+xml"/>
  <language>fr</language>
  <description>{escape(SHOW_DESC)}</description>
  <itunes:summary>{escape(SHOW_DESC)}</itunes:summary>
  <itunes:author>{SHOW_TITLE}</itunes:author>
  <itunes:owner><itunes:name>{SHOW_TITLE}</itunes:name></itunes:owner>
  <itunes:image href="{BASE}/cover.jpg"/>
  <image><url>{BASE}/cover.jpg</url><title>{SHOW_TITLE}</title><link>{BASE}/</link></image>
  <itunes:category text="News"><itunes:category text="Daily News"/></itunes:category>
  <itunes:explicit>false</itunes:explicit>
  <itunes:type>episodic</itunes:type>
  <itunes:block>yes</itunes:block>
  <lastBuildDate>{now}</lastBuildDate>
{chr(10).join(items)}
 </channel>
</rss>
"""
    open("feed.xml", "w", encoding="utf-8").write(feed)
    print(f"{len(eps)} épisode(s) dans le flux")

if __name__ == "__main__":
    main()
