export const meta = {
  name: 'karte_pruefen',
  description: 'Fertige Karte von 4 Agenten nach allen Regeln pruefen (Gelaende, Objekte, Animation, Pixel) + Gegenpruefung',
  whenToUse: 'Nach jedem Bau einer Karte (Skill neue-karte), bis keine hohen/mittleren Befunde mehr kommen. args: {karte: "karte34"}',
  phases: [{ title: 'Pruefen' }, { title: 'Gegenpruefen' }],
}
const K = (args && args.karte) || 'karte34'
const S = '/tmp/pruef_' + K
const SCHEMA = { type: 'object', properties: {
  fehler: { type: 'array', items: { type: 'object', properties: {
    stelle: { type: 'string', description: 'Objekt (basis) und/oder Pixelkoordinaten x,y im Kartenbild' },
    bild: { type: 'string' }, problem: { type: 'string' }, regel: { type: 'string' },
    schwere: { type: 'string', enum: ['hoch', 'mittel', 'gering'] },
    ursache: { type: 'string', description: 'vermutete Ursache in Code/Daten' } },
    required: ['stelle', 'problem', 'schwere'] } },
  geprueft: { type: 'string' } }, required: ['fehler', 'geprueft'] }
const BASIS = `Du pruefst die fertige 16x16-RPG-Karte ${K} im Repo /home/user/DBC. NUR pruefen und berichten, nichts im Repo aendern.
Material: maps/${K}/terrain.png (Standbild), maps/${K}/animation/${K}_animiert_16.webp (16 Bilder), maps/${K}/layout.json,
assets/objekte/${K}/platzierung.json (+Sprites), Vorlage assets/vorlagen/${K}_vorlage.png, Code tools/${K}_*.py.
Scratch-Dateien nur unter ${S}/<dein-name>/. Pruefblaetter je animiertem Objekt erzeugst du bei Bedarf mit
'python3 tools/pruefblaetter.py ${K} ${S}'. Regeln: CLAUDE.md, besonders der Abschnitt "Pruefliste: haeufige Fehler".
Schneide Ausschnitte (etwa 320x240) und vergroessere 2-4x; sieh sie mit dem Read-Tool an. Jeden Verdacht vergroessert
nachpruefen, bevor du ihn meldest. Melde nur echte Fehler mit genauer Stelle.`
const BEREICHE = [
  { n: 'gelaende', t: 'Gelaende: alle Bodenkanten am 16er-Raster mit 45 Grad, keine Einzelkachel-Punkte, Wege geschwungen und in voller Breite an Treppen/Bruecken, Treppen sauber (Wangen, keine Kerbe), Klippen/Plateaus/Hoehen logisch, Wasser (Quelle/Abfluss, Schaum parallel, kein Schaum am Kartenrand), Kartenrand, Vergleich mit der Vorlage (fehlt etwas Wichtiges?). Gehe die GANZE Karte systematisch ab.' },
  { n: 'objekte', t: 'Objekte: Raster/mittig, nichts auf Wegen/Pflaster/Mauerkronen/Kanten, keine Ueberlappungen (2 px), Begleiter an Baeumen (5/5d), keine Reihen/Wiederholungen, Einbettung, Schatten (Form, Hoehenebene, nie ueber Kanten), Verdeckung durch Hoehen/Bauwerke, Gebaeude vollstaendig, Paare symmetrisch, Teleporter frei, Waldrand nicht vor Fassaden. Pruefe JEDES groessere Objekt.' },
  { n: 'animation', t: 'Animation: erzeuge die Pruefblaetter und sieh JEDES an; dazu flaechige Effekte (Wasser, Schaum, Licht, Portale) in 3+ Bildern. Nur Bewegliches bewegt sich, Stoff statt Stange, Flammen zuengeln ohne Loecher, Leuchten nur echte Lichtquellen, Effekte nur in ihrer Flaeche, Zeichenreihenfolge, Schleife 15->0 ohne Sprung, fehlt eine Animation (Feuer/Licht/Wasser/Fahne/Maschine)?' },
  { n: 'pixel', t: 'Pixelfehler: schneide das Standbild in ein lueckenloses Raster aus Ausschnitten und sieh JEDEN Ausschnitt 3x vergroessert an: Fremdpixel, Loecher, Naehte zwischen Kacheln, abgeschnittene Kronen/Objekte, harte Balken, falsche Farben, Artefakte.' },
]
phase('Pruefen')
const funde = await parallel(BEREICHE.map(b => () => agent(BASIS + '\n\nDein Bereich: ' + b.t, { label: 'pruefen:' + b.n, phase: 'Pruefen', schema: SCHEMA })))
const alle = funde.filter(Boolean).flatMap((f, i) => f.fehler.map(x => ({ ...x, bereich: BEREICHE[i].n })))
const wichtig = alle.filter(f => f.schwere !== 'gering')
phase('Gegenpruefen')
const geprueft = await parallel(wichtig.map(f => () => agent(
  BASIS + `\n\nGegenpruefung eines gemeldeten Fehlers. Versuche ihn zu WIDERLEGEN (vergroessert ansehen). Befund: ${JSON.stringify(f)}`,
  { label: 'gegen:' + f.bereich, phase: 'Gegenpruefen', schema: { type: 'object', properties: { echt: { type: 'boolean' }, begruendung: { type: 'string' } }, required: ['echt', 'begruendung'] } })
  .then(v => ({ ...f, echt: v ? v.echt : true, begruendung: v ? v.begruendung : '' }))))
return { karte: K, bestaetigt: geprueft.filter(Boolean).filter(f => f.echt), widerlegt: geprueft.filter(Boolean).filter(f => !f.echt).length, gering: alle.filter(f => f.schwere === 'gering') }
