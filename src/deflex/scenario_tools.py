from collections import namedtuple

# ToDo: 1. Excel-Tabelle umgestalten (Namen der Tabellenblätter
#  evtl. Inhaltsverzeichnis, GENERAL-Table (year...),
#  Reihenfolge (sortieren in Klasse?), Gruppierung durch prefix), Einheiten?
# ToDo: 2. Die vier default Szenrien auf Server parallel rechnen lassen.
# ToDo: 3. Zuerst schonmal die Tests reparieren, die zu reparieren sind, dann
#   alle Tests reparieren, wenn die Ergebnisse vorliegen. Zunächst die
#   die Ergebnisse lokal speichern und alle Tests fixen, dann Ergebnisse
#   hochladen auf OSF. Das gilt für Test-Ergebnisse und Beispielergebnisse
# ToDo: 4. Das Beispielskript anpassen.
# ToDo: 5. Die Struktur für die Dokumentation erstellen und mit Pedro
#  absprechen, wer welche Texte schreibt. Dann Texte schreiben.


class Label(namedtuple("solph_label", ["cat", "tag", "subtag", "region"])):
    """A label for deflex components."""

    __slots__ = ()

    def __str__(self):
        return "_".join(map(str, self._asdict().values()))