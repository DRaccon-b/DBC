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
   - 5d. **Begleiter am Stumpf** (gilt nur für Bäume in der Karte, nicht für den Waldrand):
     - **Vor dem Stumpf** nur Objekte, die **2 Kacheln hoch** sind (z. B. bemooste Felsen, Blumenbüsche). Sie stehen
       **eine Kachel tiefer** als der Baum, sodass nur ihre **oberste Kachel** den Stumpf überdeckt.
     - **Hinter den Blättern** dürfen Felsen eine Reihe höher stehen; die Krone verdeckt sie teilweise (sie werden
       vor dem Baum gezeichnet).
     - **Nichts auf Stammhöhe:** In der Stammreihe des Baums sowie direkt darüber und darunter (eine Kachel links und
       rechts daneben) wird keine freie Deko gesetzt – sonst liegt sie auf dem Stumpf.
     - Begleiter eines Baums überlappen sich nicht gegenseitig (Fels vor dem Stumpf → keine zusätzliche Eckblume).
     - Abwechseln statt überall gleich: mal Fels vor dem Stumpf, mal Fels hinter den Blättern, mal beides.
6. **Wege** gehen nie nur gerade und müssen nicht durchgängig sein: diagonal erlaubt, natürliche Bögen, ein Weg
   darf auch einmal unterbrechen und später weitergehen.
   - 6b. **Alle Bodenkanten in 45° (Nutzer, Karte 31; für alle Bodenarten erweitert):** Gilt nicht nur für Wege, sondern für
     jede Bodenkante (Gras, Sand, Erde, Platz, Wasser, Schlamm, Schnee …) – immer am 16er-Raster mit 45°-Schrägen
     (`karte04_bauen.RASTER45 = True`). Wege im Einzelnen: Der Verlauf eines Weges darf geschwungen sein, aber seine Ränder
     folgen dem Kachelraster mit **45°-Schrägen** an den Ecken (abgeschrägte Kachelstufen) – keine runden
     Freiform-Kurven. An Treppen läuft der Weg ebenfalls mit 45° auf die exakte Treppenbreite zu.
     Referenz, die der Nutzer „perfekt“ fand: `karte31_bauen.weg_rund` – Verlauf als Kurve auf Kacheln gerastert, die
     Kachelmaske (mit angrenzenden Plätzen/Treppen) mit Gauß 5 px weichgezeichnet und bei 50 % geschnitten.
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
  Steinflächen animieren. Discord-GIF unter 10 MB.
- **Höchstens 4 Animationsbilder (neue Regel ab Karte 15):** Jede Animation läuft mit maximal 4 Frames.
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
- **Verdeckung durch Bauwerke:** Wie bei Höhen: Mauern, Wände, Dächer und Fassaden eines Gebäudes stehen vor
  Objekten, die daneben auf dem Boden stehen, und schneiden sie ab.
- **Verdeckung nur, wo sie stimmt:** Objekte, deren Fuß am oder auf dem Plateau steht, und Waldränder werden nie
  abgeschnitten – sonst fehlen Kacheln am Rand von Bäumen.
- **Schatten bleiben auf ihrer Höhenebene:** Ein Schatten fällt nur auf die Ebene, auf der der Fuß des Objekts steht
  (Canyon, Boden, Plateau) – nie über Klippenwände, Canyonränder oder Plateaukanten.
- **Gleiche Objekte bündig ausrichten:** Zusammengehörige gleichartige Objekte (z. B. Reaktor-Pods untereinander)
  stehen auf derselben Höhe bzw. Flucht wie ihre Nachbarn.
- **Sprites auf Schnittkanten prüfen:** Gerade abgeschnittene Kronen- oder Objektkanten und lose Fremdpixel im Sprite
  selbst reparieren (rund ergänzen), nicht nur die Platzierung ändern.
- **Maschinen-Animation:** Laufende Maschinen: Rauch steigt genau aus den Rohröffnungen (in Windrichtung treibend),
  Lampen/Anzeigen pulsieren, das Gehäuse rüttelt leicht (1 px) – Füße und Kabel am Boden bleiben fest. Bei
  gespiegelten Objekten werden die Animationspunkte mitgespiegelt.
- **Gebäude mit Dach:** Häuser, Krypten, Kapellen u. Ä. nie flach als reine Fassade – Dachflächen und First von
  leicht oben sichtbar (wie die Häuser auf Karte 06).
