# ShipStack news-image handoff

The pipeline accepts a generated background image and applies a deterministic editorial treatment: 1080x1350 crop, colour correction, ShipStack News label, verified source strip, headline/deck typography, and attribution. It does not publish.

Run:

    python news-single/render.py --brief news-single/sample.json --background news-single/images/SHIPNEWS-20261119-001.jpg --output news-single/out/SHIPNEWS-20261119-001.jpg

Publishing remains guarded by the approved field and the existing journal.
