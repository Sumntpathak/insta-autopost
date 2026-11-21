// ShipStack scheduler (Cloudflare Worker). Cron every 5 minutes: if a calendar slot is due and no calendar run is already
// queued or running, dispatch the GitHub workflow. Rendering and posting stay in GitHub Actions (they need ffmpeg + Remotion).
// Secret: GITHUB_TOKEN (fine-grained token, this repo only, Actions: read and write). Never put it in this file.
import {dueSlot} from './plan.js';

const API = 'https://api.github.com';

async function gh(env, path, init = {}) {
  return fetch(`${API}${path}`, {
    ...init,
    headers: {
      Authorization: `Bearer ${env.GITHUB_TOKEN}`,
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      'User-Agent': 'shipstack-scheduler',
      ...(init.headers ?? {}),
    },
  });
}

async function raw(env, file) {
  const url = `https://raw.githubusercontent.com/${env.REPO}/${env.BRANCH}/${file}?t=${Date.now()}`;
  const res = await fetch(url, {headers: {'Cache-Control': 'no-cache'}});
  if (!res.ok) throw new Error(`${file}: HTTP ${res.status}`);
  return res.json();
}

export async function tick(env, nowMs = Date.now()) {
  const [calendar, state] = await Promise.all([raw(env, 'reels/shipstack/calendar.json'), raw(env, 'reels/state.json')]);
  const slot = dueSlot(calendar, state.posts ?? {}, nowMs);
  if (!slot) return {action: 'idle'};

  const runs = await gh(env, `/repos/${env.REPO}/actions/workflows/${env.WORKFLOW}/runs?per_page=10`);
  if (!runs.ok) throw new Error(`list runs: HTTP ${runs.status}`);
  const busy = (await runs.json()).workflow_runs.some((r) => r.status === 'queued' || r.status === 'in_progress');
  if (busy) return {action: 'busy', slot: slot.id};          // a run is already handling it; the workflow is idempotent anyway

  const res = await gh(env, `/repos/${env.REPO}/actions/workflows/${env.WORKFLOW}/dispatches`, {
    method: 'POST', body: JSON.stringify({ref: env.BRANCH}),
  });
  if (res.status !== 204) throw new Error(`dispatch: HTTP ${res.status} ${await res.text()}`);
  return {action: 'dispatched', slot: slot.id};
}

export default {
  async scheduled(event, env, ctx) {
    ctx.waitUntil(tick(env).then((r) => console.log(JSON.stringify(r)), (e) => console.error(`tick failed: ${e.message}`)));
  },
  // GET /status shows what the Worker would do right now, without dispatching anything. Public info only.
  async fetch(request, env) {
    try {
      const [calendar, state] = await Promise.all([raw(env, 'reels/shipstack/calendar.json'), raw(env, 'reels/state.json')]);
      const slot = dueSlot(calendar, state.posts ?? {}, Date.now());
      return Response.json({paused: Boolean(calendar.paused), due: slot ? slot.id : null, now: new Date().toISOString()});
    } catch (e) {
      return Response.json({error: e.message}, {status: 502});
    }
  },
};