- **Tore an Treppen:** Zweiflügelige Tore/Gitter werden geteilt: je ein Flügel links und rechts am Fuß der Treppe,
  Fuß auf Höhe des Treppenfußes, der Flügel ragt vor die Klippe, auf der die Treppe liegt.
- **Symmetrische Plätze:** Paare auf einem Platz vor einem Bauwerk (Statuen, Banner, Laternen, Säulen) stehen exakt
  spiegelsymmetrisch zur Achse des Bauwerks.
- **Gebäude stehen ganz auf Land:** Nicht nur der Fuß, sondern die ganze Fläche eines Gebäudes (auch Rückwand und
  Dach) liegt über Land, mit mindestens einer Kachel Strand bis zum Wasser. Gewollte Ausnahmen (Pavillon am Teich)
  werden ausdrücklich markiert.
- **Schatten beginnen direkt am Objekt:** Der Kontaktschatten liegt unmittelbar am Fuß. Alles, was nach dem Schatten
  am Fuß gezeichnet wird (Sandverwehung, Bodenfuß, Büschel), wird im Schatten mitschattiert – nie hell darübermalen.
- **Schatten folgen der Objektform:** Kein waagerechter Balken unter dem Objekt. Der Kontaktschatten folgt der echten
  Fußform (ohne Bodenfuß-Sandhügel), der Schlagschatten ist die Silhouette des Objekts, diagonal nach rechts unten
  gelegt und nur etwa auf die Hälfte gestaucht, sodass Arme, Kronen und Pfosten erkennbar bleiben.
- **Hinter Gebäuden:** Objekte, die bewusst hinter einem Gebäude stehen (z. B. Palmen), werden ausdrücklich als
  „dahinter“ markiert und immer vor dem Gebäude gezeichnet – auch wenn sie nach dem Einrasten auf derselben Reihe stehen.
- **Offene Durchgänge:** Tore, Bögen und Portale ohne Tür haben einen transparenten Durchgang – Boden und Teppich laufen
  sichtbar hindurch, nie eine dunkle Fläche.
- **Achsen in Räumen:** Bauwerke auf einer Raum- oder Teppichachse (Tore, Portal, Orgel, Altar, Teppich-Medaillon) stehen
  exakt auf der Mitte des Teppichs bzw. Rahmens. Das geht vor Regel 1b; Paare werden an derselben Achse gespiegelt.
- **Fester Rhythmus:** Wiederkehrende Bauteile (Türme, Banner, Wandpfeiler) stehen in gleichen Abständen, symmetrisch zum
  Tor; Banner mittig zwischen den Türmen, Pfeiler im selben Raster.
  Wandpfeiler liegen symmetrisch zur Achse der jeweiligen Wand bzw. des Raums; jedes Fenster/Banner hängt mittig in einem
  Feld zwischen zwei Pfeilern (nie auf einem Pfeiler), gleichartige Wandobjekte auf exakt derselben Höhe (Karte 32).
- **Wandobjekte hängen frei:** Fenster, Banner, Bilder und Fackeln in Originalgröße auf der Wandfläche – mit Abstand zur
  Mauerkrone, Unterkante über der Leiste, ohne Bodenwall und ohne Bodenschatten.
- **Räume mit Funktion:** Innenräume bekommen eine erkennbare Aufgabe (Bibliothek, Thron, Speisesaal, Ritualsaal) statt
  gleichförmiger Säulenreihen; Kleinkram liegt nie auf oder direkt neben Teppichen.
- **Kein Sprite mit eingebautem Hintergrund** (Mauerstück, Kacheln) frei auf den Boden stellen.
- **Feuer und Licht animieren:** Alles mit Flamme, Glut oder Leuchten wird animiert; bei Feuer bewegen sich die Flammen
  selbst (züngeln, strecken sich), nicht nur die Helligkeit. Portale drehen ihren Wirbel. Nach dem GIF-Export prüfen,
  dass sich jedes animierte Objekt im GIF tatsächlich bewegt.
- **Schaukeln statt Verbiegen:** Wipptiere, Schaukeln, Ballons u. Ä. kippen als Ganzes um ihren festen Drehpunkt
  (Feder, Kette, Knoten) – das Sprite wird nie verbogen oder geschert.
- **Leuchten nur bei echten Lichtquellen:** Lampen, Feuer, Kristalle leuchten; Uhren, Zifferblätter, helle Wände nie.
  Bei Teil-Animationen (Uhrzeiger, Glocke …) nur genau dieses Teil verändern, nichts drumherum aufhellen.
