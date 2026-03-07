(function () {
  'use strict';

  const ARM_NUMS = 'ԱԲԳԴԵԶԷԸԹԺԻԼԽԾԿ';
  const ADJECTIVES = new Set([
    'կենտրոնական', 'գեղեցիկ', 'հին', 'նոր', 'աֆրիկյան', 'ասիական', 'պատմական',
    'լեռնային', 'զբոսաշրջային', 'ծովափնյա', 'գիշերային', 'արևոտ', 'անձրևոտ',
    'մշակութային', 'ապակյա', 'պլաստիկ', 'փայլուն', 'դասական', 'ժամանակակից', 'թանկ',
    'բանկային', 'միկրոալիքային', 'Հայ', 'աշխարհի', 'հայտնի', 'երաժիշտ', 'երգիչ', 'դերասան',
    'մոդել', 'ֆուտբոլիստ', 'գիտնական', 'բլոգեր', 'ռեժիսոր', 'գործարար', 'քաղաքական',
    'շախմատիստ', 'եղջյուրավոր'
  ]);
  const TWO_WORD = new Set(['Հայ հայտնի', 'աշխարհի հայտնի']);

  function toArm(n) {
    if (n >= 1 && n <= 15) return ARM_NUMS[n - 1];
    return String(n);
  }

  function fromArm(s) {
    if (s.length === 1 && ARM_NUMS.includes(s)) return ARM_NUMS.indexOf(s) + 1;
    const n = parseInt(s, 10);
    return isNaN(n) ? 1 : n;
  }

  function wordWithoutAdjective(word) {
    if (!word || !word.includes(' ')) return word.trim();
    let parts = word.split(' ');
    while (parts.length >= 2 && ADJECTIVES.has(parts[0])) parts = parts.slice(1);
    while (parts.length >= 3 && TWO_WORD.has(parts[0] + ' ' + parts[1])) {
      parts = parts.slice(2);
    }
    while (parts.length >= 2 && ADJECTIVES.has(parts[0])) parts = parts.slice(1);
    return parts.join(' ').trim() || word.trim();
  }

  let wordsData = {};
  const screens = {
    menu: document.getElementById('screen-menu'),
    categories: document.getElementById('screen-categories'),
    setup: document.getElementById('screen-setup'),
    names: document.getElementById('screen-names'),
    reveal: document.getElementById('screen-reveal'),
    round: document.getElementById('screen-round'),
    vote: document.getElementById('screen-vote'),
    result: document.getElementById('screen-result')
  };

  const cfg = {
    category: 'Բոլորը',
    players: 4,
    impostors: 1,
    roundMinutes: 2,
    roundSeconds: 120
  };

  const state = {
    word: '',
    impostorIds: [],
    revealIndex: 1,
    secretVisible: false,
    remaining: 0,
    timerId: null,
    playerNames: [],
    startPlayerName: ''
  };

  function playerDisplayName(index) {
    if (index >= 1 && index <= state.playerNames.length) {
      return state.playerNames[index - 1] + ' (Խաղացող ' + toArm(index) + ')';
    }
    return 'Խաղացող ' + toArm(index);
  }

  function showScreen(name) {
    Object.values(screens).forEach(s => { if (s) s.classList.remove('active'); });
    const el = screens[name];
    if (el) el.classList.add('active');
  }

  function loadWords() {
    return fetch('data/words_hy.json')
      .then(r => r.ok ? r.json() : Promise.reject())
      .then(data => { wordsData = data; })
      .catch(() => {
        wordsData = { 'Բոլորը': ['բառ', 'խաղ', 'իմպոստոր'] };
      });
  }

  function getPool() {
    let pool = wordsData[cfg.category];
    if (!pool || !Array.isArray(pool)) pool = wordsData['Բոլորը'] || ['բառ'];
    return pool;
  }

  function goMenu() { showScreen('menu'); }
  function goCategories() { showScreen('categories'); }

  function goSetup() {
    cfg.category = cfg.category || 'Բոլորը';
    showScreen('setup');
    document.getElementById('setup-players').value = String(cfg.players);
    document.getElementById('setup-impostors').value = String(cfg.impostors);
    document.getElementById('setup-timer').value = String(cfg.roundMinutes);
  }

  function goNames() {
    setupChange();
    const n = cfg.players;
    const box = document.getElementById('names-box');
    box.innerHTML = '';
    for (let i = 1; i <= 15; i++) {
      const inp = document.createElement('input');
      inp.type = 'text';
      inp.placeholder = 'Խաղացող ' + i + ' անուն';
      inp.className = 'name-input';
      inp.id = 'name-' + i;
      if (i <= n) {
        inp.style.display = 'block';
        if (state.playerNames[i - 1]) inp.value = state.playerNames[i - 1];
      } else {
        inp.style.display = 'none';
      }
      box.appendChild(inp);
    }
    showScreen('names');
  }

  function confirmNames() {
    const names = [];
    for (let i = 1; i <= cfg.players; i++) {
      const el = document.getElementById('name-' + i);
      if (!el) continue;
      const v = (el.value || '').trim();
      names.push(v);
    }
    if (names.length !== cfg.players) {
      alert('Փորձիր կրկին');
      return;
    }
    if (names.some(function (n) { return !n; })) {
      alert('Բոլոր անունները պարտադիր են');
      return;
    }
    state.playerNames = names;
    state.startPlayerName = state.playerNames[Math.floor(Math.random() * state.playerNames.length)];
    startGameAfterNames();
  }

  function startGameAfterNames() {
    cfg.roundSeconds = Math.max(60, cfg.roundMinutes * 60);
    const pool = getPool();
    if (!pool.length) {
      alert('Բառերի ցուցակը դատարկ է');
      return;
    }
    state.word = wordWithoutAdjective(pool[Math.floor(Math.random() * pool.length)]);
    const ids = Array.from({ length: cfg.players }, (_, i) => i + 1);
    for (let i = ids.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [ids[i], ids[j]] = [ids[j], ids[i]];
    }
    state.impostorIds = ids.slice(0, cfg.impostors).sort((a, b) => a - b);
    state.revealIndex = 1;
    state.secretVisible = false;
    updateReveal();
    showScreen('reveal');
  }

  function setupChange() {
    cfg.players = Math.max(3, Math.min(15, parseInt(document.getElementById('setup-players').value, 10) || 4));
    cfg.impostors = Math.max(1, Math.min(cfg.impostors, Math.floor(cfg.players / 2)));
    cfg.impostors = Math.max(1, Math.min(parseInt(document.getElementById('setup-impostors').value, 10) || 1, Math.floor(cfg.players / 2)));
    cfg.roundMinutes = Math.max(1, Math.min(10, parseInt(document.getElementById('setup-timer').value, 10) || 2));
    cfg.roundSeconds = cfg.roundMinutes * 60;
    document.getElementById('setup-impostors').value = String(cfg.impostors);
  }

  function selectCategory(category) {
    cfg.category = category;
    goSetup();
  }

  function updateReveal() {
    const player = state.revealIndex;
    const isImpostor = state.impostorIds.includes(player);
    document.getElementById('reveal-title').textContent = playerDisplayName(player);
    const secretEl = document.getElementById('reveal-secret');
    const btnEl = document.getElementById('reveal-toggle');
    if (state.secretVisible) {
      secretEl.textContent = isImpostor ? 'ԻՄՊՈՍՏՈՐ' : state.word;
      btnEl.textContent = 'Թաքցնել հաջորդը';
    } else {
      secretEl.textContent = '••••••';
      btnEl.textContent = 'Ցույց տալ';
    }
  }

  function toggleSecret() {
    const wasVisible = state.secretVisible;
    state.secretVisible = !state.secretVisible;
    updateReveal();
    if (wasVisible && !state.secretVisible) nextReveal();
  }

  function nextReveal() {
    if (state.revealIndex < cfg.players) {
      state.revealIndex++;
      state.secretVisible = false;
      updateReveal();
    } else {
      startRound();
    }
  }

  function startRound() {
    state.remaining = cfg.roundSeconds;
    if (state.timerId) clearInterval(state.timerId);
    updateTimerDisplay();
    state.timerId = setInterval(tick, 1000);
    var startsEl = document.getElementById('round-starts');
    if (startsEl) startsEl.textContent = 'Սկսում է՝ ' + (state.startPlayerName || '');
    showScreen('round');
  }

  function tick() {
    state.remaining--;
    if (state.remaining <= 0) {
      state.remaining = 0;
      updateTimerDisplay();
      if (state.timerId) clearInterval(state.timerId);
      state.timerId = null;
      showResult(false);
      return;
    }
    updateTimerDisplay();
  }

  function updateTimerDisplay() {
    const r = Math.max(0, state.remaining);
    const m = Math.floor(r / 60);
    const s = r % 60;
    const el = document.getElementById('round-timer');
    if (el) el.textContent = (m < 10 ? '0' : '') + m + ':' + (s < 10 ? '0' : '') + s;
  }

  function goVote() {
    if (state.timerId) clearInterval(state.timerId);
    state.timerId = null;
    const sel = document.getElementById('vote-player');
    sel.innerHTML = '';
    for (let i = 1; i <= cfg.players; i++) {
      const opt = document.createElement('option');
      const label = playerDisplayName(i);
      opt.value = label;
      opt.textContent = label;
      sel.appendChild(opt);
    }
    sel.selectedIndex = 0;
    showScreen('vote');
  }

  function parsePlayerIndexFromVote(selection) {
    if (!selection) return -1;
    for (let i = 1; i <= cfg.players; i++) {
      if (selection === playerDisplayName(i)) return i;
    }
    var part = selection.split(/\s+/).pop().replace(/[()]/g, '');
    return fromArm(part);
  }

  function goRound() {
    state.remaining = state.remaining || 60;
    updateTimerDisplay();
    state.timerId = setInterval(tick, 1000);
    showScreen('round');
  }

  function finishRound() {
    if (state.timerId) clearInterval(state.timerId);
    state.timerId = null;
    showResult(false);
  }

  function checkVote() {
    const sel = document.getElementById('vote-player');
    const text = sel.options[sel.selectedIndex].value;
    if (!text || text === 'Ընտրել խաղացող') {
      alert('Ընտրիր խաղացող');
      return;
    }
    const n = parsePlayerIndexFromVote(text);
    if (n < 1 || n > cfg.players) {
      alert('Սխալ ընտրություն');
      return;
    }
    const caught = state.impostorIds.includes(n);
    if (caught) {
      showResult(true);
    } else {
      state.remaining += 60;
      updateTimerDisplay();
      state.timerId = setInterval(tick, 1000);
      showScreen('round');
    }
  }

  function showResult(teamWon) {
    if (state.timerId) clearInterval(state.timerId);
    state.timerId = null;
    const titleEl = document.getElementById('result-title');
    const detailsEl = document.getElementById('result-details');
    titleEl.classList.remove('win', 'lose');
    if (teamWon) {
      titleEl.textContent = 'Հաղթանակ';
      titleEl.classList.add('win');
    } else {
      titleEl.textContent = 'Հաղթեց իմպոստորը';
      titleEl.classList.add('lose');
    }
    var impostorsStr = (state.impostorIds || []).map(function (i) { return playerDisplayName(i); }).join(', ');
    detailsEl.textContent = 'Բառը՝ ' + state.word + '\nԻմպոստոր-ներ՝ ' + impostorsStr;
    showScreen('result');
  }

  function newGame() {
    if (state.timerId) clearInterval(state.timerId);
    state.timerId = null;
    state.word = '';
    state.impostorIds = [];
    state.revealIndex = 1;
    state.secretVisible = false;
    showScreen('setup');
    document.getElementById('setup-players').value = String(cfg.players);
    document.getElementById('setup-impostors').value = String(cfg.impostors);
    document.getElementById('setup-timer').value = String(cfg.roundMinutes);
  }

  function resetToSetup() {
    if (state.timerId) clearInterval(state.timerId);
    state.timerId = null;
    showScreen('setup');
  }

  document.getElementById('setup-players').addEventListener('change', setupChange);
  document.getElementById('setup-impostors').addEventListener('change', setupChange);
  document.getElementById('setup-timer').addEventListener('change', setupChange);
  document.getElementById('reveal-toggle').addEventListener('click', toggleSecret);

  document.querySelectorAll('[data-action]').forEach(btn => {
    btn.addEventListener('click', function () {
      const action = this.getAttribute('data-action');
      if (action === 'go-setup') goSetup();
      else if (action === 'go-categories') goCategories();
      else if (action === 'go-menu') goMenu();
      else if (action === 'go-names') goNames();
      else if (action === 'confirm-names') confirmNames();
      else if (action === 'go-vote') goVote();
      else if (action === 'go-round') goRound();
      else if (action === 'finish-round') finishRound();
      else if (action === 'check-vote') checkVote();
      else if (action === 'new-game') newGame();
      else if (action === 'reset-setup') resetToSetup();
    });
  });

  document.querySelectorAll('[data-category]').forEach(btn => {
    btn.addEventListener('click', function () {
      selectCategory(this.getAttribute('data-category'));
    });
  });

  loadWords().then(() => {
    document.body.classList.add('ready');
  });
})();
