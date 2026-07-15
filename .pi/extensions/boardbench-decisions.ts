import { mkdir, writeFile } from "node:fs/promises";
import { join } from "node:path";

import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

type Question = { id: string; title: string; options: string[] };

const questions: Question[] = [
  {
    id: "thesis_focus",
    title: "1/17 – Was ist der Hauptfokus der Arbeit?",
    options: [
      "Empfohlen: Anleitungsdiagnose als Hauptziel; Modell- und Evaluatorfehler getrennt erklären",
      "Primär Qualität der generierten Implementierungen",
      "Primär Vergleich verschiedener LLMs",
      "Offen lassen",
    ],
  },
  {
    id: "result_unit",
    title: "2/17 – Was erhält am Ende ein eigenes Ergebnis?",
    options: [
      "Empfohlen: Jede Anleitung/Edition/Variante erhält eine eigene Ergebnis-Karte",
      "Nur jedes Spiel erhält ein gemeinsames Ergebnis",
      "Nur jede Modell-Anleitungs-Kombination erhält ein Ergebnis",
      "Offen lassen",
    ],
  },
  {
    id: "main_conditions",
    title: "3/17 – Welche Quellenbedingungen gehören in die Hauptstudie?",
    options: [
      "Empfohlen: Original + präzisiert je Spiel; Auslassung/falsch/vage nur als Kalibrierung",
      "Alle Varianten für jedes Spiel",
      "Nur Originalanleitungen",
      "Offen lassen",
    ],
  },
  {
    id: "repeats",
    title: "4/17 – Wie viele unabhängige Läufe pro Hauptbedingung?",
    options: [
      "Empfohlen: 3 Läufe; Mittelwert und Standardabweichung",
      "5 Läufe für stabilere Ergebnisse",
      "1 Lauf, dafür mehr Spiele",
      "Adaptiv: mindestens 3, bei hoher Streuung 5",
      "Offen lassen",
    ],
  },
  {
    id: "games",
    title: "5/17 – Welche Spielauswahl ist realistisch?",
    options: [
      "Empfohlen: 3 Spiele – Karten/Zufall, abstrakte Strategie, mittlere Komplexität",
      "2 Spiele sehr tief untersuchen",
      "4–5 Spiele mit weniger Szenarien",
      "Bestehende Spiele Exploding Kittens + Abalone + Havannah",
      "Offen lassen",
    ],
  },
  {
    id: "model_protocol",
    title: "6/17 – Modell und Protokoll der Hauptstudie?",
    options: [
      "Empfohlen: ein festes Modell, gpt-5.6-sol:medium, agentic-v2.1",
      "gpt-5.6-sol:low zur Kostenreduktion",
      "Zwei Modelle als zusätzlicher Faktor",
      "Offen lassen",
    ],
  },
  {
    id: "judge_design",
    title: "7/17 – Wie sollen Judges eingesetzt werden?",
    options: [
      "Empfohlen: 3 neutrale blinde Judges für den Hauptwert; Personas separat",
      "Nur drei neutrale Judges",
      "Nur Persona-Judges",
      "Neutrale und Persona-Scores gemeinsam mitteln",
      "Offen lassen",
    ],
  },
  {
    id: "judge_personas",
    title: "8/17 – Welche zusätzlichen Judge-Perspektiven?",
    options: [
      "Empfohlen: Regelprüfer + Ambiguitätsprüfer + Executable-Systems-Prüfer",
      "Zusätzlich Evaluator-Skeptiker als vierte Persona",
      "Nur Ambiguitätsprüfer",
      "Keine Personas",
      "Offen lassen",
    ],
  },
  {
    id: "assumption_profile",
    title: "9/17 – Sollen angenommene Regeln ein eigenes Ergebnis sein?",
    options: [
      "Empfohlen: Ja, nur materiale Annahmen mit Quelle, Alternativen und Auswirkung berichten",
      "Ja, jede noch so kleine Annahme zählen",
      "Nur Annahmen erwähnen, aber nicht strukturiert auswerten",
      "Nein",
      "Offen lassen",
    ],
  },
  {
    id: "headline_score",
    title: "10/17 – Ein einzelner Gesamtscore?",
    options: [
      "Empfohlen: Nein; getrenntes Profil plus kurzer kategorischer Ergebnissatz",
      "Zusätzlich ein gewichteter Gesamtscore",
      "Nur ein Gesamtscore",
      "Offen lassen",
    ],
  },
  {
    id: "cost_report",
    title: "11/17 – Welche Kostenangaben pro Anleitung?",
    options: [
      "Empfohlen: Tokens, Providerzeit, Aufrufe, Reparaturen und Geld nur wenn verlässlich",
      "Nur monetäre Kosten",
      "Nur Tokens",
      "Keine Kosten im Hauptergebnis",
      "Offen lassen",
    ],
  },
  {
    id: "freeze_policy",
    title: "12/17 – Wann wird der Evaluator eingefroren?",
    options: [
      "Empfohlen: Nach Mutationstest und offenen EK-Fällen; danach keine Hauptdaten mehr ändern",
      "Jetzt mit v2.6 einfrieren",
      "Pro Spiel während der Hauptstudie weiterentwickeln",
      "Offen lassen",
    ],
  },
  {
    id: "input_format",
    title: "13/17 – Umgang mit PDF und TXT bei weiteren Spielen?",
    options: [
      "Empfohlen: natives Format kanonisch; faithful TXT nur als getrennte Formatbedingung",
      "Alle PDFs zuerst in TXT umwandeln und nur TXT verwenden",
      "Nur PDF verwenden",
      "Offen lassen",
    ],
  },
  {
    id: "clarification_form",
    title: "14/17 – Wie werden präzisierte Anleitungen erstellt?",
    options: [
      "Empfohlen: Original/faithful Text plus sichtbarer Anhang genehmigter Präzisierungen",
      "Gesamte Anleitung neu schreiben",
      "Nur separate rulefacts.md, keine präzisierte Anleitung",
      "Offen lassen",
    ],
  },
  {
    id: "nope_parameters",
    title: "15/17 – Müssen Ziel und gewünschte Karte vor dem NÖ!-Fenster feststehen?",
    options: [
      "Empfohlen: Ja, alle Aktionsparameter werden vor Reaktionen angekündigt",
      "Nein, Parameter werden erst nach erfolgreicher NÖ!-Phase gewählt",
      "Je nach Kartentyp unterschiedlich",
      "Als unklar sichtbar lassen und noch nicht hart testen",
    ],
  },
  {
    id: "preview_after_shuffle",
    title: "16/17 – Was geschieht mit Vorschauwissen nach Mischen?",
    options: [
      "Empfohlen: Gespeicherte Topkarten-Vorschau wird ungültig und nicht mehr als aktuell gezeigt",
      "Historische Vorschau darf sichtbar bleiben, muss aber als veraltet markiert sein",
      "Nicht modellieren oder testen",
      "Offen lassen",
    ],
  },
  {
    id: "reaction_empty_target",
    title: "17/17 – Ziel spielt während der NÖ!-Kette seine letzte Karte: Was passiert?",
    options: [
      "Empfohlen: Aktion war bei Ankündigung legal, löst danach aber ohne Transfer auf",
      "Aktion wird bei Auflösung illegal und vollständig rückgängig gemacht",
      "Das Ziel darf seine letzte Karte in dieser Reaktion nicht spielen",
      "Als unklar sichtbar lassen und noch nicht hart testen",
    ],
  },
  {
    id: "empty_deck_after_retrieval",
    title: "Zusatzfrage – Was gilt, wenn Kitten-Rücknahme später einen leeren Spielstapel ermöglicht?",
    options: [
      "Empfohlen: Als echte Spezifikationslücke berichten und bis zur Entscheidung nicht hart bewerten",
      "Ein leerer Stapel beendet das Spiel ohne Gewinner",
      "Kitten-Rücknahme verbieten, sobald dadurch die Karteninvariante brechen kann",
      "Ablagestapel neu mischen",
    ],
  },
];

