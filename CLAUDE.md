# Regeln für den Kartenbau (16×16 Top-Down, Handheld-RPG-Stil)

Diese Regeln gelten für **jede** Karte und jedes Tileset in diesem Repository. Vor dem Abschluss einer Karte
wird jede Regel einzeln geprüft.

## Grundregeln des Nutzers

1. **Raster:** Alles wird an einem 16×16-Raster angeordnet.
   - 1b. Wenn es geht, immer mittig: Objekt im kleinsten Kachelblock, waagerecht zentriert, Fuß bündig auf der
     unteren Kachelkante.
2. **Treppen und Übergänge** werden immer **3× kontrolliert und verbessert** (vergrößert ansehen, Pixel für Pixel:
   Anschluss oben/unten, Wangen, Kanten, Weg passt genau zur Treppe, keine Lücken oder Fremdpixel).
3. **Wiederverwenden zuerst:** Erst prüfen, ob Objekte aus anderen Karten passen (`assets/objekte/karte0X/`).
   - 3b. Sind zu wenige vorhanden, werden neue generiert (PixelLab, `tools/pixellab_objekte.py`).
4. **Sockel / Kollision:** Objekte, die über 16×16 hinausgehen (Bäume, Säulen, Steine …), haben in der untersten
   Kachelreihe meistens einen Sockel → dort kann der Spieler **nicht** drüber laufen. Den oberen Bereich kann er
   durchlaufen, weil die Kachel ihn verdeckt (Überlagerungs-Ebene).
5. **Einzeln platzierte Bäume** brauchen Begleitung:
   - 5a. einen anderen Baum sowie 1–2 zur Karte passende Objekte, vorzugsweise zwei Kacheln hoch, so dass eines
     den Sockel des Baums überdeckt, **oder**
   - 5b. 2–3 Objekte, die dieser Regel folgen.
   - 5c. Gibt es zu wenig Variation, dürfen neue Objekte erstellt werden – gern auch gleich für andere
     Kartentypen (Gras, Stein, Wüste, Schnee …).
6. **Wege** gehen nie nur gerade und müssen nicht durchgängig sein: diagonal erlaubt, natürliche Bögen, ein Weg
   darf auch einmal unterbrechen und später weitergehen.
7. **Schatten** ragen nie über Kanten (Klippen, Wände, Wasser) oder über andere Objekte.
8. **Bäume überlappen sich nur an den äußeren Kachelspalten:** *(vorerst NICHT anwenden – der Nutzer hat die
   Baum-Änderungen auf Karte 01 und 05 verworfen; Bäume bleiben wie in der jeweiligen Vorlage/v1.0)*
   - Ein Baum, der 3 oder mehr Kacheln breit ist, darf einen Nachbarbaum nur mit seiner äußersten Spalte links
     bzw. rechts überlappen – die inneren Spalten bleiben frei.
   - Ein Baum, der 1–2 Kacheln breit ist, überlappt gar nicht – solche Bäume stehen nebeneinander.
   - Ausnahme dichter Wald: Dort dürfen sich Bäume mit bis zu **zwei** äußeren Spalten je Seite überlappen;
     mindestens eine Spalte jedes Baums bleibt frei.
   - Die Sockelregel (4) gilt auch hier: Sockel (unterste Kachelreihe) zweier Bäume überlappen nie.

## Abschlusskontrolle (Pflicht)

Wenn eine Karte fertig scheint: noch einmal komplett auf **Pixelfehler** und **Logikfehler** prüfen
(vergrößerte Ausschnitte ansehen, nicht nur die Gesamtansicht).

- **Physik/Realismus:** Es gelten reale Bedingungen. Beispiel: Ein Fels, der zwei Ebenen unter Wasser steht und
  über die Oberfläche ragt, kann nicht gleich groß aussehen wie derselbe Fels, der nur eine Ebene unter Wasser
  steht. Höhen, Wasserstände, Licht und Schatten müssen zueinander passen.
- **Zeichenreihenfolge (Ebenen-Logik):** Jeder Effekt, der über eine Fläche gezeichnet wird (Schaum, Brandung,
  Wellen, Lichtreflexe, Nebel, Schnee, Partikel), darf nur das überdecken, was physikalisch darunter liegt. Was
  aus dem Wasser, Nebel oder Schnee herausragt (Felsspitzen, Pfähle, Stege, Pflanzen, Objekte), liegt immer
  darüber. Pflicht-Kontrolle: nach jedem neuen oder geänderten Effekt alle Stellen, an denen er auf Felsen oder
  Objekte trifft, vergrößert ansehen – im Standbild **und** in mindestens drei Animationsbildern (Effekte wandern).