- **Geschützte Designs nicht kopieren:** Anspielungen (z. B. auf die Digiritter) über Farben, Anzahl und Anordnung –
  nie über originalgetreue Wappen, Logos oder Symbole.
- **PixelLab nur Objekt-Creator:** Neue Objekte ausschließlich mit dem Objekt-Creator (`create-1-direction-object`,
  höchstens 256 px) erzeugen – nicht mit dem Pro-Generator (`generate-image-v2`) oder Pixflux für größere Bilder.
  - **Ausnahme (Nutzer, Karte 25):** Objekte, die zwingend größer als 256 px sind (z. B. das Schiff in Sunset Bay), dürfen
    mit dem Pro-Generator erzeugt werden (`tools/pixellab_gross.py`): Vorlagenausschnitt als Subjekt-Referenz (geschützte
    Symbole vorher übermalt), ein vorhandenes Kartenobjekt als Stil-Referenz, danach mitgezeichnete Fremdteile entfernen.
- **Gebäude vollständig:** Generierte Gebäude müssen ganz im Bild sein – Dach mit allen Ecken, beide Seitenwände,
  Sockel; nichts abgeschnitten (mit Rand generieren). Passt ein gutes Gebäude nicht auf seine Fläche, wird die Karte
  an das Gebäude angepasst (Fläche, Straßen verschieben) – nicht das Gebäude beschnitten oder geflickt.
- **Deko-Flächen mit Abstand:** Sandflecken, Erdflecken u. Ä. um Objekte (z. B. Sand um Palmen auf Rasen) berühren nie
  Straßen- oder Gehwegkacheln; sie bleiben mit einigen Pixeln Abstand auf ihrer Fläche.
- **Nichts auf Wegen:** Objekte stehen nie mit dem Fuß auf Weg- oder Pflasterkacheln (Prüfung beim Setzen). Ausnahmen:
  Brunnen u. Ä. mitten auf Plätzen, flaches Laub.
- **Generierte Sprites umfärben:** Liefert PixelLab Farben, die nicht zur Karte passen, werden Stein/Dach/Holz auf die
  Palette der Karte bzw. eines vorhandenen Vorbild-Objekts umgefärbt (Helligkeit -> Vorbildfarbe, Karte 32: Turm,
  Säulen). Leuchtende Teile, Fenster und Stoff behalten ihre Farbe.
- **Mauern massiv:** Jede Mauer hat oben eine Abdeckung (Deckplatten mit Licht-/Schattenkante) und davor eine Wand mit
  Schattenfuge unter der Abdeckung, Fußkante und Bodenschatten. Die Abdeckung ist überall gleich breit – auch an Stufen.
- **Durchgänge passend:** Mauerdurchgang, Weg/Steg und Teppich sind gleich breit und liegen auf derselben Achse.
- **Mitte exakt bestimmen:** Bei runden oder symmetrischen Plätzen/Arenen die Achse aus der Fläche berechnen (notfalls
  auf der Kachelkante); Ring, Mitte, Runen u. Ä. sitzen exakt darauf (gespiegelt am Klassenraster prüfen).
- **Keine Wiederholung:** Gleiche Deko-Motive nie nebeneinander; Streudeko ohne Wiederholung ziehen, solange der Vorrat
  reicht.
- **Kleinkram dezent:** Lieber verstreutes Laub, Blütenblätter, Zweige und wenige Büschel als volle Flächen. Kleine
  Pflanzen werfen nur einen Kontaktschatten.
- **Ruinen-Logik:** In zerfallenen Orten werden Säulen, Leuchter u. Ä. reduziert und liegen kaputt am Boden (umgestürzt,
  abgebrochen) statt intakt in Reihen.
- **Teleporter- und Spawnfelder frei:** Im Umkreis (inkl. flankierender Objekte) keine Streudeko.
- **Schwebende Objekte:** Kein Bodenschatten, 1 px Auf-und-ab mit eigenem Takt, Abstand zu Plattformen und Rissen;
  surreale Wirkung über Motive, Schimmer und Nachbild.
- **Blicke in andere Karten:** Risse/Fenster in andere Karten zeigen Ausschnitte im selben Maßstab aus der echten Karte
  und sind aus deren Animation animiert; die Risskante liegt am 45°-Raster (wie Regel 6b).
