import test from 'node:test';
import assert from 'node:assert/strict';
import {dueSlot, guardBlock, slotTime, STALE_MS} from '../src/plan.js';
import {tick} from '../src/index.js';

const cal = {paused: false, slots: [
  {id: 'A', date: '2026-11-21', time: '15:30', format: 'news', episode: 'next'},
  {id: 'B', date: '2026-11-21', time: '17:00', format: 'dsa', episode: 'next'},
]};
const at = (hm, d = '2026-11-21') => Date.parse(`${d}T${hm}:00+05:30`);

test('slot times are IST', () => assert.equal(new Date(slotTime(cal.slots[0])).toISOString(), '2026-11-21T10:00:00.000Z'));
test('nothing before the first slot', () => assert.equal(dueSlot(cal, {}, at('15:29')), null));
test('due once its time passes', () => assert.equal(dueSlot(cal, {}, at('15:31')).id, 'A'));
test('posted slots are skipped, next one is picked', () => assert.equal(dueSlot(cal, {A: {}}, at('17:05')).id, 'B'));
test('stale slots are skipped (over 3 h late)', () => assert.equal(dueSlot({slots: [cal.slots[0]]}, {}, at('15:30') + STALE_MS + 1), null));
test('paused calendar never dispatches', () => assert.equal(dueSlot({...cal, paused: true}, {}, at('15:31')), null));

function fakeFetch({calendar, state, runs, dispatchStatus = 204}) {
  const calls = [];
  globalThis.fetch = async (url, init = {}) => {
    calls.push({url: String(url), method: init.method ?? 'GET', headers: init.headers});
    const u = String(url);
    if (u.includes('calendar.json')) return Response.json(calendar);
    if (u.includes('state.json')) return Response.json(state);
    if (u.endsWith('/dispatches')) return new Response(null, {status: dispatchStatus});
    if (u.includes('/runs')) return Response.json({workflow_runs: runs});
    return new Response('?', {status: 404});
  };
  return calls;
}
const env = {REPO: 'o/r', BRANCH: 'main', WORKFLOW: 'w.yml', GH_TOKEN: 'secret-token'};

test('tick dispatches when due and idle, token only in the Authorization header', async () => {
  const calls = fakeFetch({calendar: cal, state: {posts: {}}, runs: [{status: 'completed'}]});
  const r = await tick(env, at('15:40'));
  assert.deepEqual(r, {action: 'dispatched', slot: 'A'});
  const post = calls.find((c) => c.method === 'POST');
  assert.equal(post.headers.Authorization, 'Bearer secret-token');
  assert.ok(calls.every((c) => !c.url.includes('secret-token')));
});
test('tick does not dispatch while a run is queued or in progress', async () => {
  const calls = fakeFetch({calendar: cal, state: {posts: {}}, runs: [{status: 'in_progress'}]});
  assert.equal((await tick(env, at('15:40'))).action, 'busy');
  assert.ok(!calls.some((c) => c.method === 'POST'));
});
test('tick is idle when nothing is due and makes no GitHub API call', async () => {
  const calls = fakeFetch({calendar: cal, state: {posts: {A: {}, B: {}}}, runs: []});
  assert.equal((await tick(env, at('17:10'))).action, 'idle');
  assert.ok(!calls.some((c) => c.url.startsWith('https://api.github.com')));
});
test('a failed dispatch is reported, not swallowed', async () => {
  fakeFetch({calendar: cal, state: {posts: {}}, runs: [], dispatchStatus: 403});
  await assert.rejects(tick(env, at('15:40')), /dispatch: HTTP 403/);
});

test('guard: waits 60 minutes after any post, stories excluded', () => {
  const now = at('19:41');
  assert.match(guardBlock({a: {published_at: '2026-11-21T19:40:01+05:30'}}, now), /min ago/);
  assert.equal(guardBlock({a: {published_at: '2026-11-21T18:40:00+05:30'}}, now), null);
  assert.equal(guardBlock({a: {published_at: '2026-11-21T19:40:01+05:30', kind: 'story'}}, now), null);
  assert.equal(guardBlock({a: {attempted_at: '2026-11-21T19:00:00+05:30'}}, now), 'last post 41 min ago');
});
test('guard: daily cap of 12 per IST day', () => {
  const posts = {};
  for (let i = 0; i < 12; i++) posts['p' + i] = {published_at: `2026-11-21T${String(6 + i).padStart(2, '0')}:00:00+05:30`};
  assert.equal(guardBlock(posts, at('19:41', '2026-11-21')), '12 posts today');
  assert.equal(guardBlock(posts, at('19:41', '2026-11-22')), null);
});
test('tick waits (no GitHub call) while the guard would block', async () => {
  const calls = fakeFetch({calendar: cal, state: {posts: {x: {published_at: '2026-11-21T15:35:00+05:30'}}}, runs: []});
  const r = await tick(env, at('15:50'));
  assert.equal(r.action, 'waiting');
  assert.ok(!calls.some((c) => c.url.startsWith('https://api.github.com')));
});
