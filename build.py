"""Rebuild handbook.html (slide deck) from deck.template.html + imgmanifest.json.

    python build.py
"""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))

tmpl = open(os.path.join(HERE, "deck.template.html"), encoding="utf-8").read()
man  = json.load(open(os.path.join(HERE, "imgmanifest.json"), encoding="utf-8"))
out  = tmpl.replace("__IMG__", json.dumps(man))
open(os.path.join(HERE, "handbook.html"), "w", encoding="utf-8").write(out)
print("Wrote handbook.html  (%.2f MB)" % (len(out.encode()) / 1048576))
