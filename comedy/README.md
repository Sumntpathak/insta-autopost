# The Last Laugh

An original 27-second, wordless stick-figure comedy. Black linework on white; no captions, dialogue, social-media UI, logos from the references or copied frames.

Story: a gust flips one friend's umbrella inside out. His dry friend laughs. The weather turns hot, and the collected rainwater becomes useful. The laughing friend takes the umbrella, presses its release button out of habit and gets drenched. The other friend laughs, then shares his cup. They remain friends.

The two characters have separate hair signatures and readable surprised, annoyed, amused, overheated, pleading and angry expressions. Body movement, handoffs and sound cues carry the story.

Audio is original procedural cartoon sound design: rain, wind, spring snaps, water, cup sounds, nonverbal synthesized laughter, huffs and a grumble. These are stylized synthetic vocal reactions, not recordings of human actors or spoken dialogue.

```bash
python -m pip install Pillow numpy scipy
python comedy/render.py --previews
python comedy/render.py --output comedy/out/umbrella-last-laugh.mp4
```

Requires FFmpeg. Default output: 1080×1920, 30 FPS, H.264 video, stereo AAC audio. The source renderer uses oversampled linework for clean edges.

`out/character-sheet.png` shows the expression designs, and `out/storyboard.png` shows the narrative beats. The MP4 is a review draft; this script does not publish or activate any account automation.
