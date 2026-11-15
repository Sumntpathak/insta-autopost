# Clear-glass visual revision

## Review of the first rendered reel

- Cups were flat trapezoids and had no modeled rim or surface reflections.
- Balls used concentric circles with dark edges; faces were too small.
- Glass had a hard drop shadow and a uniform white tint, with little optical depth.
- All-caps outlined headings competed with the game. Decorative sparkles added noise.
- Cups jumped instantly between their raised and lowered positions.

## Implemented direction

An original Apple-inspired clear-glass aesthetic, rendered into video. This is not Apple's native Liquid Glass implementation.

The new composition uses a pale field with broad peach, blue and mint colour pools, a concise dark typographic hierarchy, a single spacious game stage, restrained floating controls, blurred shadows, a translucent lens-like panel, edge highlights and a subtle top sheen.

Sunny, Blu and the rose cups are original 3D models rendered in Blender with studio area lights and a Principled BSDF glazed surface. Curious, happy, surprised and blinking expressions are transparent sprite assets. They retain smooth bobbing, bouncing and tilting during video composition. Cups now lower and lift with easing. The engine still uses the original procedural characters for other colour characters until their sprite set is generated.

Assets are pre-rendered so the Python/FFmpeg pipeline can generate reels without Blender at runtime. The video is composited 3D imagery, not a full per-frame 3D scene or physical refraction simulation.

## Material and motion refinement

The next pass raises Cycles sampling to 96, adds a cool lower fill light to lift crushed shadows and a small subsurface contribution to the candy glaze. Cup geometry is closed on top and open underneath, as a shell-game cup should be. Grounded contact shadows change their softness with object height, faint floor reflections add surface context, and the shuffle sorts objects by depth with perspective scaling and restrained banking. Sunny's celebration now uses diminishing ballistic hops and settles instead of bouncing endlessly. Floor reflections and panel optics remain compositing approximations.

## Sources consulted

- [Apple Human Interface Guidelines: Materials](https://developer.apple.com/design/human-interface-guidelines/materials) — distinguish clear and regular material roles; keep text readable over translucent surfaces.
- [Apple: Meet Liquid Glass](https://developer.apple.com/videos/play/wwdc2025/219/) — avoid stacking glass surfaces and keep content visually clear.
- [UI UX Pro Max guidance](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/blob/main/src/ui-ux-pro-max/templates/base/skill-content.md) — reviewed hierarchy, consistency, spacing and motion guidance; applied the relevant general visual principles to a rendered reel. Native app interaction requirements do not apply to this video. No third-party installer was run or catalog CLI output claimed.
- [Blender Principled BSDF](https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/principled.html) — material reference discovered through web search. Local rendering uses Blender 4.3.2.

## Regeneration

```bash
blender -b -t 4 --python scripts/render_characters.py
python -m shipstack.cli render examples/follow_ball.json --width 1080 --fps 30 --output output/follow-ball-clear-glass.mp4
```

The Blender script uses CPU Cycles and does not require a GPU or denoising support. Pillow and the bundled models are sufficient for normal video rendering.