- **Unklares erst fragen:** Bei mehrdeutigen Wünschen kurz nachfragen (z. B. welche Variante gemeint ist), sonst ohne
  Zögern umsetzen.
- **Ablauf:** Jede Änderung committen und pushen, Bilder/GIFs an den Nutzer schicken, auf Deutsch erklären.

## Prüfliste: häufige Fehler (aus Nutzer-Korrekturen und der Agenten-Gesamtprüfung)

Vor jeder Abgabe Punkt für Punkt prüfen (vergrößert, Standbild und mehrere Animationsbilder):

- **Weg ↔ Treppe/Brücke:** Weg läuft in voller Treppen-/Brückenbreite an (je 2 Reihen davor und danach), ohne Gras-
  streifen am Brückenende; keine Kerbe in der Plateaukante über der Treppe (ganze Treppenbreite auf Plateauhöhe, Front
  links/rechts 2 Kacheln gerade weiter). Wege in Senken/Terrassen haben an jeder Stufenkante eine Treppe in Wegbreite.
- **Einzelkacheln:** keine Ein-Kachel-Inseln oder -Löcher (Wasser, Moor, Sandfleck, Tiefenstufe) – sie werden durch das
  45°-Raster zu runden Punkten. Mindestens 2–3 Kacheln oder an die Nachbarn angleichen.
- **Kartenrand:** Abstands-/Weichzeichner-Berechnungen nie über den Rand laufen lassen (kein `np.roll`, Rand
  fortsetzen) – sonst Schaum/Ufer gegenüber am anderen Rand.
- **Objekte:** nichts auf Pflaster/Weg/Mauerkrone/Klippenkante; keine Überlappung (Schild↔Feuerstelle, Wagen↔Scheune,
  Laterne↔Silo, Netz↔Netz, Stein auf Obelisk); Waldbäume/Felsnadeln nie über Teleportern; Waldrand nie vor Fassaden;
  keine Laternen in Riesenrad/Gebäuden; Autos in Fahrtrichtung; Kronen nicht am Kartenrand abgeschnitten.
- **Platzierung pixelgenau (Karte 34):** Freie Objekte gegen die echten Bildrechtecke aller gesetzten Objekte prüfen
  (2 px Abstand, auch über verschiedene Deko-Listen hinweg), nicht nur die Fußkachel; Bänke/Möbel mit allen Fußkacheln
  neben dem Weg; Waldrand **nach** Bäumen/Möbeln setzen, nie über deren Fuß oder Teleporter, Lücken im Waldrand mit
  Büschen schließen (kein nackter Waldboden); Streudeko erst danach, nie unter Waldkronen.
- **Platzmitte und Möbel (Nutzer, Karte 34):** Brunnen, Denkmäler u. Ä. stehen exakt auf der aus der Platzfläche
  berechneten Mitte (nicht auf der Vorlagenkachel); Bänke sparsam – höchstens eine je Ort bzw. ein gespiegeltes Paar am
  Platzobjekt, nie viele Bänke verteilt.
- **Stadt (Karte 35):** Fahrtrichtung je Sprite an Front/Scheinwerfern prüfen, nicht an der Spiegel-Annahme (Bus und
  Autos können unterschiedlich gezeichnet sein; Linksverkehr); Laternen/Möbel nie im Austritt von Treppen und Brücken
  (2 Reihen frei); Leuchtschein mit `licht`/`licht_box`/`licht_r` nur am Lampenkopf bzw. Warenfenster; gewollte
  Begleiter (Busch an der Stammecke) ohne 2-px-Prüfung gegen den eigenen Baum setzen und ihr Setzen kontrollieren;
  abgeschnittene Markierungsreste (< 10 px) entfernen; Gebäude, die höher als in der Vorlage sind: Karte anpassen.
- **Bäume auf Grünstreifen und Bodenwall in der Stadt (Nutzer, Karte 35):** Bäume auf schmalen Grünstreifen/Beeten stehen
  mit dem Stammfuß auf der senkrechten Mitte des Streifens, nicht am unteren Rand (geht vor Regel 1b). Auf Gehweg,
  Pflaster und Asphalt bekommen Objekte keinen Bodenwall (`ohne_wall`) – Straßen haben harte Kanten, nichts wird
  aus der Bodentextur an den Fuß gepixelt.
