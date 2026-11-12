# Pythonic Life integration

Pinned MIT-licensed source and attribution: UPSTREAM.md and upstream/LICENSE.
Five formats are adapted: three-ring escape, balloon pop, last ball standing,
crumbling floor, and marble race. The original simulation and synthesized sound
are retained. Branding/fonts and the exporter are adapted to @shipstack_.

Every clip is 1080x1920, 30 FPS and exactly 15 seconds. The source timeline and
source sound are resampled together so the actual winning event is shown before
the end. This changes playback speed; it does not change who wins. The end-card
source-code tutorial is omitted. No external songs or voice models are used.

## Overnight batch

batch.json declares ten specific clips (two variants of each format). The
Pythonic Life — overnight 10 workflow renders three at a time, validates all ten,
then publishes sequentially with a 45-second gap. It is a one-off batch, separate
from the regular ten daily Instagram slots, as explicitly requested. Its IDs and
content hashes are recorded in the existing reels/state.json before publishing.
A failed/uncertain publish is never retried blindly. Re-running skips attempted IDs.
Disable the workflow to stop the batch. Do not change this manifest after posting
starts; create a separately identified batch instead.

Facebook publishing uses the same clips only when FB_PAGE_ID and FB_PAGE_TOKEN
identify the same Page and access succeeds. Missing Facebook credentials do not
prevent the authorized Instagram batch. Facebook requires its own Page access
token; the existing Instagram-only token cannot be used. Facebook receives a
separate publish journal before the finish request. An uncertain Facebook result
needs manual reconciliation, not a re-upload.

This integration does not yet enable a 30/day Facebook schedule. That rollout
requires a working Page connection and confirmation of its identity. No views,
reach, income, or monetization approval are promised by the workflow.

The regular Instagram pipeline now uses these five formats with seed variation.
The original 30-day campaign window and existing publication history are preserved.
