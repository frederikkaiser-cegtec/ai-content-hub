# AI Content Hub

## Workflow: "update content hub"

Wenn der User "update content hub", "/content linkedin" oder aehnliches sagt, fuehre diesen Workflow aus:

### Schritt 1: Crawl
```bash
cd /c/Users/frede/Projects/ai-content-hub
rm -f scripts/last_crawl.json
python scripts/crawl_rss.py
python scripts/crawl_youtube.py
```

### Schritt 2: Analyse & Filterung
- Lies `scripts/raw/rss_raw.json` und `scripts/raw/youtube_raw.json`
- Filtere nur Artikel die relevant sind fuer: AI + Marketing, AI-Friendliness, Agents, Content-Strategie, B2B Growth, AI Search
- **Major Model Releases immer durchlassen** — neue Versionen von Claude, GPT, Gemini, Llama, Mistral, Grok, DeepSeek auch ohne Marketing-Tag. Hook/Angle dann auf "was bedeutet das fuer GTM/Outbound" framen, nicht reines Tech-Reblog.
- Ignoriere: Hardware-News, reine Dev-Tools ohne Business-Bezug, Off-Topic (Lifestyle, Politik), Satire
- Pruefe welche Artikel bereits in `content/` existieren (keine Duplikate)

### Schritt 3: Content generieren
Fuer jeden relevanten Artikel erstelle eine Markdown-Datei in `content/YYYY-MM-DD/`:

```markdown
---
title: "Deutscher Titel mit Marketing-Bezug"
date: YYYY-MM-DD
source: Quellenname
source_url: https://...
type: blog | youtube
tags: [relevante, tags]
---

## Kernaussagen
- 3-5 Bullet Points

## Relevanz fuer Marketing
1-2 Saetze warum das fuer B2B-Marketing relevant ist.

## Post-Idee
Hook + Angle fuer LinkedIn Post (Persona: Frederik Kaiser, B2B Marketing + KI Stratege)
```

### Schritt 4: Feed & Push
```bash
python scripts/generate_feed.py     # erzeugt feed.xml + index.json
git add content/ feed.xml index.json
git commit -m "content: [Anzahl] neue Summaries — [Themen-Stichworte]"
git push origin main
```

`index.json` ist die Konsumenten-API fuer `/content vorschlaege` (full-body, kein 500-char-Truncate wie in feed.xml). Beide werden via GitHub Pages unter `https://frederikkaiser-cegtec.github.io/ai-content-hub/{feed.xml,index.json}` ausgeliefert.

### Schritt 5: Summary
Zeige eine Tabelle der neuen Eintraege mit Thema, Quelle und Post-Angle.

## Quellen-Config
Alle Quellen sind in `scripts/config.yaml` definiert. Neue Quellen dort hinzufuegen.

## LinkedIn Persona
- Name: Frederik Kaiser
- Rolle: Marketing- & KI-Stratege
- Ton: strategisch-pragmatisch, deutsch, Du-Form
- Keine CegTec-Erwaehnung
- Konkrete Zahlen und KPIs wenn moeglich
- Hook muss in Zeile 1 zum Stoppen bringen