- **Generierte Gebäude auf Schnittkanten prüfen (Nutzer, Karte 35):** Nach jeder Generierung die äußersten Pixelspalten
  und -zeilen ansehen – helles Wand-/Pfeilermaterial ohne dunkle Kontur am Bildrand heißt: abgeschnitten. Der Pro-Generator
  füllt die Leinwand oft ganz aus (Rand im Prompt wird ignoriert); dann das Sprite reparieren (Kante/Pfeiler ergänzen,
  Kontur setzen) statt es angeschnitten einzusetzen.
- **Kartenrand mit Baumgürtel (Nutzer, Karte 35):** Eine Karte endet nie direkt im Nichts/Nebel/Kartenrand. Ringsum
  wird sie um einige Kacheln erweitert und mit einem dichten Baumgürtel (nicht begehbar, Lücken mit Büschen gefüllt)
  umschlossen; Nebel/Effekte liegen nur ganz außen darüber. Ausgänge laufen in voller Weg-/Fahrbahnbreite durch den
  Gürtel bis zum Teleporter am neuen Rand (Teleporter mittig im Weg); Straßen ohne Ausgang enden mit Bordstein.
- **Brücken und Bauwerke wie in der Vorlage (Nutzer, Karte 35):** Ansicht und Aufbau aus der Vorlage übernehmen (z. B.
  Fußgängerbrücke in Draufsicht: gerade Treppen auf den Gehwegen, Pfeiler am Fahrbahnrand – nie Stelzen auf der
  Fahrbahnmitte); zwischen Zebrastreifen, nie darauf. Breite Bauwerke über Straßen ohne automatischen Schattenbalken
  (`schattenlos`, wenn Kontakt-/Schlagschatten als Balken quer über die Fahrbahn fällt).
- **Neue Objekte nie selbst zeichnen (Nutzer, Karte 35):** Fehlt ein Objekt, wird es mit PixelLab erzeugt – nicht
  per Code gemalt. Bei wichtigen Einzelobjekten (Brücke, Wahrzeichen) mehrere Kandidaten erzeugen und dem Nutzer als
  Vorschau neben der Vorlage zur Auswahl zeigen. Reparaturen an generierten Sprites (Kanten, Fremdpixel) sind erlaubt.
- **Eingänge frei (Karte 35):** Vor jeder Tür liegt Gehweg/Weg auf der Türachse (Beetlücke genau vor dem Eingang);
  aus Hälften gespiegelte Gebäude bekommen einen Eingang auf der Achse, Saum- und Rauschpixel werden entfernt.
- **Begleiter am Stumpf (5d):** keine 1-Kachel-Blumen auf dem Stumpf, kein Blumenklumpen; Begleiter überlappen sich nicht.
- **Paare/Achsen:** Paare vor Toren/Bauwerken exakt gespiegelt (Mitte und Fuß), gleiche Objekte auf gleicher Höhe;
  Druckplatten, Obelisken usw. symmetrisch zur berechneten Achse.
- **Streudeko:** nie an Portalen, Objekten (2 px Abstand) oder Gittern; keine regelmäßigen Raster (Vogelscheuchen-Gitter).
- **Animation:** Fahnen/Banner – nur das Tuch, Stange und Fuß fest, Motiv bleibt ganz (`standarte`/`wimpel`); Feuer ohne
  Löcher; Pumpen/Arme/Schaukeln drehen um den echten Drehpunkt, alle Gestänge folgen; Bildschirm-/LED-Effekte nur in
  der Bildfläche (Box), nie auf Gehäuse, Kabel, Reagenzgläsern; Leuchtschein auf der Lichtquelle, nicht auf dem Sockel;
  Rauch nur aus der Öffnung; Kristalle glitzern selbst; graue/andersfarbige Portale drehen (`portal_box`); Gondeln
  ruhig (ein Schwung je Schleife); Schleife Bild 15→0 ohne Sprung (Wasserstriche, Schaum, Riesenrad, Farbmuster).
- **Zeichenreihenfolge:** Wolken/Wellen/Seegras nie über Mauern, Felsen, Stegen; schwebende Objekte ohne Bodenwall.
- **Wasser:** Schaum und Stufen parallel zur 45°-Küste (`wasser_details.RASTER45`), keine dünnen Stufen-Grate in Kanälen,
  keine Felsspitzen an Brücken/Teleportern, keine Schaumringe auf Land; Brückenringe nur auf Wasser.
- **Kollision:** Treppen/Brücken begehbar, Risse/Leere/Wasser gesperrt; Overlay ansehen.