- **Verdeckung durch Höhen:** Ein Objekt auf tieferem Boden ragt nie über ein seitlich daneben liegendes, höheres
  Plateau – der Berg steht davor und schneidet das Objekt ab. Nur wenn die Klippe hinter dem Objekt liegt (Norden),
  darf es vor der Wand stehen.

## Bewährte Regeln aus den bisherigen Runden

- **Ansicht frontal:** Objekte frontal von vorne, nicht diagonal/isometrisch (PixelLab-Prompt mit dem
  Frontal-Zusatz „perfectly straight front elevation view …“).
- **Licht** kommt von oben links; Schatten nur auf dem Boden.
- **Keine Überlappungen:** Objekte berühren sich nicht ungewollt (Pixelprüfung mit 2 px Abstand). Gewollte
  Überdeckung nur bei Begleitobjekten vor einem Sockel (Regel 5).
- **Wandregel:** Die untersten zwei Kachelreihen eines Objekts liegen nie auf einer Felswand oder Kante. Obere
  Reihen dürfen vor die Wand ragen.
- **Einbettung:** Bäume, Felsen, Kristalle usw. bekommen Büschel/Blumen an den Sockelecken, damit sie im Boden
  sitzen. Im Schnee Schnee-Varianten verwenden.
- **Animation:** Nur, was sich wirklich bewegt (Wasser, Feuer, Pflanzen im Wind, Leuchten). Keine Steine oder
  Steinflächen animieren. Discord-GIF unter 10 MB (sonst 8 statt 16 Bilder).
- **Wehen nur am beweglichen Teil:** Ist etwas wehend animiert (z. B. eine Flagge, ein Banner, ein Tuch), bewegt
  sich nur der Stoff – nie das Objekt, an dem er befestigt ist (Mast, Stange, Ständer aus Holz, Metall o. Ä.
  bleibt völlig ruhig). Also nicht das ganze Sprite verbiegen, sondern nur die Stoffpixel animieren.
- **Tilesets:** Statisches Tileset mit allem; animiertes Tileset nur mit den animierten Teilen **am exakt selben
  Platz**. Sauber nach Gruppen geordnet (wie klassische Handheld-Tilesets: Fläche, Ränder, Innenecken, Objekte).
  Boden-Übergänge als kombinierbare Ecken-Kacheln mit sauberen, runden Kanten.
- **Wasser folgt der Physik:** Wasserfälle nie einfach an eine Wand setzen – oben braucht es eine Quelle (Teich/Bach),
  unten einen Abfluss (Bach, See). Kreuzt ein Bach einen Weg, kommt eine Brücke hin.
- **Seitliche Plateaukanten:** Senkrechte (seitliche) Kanten von Plateaus nur als schmale Abgrenzung (Kontur +
  leichter Schatten), keine sichtbare Seitenwand aus Kacheln. Fronten (Süden) bleiben echte Klippen.
- **Liegende Objekte werfen flache Schatten:** Äste, Knochen u. Ä. werfen den Schatten über ihre ganze Form (leicht
  nach rechts unten versetzt), nicht wie stehende Objekte nur vom Fußpunkt aus.
- **Keine Reihen:** Deko nie in Reihen nebeneinander – unregelmäßig, mit Abständen, eher etwas weniger Kleinkram.
- **Große Objekte zuerst:** Erst große Bäume, Server, Kristalle usw. setzen, dann Kleinkram in die Lücken – sonst ist
  kein Platz mehr für Großes. Bei Bäumen müssen nur die unteren zwei Reihen auf passendem Boden stehen.
- **Baumarten der Karte verwenden:** Neue Baumarten nur, wenn sie zum Stil der Karte passen; vorhandene Schneebäume
  einer Schneekarte haben Vorrang vor umgefärbten Bäumen anderer Karten.
- **Bestehendes verbessern statt ersetzen:** Gefällt ein Objekt grundsätzlich und hat nur Fehler (z. B. unsaubere
  Kanten), wird es repariert – nicht gegen ein anderes ausgetauscht.
- **Übergänge an Bauwerken in der Wand:** Höhlen, Tore u. Ä. in einer Klippe bekommen links/rechts einen Baum oder
  Busch als Übergang zur Wand.
- **Vorschau zuerst:** Änderungen erst als Vorschau-Bild (Ausschnitt) zeigen; GIF und ZIP erst, wenn der Nutzer
  zufrieden ist.
- **Ablauf:** Jede Änderung committen und pushen, Bilder/GIFs an den Nutzer schicken, auf Deutsch erklären.
