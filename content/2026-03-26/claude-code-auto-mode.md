---
title: "Claude Code Auto Mode: AI-Agent mit eingebauten Sicherheitsschranken"
date: 2026-03-24
source: Simon Willison
source_url: https://simonwillison.net/2026/Mar/24/auto-mode-for-claude-code/
type: blog
tags: [anthropic, claude, agents, safety, developer-tools]
---

## Kernaussagen
- Anthropic launcht "Auto Mode" fuer Claude Code — AI trifft selbst Entscheidungen, mit Safeguards
- Ein separates Classifier-Modell (Sonnet 4.6) prueft JEDE Aktion bevor sie ausgefuehrt wird
- Blockiert: Scope-Eskalation, unbekannte Infrastruktur, feindliche Inhalte in Dateien
- Detaillierte Allow/Deny-Listen: Test-Artifacts erlaubt, Git Force-Push blockiert, Dependencies nur aus Manifest

## Relevanz fuer Marketing
Zeigt wohin AI-Tools sich entwickeln: Vom "Ich frage, AI antwortet" zum "AI handelt eigenstaendig mit Sicherheitsnetz". Fuer Marketing-Teams die AI-Agents einsetzen wollen, ist das die Blaupause: Autonomie + Kontrolle. Nicht blindes Vertrauen, sondern definierte Grenzen.

## Post-Idee
Hook: "Der groesste Fehler bei AI-Automation? Alles oder nichts."
Angle: Anthropics neuer Ansatz zeigt wie es richtig geht — nicht "AI darf alles" oder "AI darf nichts", sondern granulare Kontrolle. Uebertragbar auf Marketing: Welche Aufgaben kann AI autonom erledigen? Wo braucht es einen Menschen? Framework fuer Marketing-Entscheider.
