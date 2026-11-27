好的，下面是“串联与并联”的学科内容代码：

```javascript
const SCENE = {
  title: '串联与并联',
  subtitle: '初中物理，拆灯、开关和电流',
  sky: 'dawn',
  size: [9.5, 4],
  theme: { main: '#7a4b1e', hl: '#ff6a13' },
  cover: { tag: '初中物理', q: '拆掉一盏灯，<br>另一盏还亮吗？', p: '实验台上有串联、并联两块电路板。每道题先预测，再动手拆灯、开关，用电流表测一测。', btn: '走进实验台' },
  noteQ: '串联和并联哪里不一样？从电流的路、开关的作用、电流的大小三方面写。',
  source: '模型简化：电池按 3 V 理想电源，L1、L2 规格不同（灯丝电阻 10 Ω 和 15 Ω），电流值由此算出。',
  views: {
    overview: { az: .12, el: .8, z: 1, t: [0, .6, 0] },
    series: { az: .1, el: .9, z: .52, t: [-2.4, .6, 0] },
    parallel: { az: .1, el: .9, z: .52, t: [2.4, .6, 0] }
  }
};

const U = 3, R1 = 10, R2 = 15, SX = -2.4, PX = 2.4;
const PARTS = {}, TAGS = {}, METER = {};

// 题目：每个选项都有自己的反馈；act 是验证动作，measure 是要测的点
const QS = [
  { id: 'q1', board: 'series', mark: 'sL1', title: '串联：拆灯',
    q: '拆掉串联电路里的灯 L1，灯 L2 会怎样？', opts: ['还亮', '熄灭', '更亮'], a: 1,
    act: { label: '拆掉 L1 看看', apply: c => { c.sL1 = false; } },
    why: ['你可能以为每盏灯各有一条路。串联电路只有一条路，L1 的灯座空了，路就断了，L2 也没有电流。',
      '串联只有一条路。拆掉 L1，电路断开，电流表读数变成 0，L2 熄灭。',
      '你可能以为少了一盏灯，电流全给了 L2。可是拆掉 L1 后路就断了，L2 一点电流也没有。'] },
  { id: 'q2', board: 'parallel', mark: 'pL1', title: '并联：拆灯',
    q: '拆掉并联电路里的灯 L1，灯 L2 会怎样？', opts: ['还亮，亮度不变', '熄灭', '还亮，但更暗', '还亮，但更亮'], a: 0,
    act: { label: '拆掉 L1 看看', apply: c => { c.pL1 = false; } },
    why: ['L2 在自己的支路上，和电池直接连成通路。拆掉 L1 只断了 L1 那一条支路，L2 的电流还是 0.20 A，亮度不变。',
      '你可能把它当成了串联。并联有两条支路，L1 那条断了，L2 那条还是通的。',
      '你可能以为总电流变小了，L2 分到的也会变少。总电流确实变小了（0.50 A → 0.20 A），但少掉的是 L1 那一份。L2 的支路两端仍接在电池两极，电流还是 0.20 A，所以亮度不变。',
      '你可能以为 L1 那份电流会转给 L2。每条支路的电流只由它自己决定，L2 还是 0.20 A，亮度不变。'] },
  { id: 'q3', board: 'parallel', mark: 'pS1', title: '并联：支路开关',
    q: '断开支路开关 S1，L1、L2 会怎样？', opts: ['L1、L2 都熄灭', '只有 L1 熄灭', '只有 L2 熄灭', '都还亮'], a: 1,
    act: { label: '断开 S1', apply: c => { c.pS1 = false; } },
    why: ['你可能以为每个开关都控制整个电路。S1 和 L1 串在同一条支路上，只管这一条。',
      'S1 在 L1 的支路上，支路开关只控制它所在的那条支路。',
      '看看 S1 接在哪：它和 L1 串在一条支路上，不在 L2 那条支路上。',
      '并联的支路互不影响，但支路上的开关管得住自己这一条。断开 S1，L1 这条支路就断了。'] },
  { id: 'q4', board: 'parallel', mark: 'pS', title: '并联：干路开关',
    q: '开关 S 接在电池旁边。断开 S，L1、L2 会怎样？', opts: ['L1、L2 都熄灭', '只有 L1 熄灭', '都还亮'], a: 0,
    act: { label: '断开 S', apply: c => { c.pS = false; } },
    why: ['S 在干路上，两条支路的电流都要经过它。干路开关控制整个电路。',
      '你可能以为 S 和 S1 一样只管一条支路。S 在电池旁边的干路上，两条支路的电流都要经过它。',
      '你可能以为并联时每盏灯各自通电。两条支路都要经过干路才能回到电池，干路断了，整个电路都断了。'] },
  { id: 'q5', board: 'series', title: '串联：测电流',
    q: '电流从电池正极出发，依次经过 L1、L2。A、B、C 三处的电流有什么关系？',
    opts: ['A 最大，C 最小（电流被灯用掉了）', '三处一样大', 'C 最大，A 最小'], a: 1, measure: ['sA', 'sB', 'sC'],
    why: ['这是很常见的想法。灯消耗的是电能，电流不会被“用掉”。串联只有一条路，三处都是 0.12 A。再看亮度：L2 比 L1 还亮一些，因为两盏灯规格不同，和谁在前面无关。',
      '串联电路中各处电流相等，三处都是 0.12 A。再看亮度：电流一样，L2 却比 L1 亮一些，因为两盏灯规格不同。',
      '电流不会越流越大。串联只有一条路，三处都是 0.12 A。'] },
  { id: 'q6', board: 'parallel', title: '并联：测电流',
    q: 'A 在干路上，B 在 L1 的支路上，C 在 L2 的支路上。三处电流有什么关系？',
    opts: ['I<sub>A</sub> = I<sub>B</sub> + I<sub>C</sub>', 'I<sub>A</sub> = I<sub>B</sub> = I<sub>C</sub>', 'I<sub>B</sub> 和 I<sub>C</sub> 一定相等'], a: 0, measure: ['pA', 'pB', 'pC'],
    why: ['干路电流等于各支路电流之和：0.50 A = 0.30 A + 0.20 A。',
      '你可能套用了串联的规律。并联时电流在分岔点分成两股：干路 0.50 A，两条支路 0.30 A 和 0.20 A，加起来正好等于干路。',
      '只有两盏灯规格相同，两条支路电流才相等。这里 L1、L2 规格不同，支路电流是 0.30 A 和 0.20 A。相等不相等，干路都等于两条支路之和。'] },
  { id: 'q7', board: 'overview', title: '生活里的电路',
    q: '家里关掉台灯，冰箱照常工作。台灯和冰箱是怎样连接的？', opts: ['串联', '并联'], a: 1,
    why: ['如果是串联，关掉台灯整条路就断了，冰箱也会停。', '家里的用电器都是并联：各在一条支路上，互不影响，各有自己的开关。'] },
  { id: 'q8', board: 'overview', title: '生活里的电路',
    q: '一串老式节日小彩灯，坏了一个，整串都不亮。这些小彩灯是怎样连接的？', opts: ['串联', '并联'], a: 0,
    why: ['坏一个整串都灭，说明电流只有一条路，是串联。', '如果是并联，坏了一个，其他支路照样亮。'] }
];

// 折线拐角处插两个点，让流动箭头贴着导线走
function rounded(pts, k = .1) {
  const out = [pts[0]];
  for (let i = 1; i < pts.length - 1; i++) {
    const p = pts[i];
    for (const q of [pts[i - 1], pts[i + 1]]) {
      const d = Math.hypot(q[0] - p[0], q[2] - p[2]);
      out.push([p[0] + (q[0] - p[0]) * k / d, p[1], p[2] + (q[2] - p[2]) * k / d]);
    }
  }
  out.push(pts[pts.length - 1]);
  return out;
}
// 导线：一段段直的铜线，拐角处放一个焊点
function wire(pts) {
  const P = pts.map(([x, z]) => [x, .62, z]);
  for (let i = 1; i < P.length; i++) tube([P[i - 1], P[i]], .025, '#b87333');
  P.slice(1, -1).forEach(([x, y, z]) => ball(.035, '#b87333', { x, y, z }));
}
function flow(pts) { return arrow(rounded(pts.map(([x, z]) => [x, .66, z])), { r: .028, color: '#3b8fd0' }); }

function lamp(id, x, z, ry, name, text) {
  const g = group({ x, y: .6, z });
  box(.34, .08, .2, '#333', { parent: g, ry });
  cyl(.07, .08, .1, '#9a9a9a', { parent: g, y: .08, flat: false });
  const bulb = group({ parent: g, y: .18 });
  const glass = lathe([[.04, 0], [.12, .08], [.15, .2], [.12, .32], [0, .36]], '#d9d9d9', { parent: bulb, opacity: .9, glow: '#ffc845' });
  const halo = ball(.26, '#ffd76a', { parent: bulb, y: .2, opacity: 0, glow: '#ffcc55', shadow: false });
  TAGS[id] = tag(name, [x, 1.32, z]);
  pickable(g, { id, title: '小灯泡 ' + name, text });
  return PARTS[id] = { g, bulb, glass, halo };
}
function knife(id, x, z, ry, name, text) {
  const g = group({ x, y: .6, z, ry });
  box(.5, .05, .16, '#5b3a1e', { parent: g });
  [-.2, .2].forEach(dx => cyl(.035, .035, .1, '#c9a227', { parent: g, x: dx, metal: .6 }));
  const hinge = group({ parent: g, x: -.2, y: .1 });
  box(.42, .03, .05, '#d4b24a', { parent: hinge, x: .21, metal: .7 });
  cyl(.03, .03, .14, '#222', { parent: hinge, x: .38 });
  TAGS[id] = tag(name, [x, 1.02, z]);
  pickable(g, { id, title: '开关 ' + name, text });
  return PARTS[id] = { hinge };
}
function meterPoint(id, x, z, name, dx = 0, dz = .3) {
  const m = cyl(.08, .08, .05, '#d64532', { x, y: .6, z });
  METER[id] = { name, t: tag(name, [x + dx, .7, z + dz]) };
  pickable(m, { id, title: '测量点 ' + name, text: '在这里接入电流表，测这一处的电流。' });
}

function buildSubject() {
  // 实验台
  box(9.6, .5, 4.4, '#8a6640', { y: 0 });
  [[-4.6, -2], [4.6, -2], [-4.6, 2], [4.6, 2]].forEach(([x, z]) => cyl(.12, .12, 1.4, '#6a4c32', { x, y: -1.4, z }));
  for (const [cx, name] of [[SX, '串联'], [PX, '并联']]) {
    box(3.6, .1, 2.8, '#c9a66b', { x: cx, y: .5 });
    box(1, .22, .4, '#2c2c2c', { x: cx, y: .6, z: 1 });
    [-.22, .22].forEach(dx => cyl(.1, .1, .4, '#c8551f', { x: cx + dx, y: .82, z: 1, rz: Math.PI / 2 }));
    label('+', [cx + .62, .85, 1.12], 'lbl'); label('−', [cx - .62, .85, 1.12], 'lbl');
    label(name, [cx, .62, 1.6], 'lbl');
  }
  // 串联：一条路。正极 → S → L1 → L2 → 负极
  const s = SX;
  wire([[s + .5, 1], [s + 1.4, 1], [s + 1.4, .2]]);
  wire([[s + 1.4, -.2], [s + 1.4, -1], [s + .77, -1]]);
  wire([[s + .43, -1], [s - .43, -1]]);
  wire([[s - .77, -1], [s - 1.4, -1], [s - 1.4, 1], [s - .5, 1]]);
  knife('sS', s + 1.4, 0, Math.PI / 2, 'S', '串联电路只有一个开关，它控制整个电路。');
  lamp('sL1', s + .6, -1, 0, 'L1', '电流流过灯丝，灯丝发热发光。L1 和 L2 规格不同。');
  lamp('sL2', s - .6, -1, 0, 'L2', '电流流过灯丝，灯丝发热发光。L2 和 L1 规格不同。');
  meterPoint('sA', s + 1, 1, 'A'); meterPoint('sB', s, -1, 'B'); meterPoint('sC', s - 1.4, 0, 'C');
  PARTS.sFlow = flow([[s + .5, 1], [s + 1.4, 1], [s + 1.4, -1], [s - 1.4, -1], [s - 1.4, 1], [s - .5, 1]]);

  // 并联：干路 + 两条支路。右侧分岔点 N1，左侧汇合点 N2
  const p = PX;
  wire([[p + .5, 1], [p + 1.4, 1], [p + 1.4, .65]]);
  wire([[p + 1.4, .25], [p + 1.4, -1], [p + .9, -1]]);
  wire([[p + .5, -1], [p - .13, -1]]);
  wire([[p - .47, -1], [p - 1.4, -1], [p - 1.4, 1], [p - .5, 1]]);
  wire([[p + 1.4, -.2], [p + .9, -.2]]);
  wire([[p + .5, -.2], [p - .13, -.2]]);
  wire([[p - .47, -.2], [p - 1.4, -.2]]);
  [[p + 1.4, -.2], [p - 1.4, -.2]].forEach(([x, z]) => ball(.06, '#7a4b1e', { x, y: .62, z }));
  knife('pS', p + 1.4, .45, Math.PI / 2, 'S', 'S 在干路上，两条支路的电流都要经过它。');
  knife('pS1', p + .7, -1, 0, 'S1', 'S1 和 L1 串在同一条支路上。');
  knife('pS2', p + .7, -.2, 0, 'S2', 'S2 和 L2 串在同一条支路上。');
  lamp('pL1', p - .3, -1, 0, 'L1', 'L1 在后面那条支路上，和 L2 规格不同。');
  lamp('pL2', p - .3, -.2, 0, 'L2', 'L2 在前面那条支路上，和 L1 规格不同。');
  meterPoint('pA', p + 1, 1, 'A'); meterPoint('pB', p - 1.4, -.6, 'B', -.4, 0); meterPoint('pC', p - .9, -.2, 'C');
  PARTS.pMain1 = flow([[p + .5, 1], [p + 1.4, 1], [p + 1.4, -.2]]);
  PARTS.pBr1 = flow([[p + 1.4, -.2], [p + 1.4, -1], [p - 1.4, -1], [p - 1.4, -.2]]);
  PARTS.pBr2 = flow([[p + 1.4, -.2], [p - 1.4, -.2]]);
  PARTS.pMain2 = flow([[p - 1.4, -.2], [p - 1.4, 1], [p - .5, 1]]);

  // 桌上散放的器材
  scatter(new THREE.CylinderGeometry(.05, .05, .5, 6), 'vary', spots(10, -4.3, 4.3, -2.1, -1.6).map(q => ({ ...q, y: .5, color: ['#b87333', '#888', '#c8551f'][Math.floor(rnd() * 3)] })));
}

let state;
const base = () => ({ sS: true, sL1: true, sL2: true, pS: true, pS1: true, pS2: true, pL1: true, pL2: true });
function fresh() { state = { i: 0, ans: {}, done: {}, cfg: base(), meas: {} }; }
function currentView() { const q = QS[state.i]; return q ? q.board : 'overview'; }
const amp = I => I.toFixed(2) + ' A';

// 按电路算电流：电池按理想电源，灯丝电阻不变
function solve(c) {
  const Is = c.sS && c.sL1 && c.sL2 ? U / (R1 + R2) : 0;
  const I1 = c.pS && c.pS1 && c.pL1 ? U / R1 : 0, I2 = c.pS && c.pS2 && c.pL2 ? U / R2 : 0;
  return { Is, I1, I2, I: I1 + I2, read: { sA: Is, sB: Is, sC: Is, pA: I1 + I2, pB: I1, pC: I2 } };
}
// 亮度按电功率 I²R 算，最亮的一盏是并联时的 L1
function lit(L, on, P) {
  const k = Math.pow(clamp(P / .9, 0, 1), .6);
  L.bulb.visible = on;
  L.glass.material.color.copy(C('#d9d9d9').lerp(C('#fff3c4'), k));
  L.glass.material.emissiveIntensity = k * 1.4;
  L.halo.material.opacity = k * .35; L.halo.scale.setScalar(.6 + .8 * k);
}
function stream(a, I) { a.set(I > 0 ? '' : 'dim'); a.speed(I / .3); }

function render() {
  const q = QS[state.i], free = !q, c = state.cfg, r = solve(c);
  // 场景
  lit(PARTS.sL1, c.sL1, r.Is * r.Is * R1); lit(PARTS.sL2, c.sL2, r.Is * r.Is * R2);
  lit(PARTS.pL1, c.pL1, r.I1 * r.I1 * R1); lit(PARTS.pL2, c.pL2, r.I2 * r.I2 * R2);
  stream(PARTS.sFlow, r.Is); stream(PARTS.pMain1, r.I); stream(PARTS.pMain2, r.I); stream(PARTS.pBr1, r.I1); stream(PARTS.pBr2, r.I2);
  for (const id of ['sS', 'pS', 'pS1', 'pS2']) PARTS[id].hinge.rotation.z = c[id] ? 0 : .9;
  for (const id in TAGS) TAGS[id].set(q && q.mark === id ? 'hl' : '');
  for (const id in METER) {
    const m = METER[id], show = free || (q.measure || []).includes(id), got = free || state.meas[id];
    m.t.el.style.display = show ? '' : 'none';
    m.t.text(got ? `${m.name}　${amp(r.read[id])}` : m.name); m.t.set(got ? 'ok' : show ? 'hl' : '');
  }
  // 面板
  if (q) {
    const a = state.ans[q.id], done = state.done[q.id];
    const btns = q.opts.map((o, i) => `<button data-act="choose" data-v="${i}" ${a != null ? 'disabled' : ''} class="${done ? (i === q.a ? 'good' : i === a ? 'wrong' : '') : i === a ? 'chosen' : ''}">${o}</button>`).join('');
    let step = '';
    if (a != null && !done && q.act) step = `<button class="primary" data-act="act" style="width:100%">${q.act.label}</button>`;
    if (a != null && !done && q.measure) step = `<p class="hint">点场景里的红色测量点，或用下面的按钮接入电流表：</p><div class="row">${q.measure.map(id => `<button data-act="meas" data-v="${id}" ${state.meas[id] ? 'disabled' : ''}>测 ${METER[id].name} 点</button>`).join('')}</div>`;
    if (done) step = `<button class="primary" data-act="next" style="width:100%">${state.i + 1 < QS.length ? '下一题' : '看总结'}</button>`;
    ui.task(`<h2>${state.i + 1}/${QS.length}　${q.title}</h2><p>${q.q}</p><p class="hint">先预测：</p><div class="opts one">${btns}</div>${step}`);
    if (a == null) ui.msg('<p class="hint">先预测，预测之后才能动手。点场景里的灯、开关，可以看它的说明。</p>');
    else if (!done) ui.msg(`<p class="hint">已锁定预测：${q.opts[a]}。${q.act ? '现在动手验证。' : '把三处都测一遍。'}</p>`);
    else ui.msg(`<div class="fb ${a === q.a ? 'ok' : 'bad'}"><b>${a === q.a ? '✓ 和预测一致' : '✗ 和预测不一样，答案是：' + q.opts[q.a]}</b>${q.why[a]}</div>`);
  } else {
    ui.task(`<h2>总结</h2><table><tr><th></th><th>串联</th><th>并联</th></tr>
      <tr><td>电流的路</td><td>只有一条</td><td>干路加几条支路</td></tr>
      <tr><td>拆掉一盏灯</td><td>其他灯都灭</td><td>其他灯照常亮</td></tr>
      <tr><td>开关</td><td>一个开关控制全部</td><td>干路开关控制全部，支路开关只管本支路</td></tr>
      <tr><td>电流</td><td>处处相等</td><td>干路等于各支路之和</td></tr></table>
      <p class="hint">自由实验：点场景里的开关可以开合，点灯泡可以拆下或装回，电流表读数跟着变。</p>
      <button data-act="restore" style="width:100%">全部装回、合上</button>`);
    ui.msg(`<div class="fb"><b>现在的读数</b>串联 ${amp(r.Is)}；并联干路 ${amp(r.I)}，L1 支路 ${amp(r.I1)}，L2 支路 ${amp(r.I2)}</div>`);
  }
  const rows = QS.filter(x => state.ans[x.id] != null);
  ui.rec(rows.length ? `<table><tr><th>题</th><th>预测</th><th>结果</th></tr>${rows.map(x => `<tr><td>${QS.indexOf(x) + 1}</td><td>${x.opts[state.ans[x.id]]}</td><td>${state.done[x.id] ? (state.ans[x.id] === x.a ? '✓' : x.opts[x.a]) : '未验证'}</td></tr>`).join('')}</table>` : '');
  focus(currentView());
}

const ACTIONS = {
  choose(v) {
    const q = QS[state.i]; if (state.ans[q.id] != null) return;
    state.ans[q.id] = +v; if (!q.act && !q.measure) state.done[q.id] = true; render();
  },
  act() { const q = QS[state.i]; q.act.apply(state.cfg); state.done[q.id] = true; render(); },
  meas(id) {
    const q = QS[state.i]; if (!q || !q.measure || state.ans[q.id] == null || !q.measure.includes(id)) return;
    state.meas[id] = true; if (q.measure.every(m => state.meas[m])) state.done[q.id] = true; render();
  },
  next() { state.i++; state.cfg = base(); state.meas = {}; render(); },
  restore() { state.cfg = base(); render(); }
};

function onPick(info) {
  const q = QS[state.i];
  if (!q && info.id in state.cfg) { state.cfg[info.id] = !state.cfg[info.id]; render(); return; }
  if (q && q.measure && METER[info.id]) { ACTIONS.meas(info.id); if (state.meas[info.id]) return; }
  ui.msg(`<div class="fb"><b>${info.title}</b>${info.text}</div>`);
}
```

把上面的代码粘贴到拼装器即可。
