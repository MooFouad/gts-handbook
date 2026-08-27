"""Write handbook.html from deck.template.html.

Images are no longer inlined — deck.template.html references files
under img/ directly, so this is just a copy step (kept as its own
script so the "source template" vs "built output" split stays clear).

    python build.py
"""
import os
HERE = os.path.dirname(os.path.abspath(__file__))

tmpl = open(os.path.join(HERE, "deck.template.html"), encoding="utf-8").read()
open(os.path.join(HERE, "handbook.html"), "w", encoding="utf-8").write(tmpl)
print("Wrote handbook.html  (%.2f KB)" % (len(tmpl.encode()) / 1024))
