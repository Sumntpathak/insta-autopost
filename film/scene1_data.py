"""Caption timings for the Scene 1 sample: words spread across each line's spoken span
(found with silence detection), weighted by word length."""
import json, re, subprocess
from pathlib import Path

LINES = {'L1a': 'Three hundred and fifty crore. Forty-seventh floor. And every morning... I look down at my people.',
         'L2a': 'Forty tabs per household. Every tutorial paused at minute three. Beautiful.'}


def spans(path):
    err = subprocess.run(['ffmpeg', '-v', 'info', '-i', path, '-af', 'silencedetect=noise=-38dB:d=0.18', '-f', 'null', '-'],
                         capture_output=True, text=True).stderr
    dur = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path]))
    s = [float(x) for x in re.findall(r'silence_start: ([0-9.]+)', err)]
    e = [float(x) for x in re.findall(r'silence_end: ([0-9.]+)', err)]
    cuts, start = [], 0.0
    for a, b in zip(s, e + [dur]):
        if a - start > 0.15:
            cuts.append((start, a))
        start = b
    if dur - start > 0.15:
        cuts.append((start, dur))
    return cuts, dur


out = {}
for key, text in LINES.items():
    path = f'public/vo/lines/{key}.wav'
    cuts, dur = spans(path)
    sentences = [s.strip() for s in re.split(r'(?<=[.?!])\s+', text) if s.strip()]
    # map sentences onto speech spans in order (merge extra spans into the last sentence)
    while len(cuts) > len(sentences):
        a, b = cuts.pop(); cuts[-1] = (cuts[-1][0], b)
    while len(cuts) < len(sentences):               # fewer spans: split the longest
        i = max(range(len(cuts)), key=lambda k: cuts[k][1] - cuts[k][0]); a, b = cuts[i]; m = (a + b) / 2
        cuts[i:i + 1] = [(a, m), (m, b)]
    words = []
    for (a, b), sentence in zip(cuts, sentences):
        ws = sentence.split(); weights = [len(w) + 2 for w in ws]; total = sum(weights); t = a
        for w, wt in zip(ws, weights):
            d = (b - a) * wt / total; words.append({'text': w, 'start': round(t, 3), 'end': round(t + d, 3)}); t += d
    out[key] = {'file': f'vo/lines/{key}.wav', 'duration': dur, 'words': words}
Path('src/scene1-data.json').write_text(json.dumps(out, indent=1))
print({k: (v['duration'], len(v['words'])) for k, v in out.items()})
