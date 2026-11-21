import test from 'node:test';
import assert from 'node:assert/strict';
import {dueSlot, slotTime, STALE_MS} from '../src/plan.js';
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
const env = {REPO: 'o/r', BRANCH: 'main', WORKFLOW: 'w.yml', GITHUB_TOKEN: 'secret-token'};

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