export default function boardbenchDecisions(pi: ExtensionAPI) {
  pi.registerCommand("bbdecide", {
    description: "Answer the open BoardBench study decisions interactively",
    handler: async (_args, ctx) => {
      if (!ctx.hasUI) return;
      const answers: Record<string, string> = {};
      for (const question of questions) {
        const answer = await ctx.ui.select(question.title, question.options);
        if (answer === undefined) {
          ctx.ui.notify("Entscheidungsrunde abgebrochen; es wurde nichts gespeichert.", "info");
          return;
        }
        answers[question.id] = answer;
      }

      const directory = join(ctx.cwd, "meeting", "23.7");
      const capturedAt = new Date().toISOString();
      await mkdir(directory, { recursive: true });
      await writeFile(
        join(directory, "DECISIONS.json"),
        JSON.stringify({ captured_at: capturedAt, answers }, null, 2) + "\n",
        "utf8",
      );
      const text = [
        "Entscheidungen für die Hauptstudie",
        `Erfasst: ${capturedAt}`,
        "",
        ...questions.flatMap((question) => [
          question.title.replace(/^\d+\/17 – /, ""),
          `- ${answers[question.id]}`,
          "",
        ]),
      ].join("\n");
      await writeFile(join(directory, "DECISIONS.txt"), text, "utf8");
      ctx.ui.notify("Gespeichert: meeting/23.7/DECISIONS.txt und DECISIONS.json", "info");
    },
  });
}
