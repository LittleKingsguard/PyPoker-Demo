/* PyPoker interactive table — one hand at a time against the league. */
"use strict";

(() => {
  const $ = (id) => document.getElementById(id);

  const SUITS = { s: "♠", h: "♥", d: "♦", c: "♣" };
  const SUIT_NAMES = { s: "spades", h: "hearts", d: "diamonds", c: "clubs" };
  const RED_SUITS = new Set(["h", "d"]);
  const RANK_LABELS = {
    T: "10", J: "J", Q: "Q", K: "K", A: "A",
    2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7", 8: "8", 9: "9",
  };
  const STREET_NAMES = {
    preflop: "Pre-flop",
    flop: "Flop",
    turn: "Turn",
    river: "River",
  };
  const SHORT_POSITIONS = {
    "Button · Small blind": "Button · SB",
    "Big blind": "BB",
    "Button": "Button",
    "Small blind": "SB",
    "Big blind": "BB",
    "Under the gun": "UTG",
    "Hijack": "HJ",
    "Cutoff": "CO",
  };
  const RING = {
    1: ["pos-top"],
    2: ["pos-upper-left", "pos-upper-right"],
    3: ["pos-upper-left", "pos-top", "pos-upper-right"],
    4: ["pos-upper-left", "pos-upper-right", "pos-lower-left", "pos-lower-right"],
    5: ["pos-lower-left", "pos-upper-left", "pos-top", "pos-upper-right", "pos-lower-right"],
  };

  const state = {
    league: null,
    match: null,
    hand: null,
    tab: "models",
    shape: null,
    seat: 0,
    mixed: false,
    query: "",
    busy: false,
    anim: null,
    logLength: -1,
    toastTimer: 0,
  };

  const els = {
    body: document.body,
    actionbar: $("actionbar"),
    actions: $("actions"),
    turnEyebrow: $("turn-eyebrow"),
    turnTitle: $("turn-title"),
    turnSub: $("turn-sub"),
    handMeta: $("hand-meta"),
    scoreYou: $("score-you"),
    scoreThem: $("score-them"),
    scoreOpp: $("score-opp"),
    emptyState: $("empty-state"),
    emptyChoose: $("empty-choose"),
    table: $("poker-table"),

    opponentSeats: $("opponent-seats"),
    humanSeat: $("seat-human"),
    youSub: $("you-sub"),
    youLast: $("you-last"),
    youStack: $("you-stack"),
    youCards: $("you-cards"),
    youRank: $("you-rank"),
    youBet: $("you-bet"),
    youDealer: $("you-dealer"),
    youDelta: $("you-delta"),

    board: $("board"),
    potValue: $("pot-value"),
    streetLabel: $("street-label"),
    handSeed: $("hand-seed"),

    sidebarHand: $("sidebar-hand"),
    logScroll: $("log-scroll"),
    leagueCard: $("league-card"),

    drawer: $("drawer"),
    backdrop: $("backdrop"),
    drawerClose: $("drawer-close"),
    drawerFootNote: $("drawer-foot-note"),
    restartBtn: $("restart-btn"),
    seatToggle: $("seat-toggle"),
    shapeSelect: $("shape-select"),
    seedInput: $("seed-input"),
    mixRow: $("mix-row"),
    mixInput: $("mix-input"),
    tabs: $("tabs"),
    search: $("opp-search"),
    opponentList: $("opponent-list"),
    countModels: $("count-models"),
    countBaselines: $("count-baselines"),

    logBtn: $("log-btn"),
    logClose: $("log-close"),

    helpBtn: $("help-btn"),
    helpModal: $("help-modal"),
    helpClose: $("help-close"),

    leagueBtn: $("league-btn"),
    newMatchBtn: $("new-match-btn"),
    toast: $("toast"),
  };

  /* --- start-up ---------------------------------------------------------- */

  init();

  async function init() {
    bindEvents();
    render();
    try {
      const [league, resume] = await Promise.all([
        api("/api/opponents"),
        api("/api/state").catch(() => ({ match: null })),
      ]);
      state.league = league;
      populateShapes();
      restorePreferences();
      renderLeagueCounts();
      if (resume && resume.match && resume.hand) {
        applyState(resume, { animate: false });
      } else {
        setShape(state.shape || league.default_shape, { keepSeat: true });
        render();
      }
    } catch (error) {
      render();
      toast("Could not reach the table server. " + error.message, true);
    }
  }

  function populateShapes() {
    const shapes = state.league ? state.league.shapes : {};
    const options = [];
    for (const [name, row] of Object.entries(shapes)) {
      const option = document.createElement("option");
      option.value = name;
      option.textContent = row.label + " · " + row.starting_stack + " chips";
      options.push(option);
    }
    els.shapeSelect.replaceChildren(...options);
    if (!state.shape || !shapes[state.shape]) {
      state.shape = state.league ? state.league.default_shape : null;
    }
    if (state.shape) els.shapeSelect.value = state.shape;
  }

  function restorePreferences() {
    let savedShape = null;
    let savedSeat = null;
    try {
      savedShape = window.localStorage.getItem("pypoker.shape");
      savedSeat = window.localStorage.getItem("pypoker.seat." + (savedShape || ""));
    } catch (_) {
      /* storage may be disabled */
    }
    const shape = savedShape && state.league.shapes[savedShape]
      ? savedShape
      : state.league.default_shape;
    const seat = savedSeat === null ? 0 : Number(savedSeat);
    setShape(shape, { keepSeat: true });
    const seats = state.league.shapes[shape].seats;
    state.seat = Number.isInteger(seat) && seat >= 0 && seat < seats ? seat : 0;
    setSeatButtons();
  }

  /* --- events ------------------------------------------------------------ */

  function bindEvents() {
    els.leagueBtn.addEventListener("click", openDrawer);
    els.newMatchBtn.addEventListener("click", openDrawer);
    els.drawerClose.addEventListener("click", closeDrawer);
    els.emptyChoose.addEventListener("click", openDrawer);

    els.backdrop.addEventListener("click", () => {
      if (els.body.classList.contains("log-open")) closeLog();
      else if (els.body.classList.contains("drawer-open")) closeDrawer();
    });

    document.addEventListener("click", (event) => {
      const target = event.target.closest("[data-open-league]");
      if (target) {
        openDrawer();
        return;
      }
      const row = event.target.closest(".opp-row");
      if (row && row.dataset.id && !row.disabled) {
        chooseOpponent(row.dataset.id);
        return;
      }
      const next = event.target.closest("[data-next]");
      if (next && !next.disabled) nextHand();
    });

    els.actions.addEventListener("click", (event) => {
      const action = event.target.closest("[data-action]");
      if (action && !action.disabled) {
        event.stopPropagation();
        act(action.dataset.action);
      }
    });

    els.shapeSelect.addEventListener("change", () => {
      setShape(els.shapeSelect.value);
      persistShape();
      updateDrawerNote();
      renderOpponentList();
    });

    els.seatToggle.addEventListener("click", (event) => {
      const button = event.target.closest("[data-seat]");
      if (!button) return;
      state.seat = Number(button.dataset.seat);
      setSeatButtons();
      persistShape();
      updateDrawerNote();
    });

    els.mixInput.addEventListener("change", () => {
      state.mixed = Boolean(els.mixInput.checked);
      updateDrawerNote();
    });

    els.tabs.addEventListener("click", (event) => {
      const button = event.target.closest("[data-tab]");
      if (!button) return;
      state.tab = button.dataset.tab;
      for (const tab of els.tabs.querySelectorAll("[data-tab]")) {
        const on = tab.dataset.tab === state.tab;
        tab.classList.toggle("is-on", on);
        tab.setAttribute("aria-selected", on ? "true" : "false");
      }
      renderOpponentList();
    });

    els.search.addEventListener("input", () => {
      state.query = els.search.value;
      renderOpponentList();
    });

    els.restartBtn.addEventListener("click", restartMatch);

    els.helpBtn.addEventListener("click", openHelp);
    els.helpClose.addEventListener("click", closeHelp);
    els.helpModal.addEventListener("click", (event) => {
      if (event.target === els.helpModal) closeHelp();
    });

    els.logBtn.addEventListener("click", openLog);
    els.logClose.addEventListener("click", closeLog);

    document.addEventListener("keydown", onKeyDown);
  }

  function openHelp() {
    els.helpModal.hidden = false;
    els.helpClose.focus();
  }

  function closeHelp() {
    els.helpModal.hidden = true;
    els.helpBtn.focus();
  }

  function onKeyDown(event) {
    if (event.metaKey || event.ctrlKey || event.altKey) return;

    if (event.key === "Escape") {
      if (!els.helpModal.hidden) {
        closeHelp();
        return;
      }
      if (els.body.classList.contains("log-open")) {
        closeLog();
        return;
      }
      if (els.body.classList.contains("drawer-open")) closeDrawer();
      return;
    }

    const tag = (document.activeElement && document.activeElement.tagName) || "";
    if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;

    if (!els.helpModal.hidden || els.body.classList.contains("drawer-open")) return;
    if (state.busy) return;

    const key = event.key.toLowerCase();

    if (key === "l") {
      event.preventDefault();
      openDrawer();
      return;
    }
    if (key === "?") {
      event.preventDefault();
      openHelp();
      return;
    }
    if (state.hand && state.hand.over) {
      if (event.key === "Enter" || key === "n") {
        event.preventDefault();
        nextHand();
      }
      return;
    }
    if (!state.hand || state.hand.phase !== "your_turn") return;

    const legal = state.hand.legal || [];
    if (key === "f") {
      const found = legal.find((row) => row.kind === "fold");
      if (found) {
        event.preventDefault();
        act(found.action);
      }
      return;
    }
    if (key === "c") {
      const found = legal.find((row) => row.kind === "check");
      if (found) {
        event.preventDefault();
        act(found.action);
      }
      return;
    }
    if (key === "r") {
      const found = primaryRaise(legal);
      if (found) {
        event.preventDefault();
        act(found.action);
      }
    }
  }

  /* --- shape and seats --------------------------------------------------- */

  function setShape(shape, options = {}) {
    if (!state.league || !state.league.shapes[shape]) return;
    state.shape = shape;
    els.shapeSelect.value = shape;
    const row = state.league.shapes[shape];
    const positions = row.positions || [];
    if (!options.keepSeat || !Number.isInteger(state.seat) || state.seat >= positions.length) {
      state.seat = 0;
    }
    if (state.seat >= positions.length) state.seat = 0;
    setSeatButtons();
    els.mixRow.hidden = row.seats <= 2;
    if (row.seats <= 2) {
      state.mixed = false;
      els.mixInput.checked = false;
    } else {
      state.mixed = Boolean(els.mixInput.checked);
    }
    els.table.classList.toggle("is-six", row.seats > 2);
  }

  function setSeatButtons() {
    const row =
      state.league && state.shape ? state.league.shapes[state.shape] : null;
    const positions = row ? row.positions : ["Button · Small blind", "Big blind"];
    els.seatToggle.classList.toggle("is-two", positions.length <= 2);
    const buttons = positions.map((label, index) => {
      const button = document.createElement("button");
      button.type = "button";
      button.dataset.seat = String(index);
      button.textContent = SHORT_POSITIONS[label] || label;
      button.title = label;
      button.classList.toggle("is-on", index === state.seat);
      return button;
    });
    els.seatToggle.replaceChildren(...buttons);
  }

  function persistShape() {
    try {
      window.localStorage.setItem("pypoker.shape", state.shape || "");
      window.localStorage.setItem(
        "pypoker.seat." + (state.shape || ""),
        String(state.seat),
      );
    } catch (_) {
      /* ignore */
    }
  }

  function updateDrawerNote() {
    if (state.busy) {
      els.drawerFootNote.textContent = "The table is working…";
    } else if (state.match && state.shape && state.match.shape !== state.shape) {
      els.drawerFootNote.textContent =
        "The table shape applies to your next match. Restart keeps this match's shape.";
    } else if (state.mixed && state.league && state.shape) {
      els.drawerFootNote.textContent =
        "A mixed table keeps the selected member and fills the other seats from the league.";
    } else if (state.match) {
      els.drawerFootNote.textContent =
        "Restart replays this seed with your current seat and lineup.";
    } else {
      els.drawerFootNote.textContent = "A new opponent starts a new match.";
    }
  }

  /* --- sessions ---------------------------------------------------------- */

  function findMember(id) {
    if (!state.league) return null;
    return (
      state.league.models.find((row) => row.id === id) ||
      state.league.baselines.find((row) => row.id === id) ||
      null
    );
  }

  async function chooseOpponent(id) {
    const member = findMember(id);
    if (!member) return;
    if (member.kind === "model") {
      if (member.available === false) {
        toast(member.unavailable_reason || "That checkpoint is unavailable.", true);
        return;
      }
      setShape(member.shape, { keepSeat: true });
      persistShape();
    }
    await startMatch(id);
  }

  async function startMatch(opponentId) {
    if (state.busy) return;
    const seedText = els.seedInput.value.trim();
    if (seedText && !/^-?\d+$/.test(seedText)) {
      toast("The seed must be a whole number.", true);
      els.seedInput.focus();
      return;
    }
    const table = state.league.shapes[state.shape];
    const lineupMode =
      state.mixed && table && table.seats > 2 ? "mixed" : "same";
    state.busy = true;
    render();
    try {
      const payload = await api("/api/start", {
        opponent_id: opponentId,
        seat: state.seat,
        seed: seedText || null,
        shape: state.shape,
        lineup_mode: lineupMode,
      });
      state.busy = false;
      closeDrawer();
      applyState(payload, { animate: true });
      toast(
        payload.match.lineup_mode === "mixed"
          ? "Mixed table dealt at " + payload.match.shape_label + "."
          : "Match started against " + payload.match.label + ".",
      );
    } catch (error) {
      state.busy = false;
      render();
      toast(error.message, true);
      refreshLeague();
    }
  }

  async function refreshLeague() {
    try {
      const league = await api("/api/opponents");
      state.league = league;
      populateShapes();
      renderLeagueCounts();
      renderOpponentList();
    } catch (_) {
      /* the next start will report the same reason */
    }
  }

  async function restartMatch() {
    if (!state.match || state.busy) return;
    const match = state.match;
    const table = state.league.shapes[match.shape];
    const seat = state.seat < table.seats ? state.seat : match.human_seat;
    state.busy = true;
    render();
    try {
      const payload = await api("/api/start", {
        opponent_id: match.opponent.id,
        seat,
        seed: match.seed,
        shape: match.shape,
        lineup_mode: match.lineup_mode,
      });
      state.busy = false;
      closeDrawer();
      applyState(payload, { animate: true });
      toast("Match restarted from seed " + match.seed + ".");
    } catch (error) {
      state.busy = false;
      render();
      toast(error.message, true);
    }
  }

  async function act(action) {
    if (state.busy || !state.hand || state.hand.over) return;
    state.busy = true;
    render();
    try {
      const payload = await api("/api/action", { action });
      state.busy = false;
      applyState(payload, { animate: true, syncShape: false });
    } catch (error) {
      state.busy = false;
      render();
      toast(error.message, true);
    }
  }

  async function nextHand() {
    if (state.busy || !state.hand || !state.hand.over) return;
    state.busy = true;
    render();
    try {
      const payload = await api("/api/next", {});
      state.busy = false;
      applyState(payload, { animate: true, syncShape: false });
    } catch (error) {
      state.busy = false;
      render();
      toast(error.message, true);
    }
  }

  function applyState(payload, options = {}) {
    const animate = options.animate !== false;
    if (!payload || !payload.match || !payload.hand) {
      state.match = null;
      state.hand = null;
      state.anim = null;
      render();
      return;
    }

    const previous = state.hand;
    const handChanged =
      !previous ||
      previous.hand_number !== payload.hand.hand_number ||
      previous.seed !== payload.hand.seed ||
      previous.shape !== payload.hand.shape;
    const previousBoard = handChanged ? 0 : (previous.board || []).length;

    if (options.syncShape !== false && payload.match.shape !== state.shape) {
      setShape(payload.match.shape, { keepSeat: true });
      persistShape();
    }
    state.seat = payload.match.human_seat;
    state.mixed = payload.match.lineup_mode === "mixed";
    els.mixInput.checked = state.mixed;
    setSeatButtons();

    state.match = payload.match;
    state.hand = payload.hand;
    state.anim = animate
      ? {
          hand: handChanged,
          boardFrom: handChanged ? payload.hand.board.length : previousBoard,
        }
      : null;
    render();
    state.anim = null;
  }

  async function api(path, body) {
    const options = {
      credentials: "same-origin",
      headers: { Accept: "application/json" },
    };
    if (body !== undefined) {
      options.method = "POST";
      options.headers["Content-Type"] = "application/json";
      options.body = JSON.stringify(body);
    }
    const response = await fetch(path, options);
    let payload = null;
    try {
      payload = await response.json();
    } catch (_) {
      payload = null;
    }
    if (!response.ok) {
      const message =
        payload && payload.error
          ? payload.error
          : response.status + " " + response.statusText;
      throw new Error(message);
    }
    return payload;
  }

  /* --- rendering --------------------------------------------------------- */

  function render() {
    renderHeader();
    renderTable();
    renderSidebar();
    renderLeagueCard();
    renderActions();
    renderOpponentList();
    els.emptyState.hidden = Boolean(state.match);
    els.restartBtn.disabled = !state.match || state.busy;
    els.restartBtn.textContent = "Restart this match";
    updateDrawerNote();
    if (state.league) renderLeagueCounts();
    document.title = state.match
      ? "PyPoker — " + state.match.label
      : "PyPoker — Play the league";
  }

  function renderHeader() {
    const match = state.match;
    els.scoreYou.textContent = signed(match ? match.score.human : 0);
    els.scoreThem.textContent = signed(match ? match.score.opponents : 0);
    els.scoreOpp.textContent = match ? match.label : "No opponent";
    els.scoreOpp.title = match
      ? match.opponents.map((row) => row.name).join(" · ")
      : "";
  }

  function renderTable() {
    const match = state.match;
    const hand = state.hand;

    if (!match || !hand) {
      const table =
        state.league && state.shape ? state.league.shapes[state.shape] : null;
      const positions = table ? table.positions : ["Button · Small blind", "Big blind"];
      els.opponentSeats.replaceChildren();
      els.humanSeat.className = "seat seat-human";
      els.youSub.textContent = positions[state.seat] || positions[0] || "Seat";
      els.youStack.textContent = "—";
      els.youLast.textContent = "";
      els.youCards.replaceChildren();
      els.youRank.hidden = true;
      els.youBet.hidden = true;
      els.youDealer.hidden = true;
      hideDelta(els.youDelta);
      els.board.replaceChildren(...Array.from({ length: 5 }, slotNode));
      els.potValue.textContent = "0";
      els.streetLabel.textContent = "Pre-flop";
      els.handSeed.textContent = "seed —";
      els.table.classList.toggle(
        "is-six",
        Boolean(table && table.seats > 2),
      );
      return;
    }

    const human = hand.human;
    const seats = hand.seats;
    const opponents = seats.filter((seat) => !seat.is_human);
    const animateHand = Boolean(state.anim && state.anim.hand);

    els.table.classList.toggle("is-six", hand.seats_count > 2);

    els.humanSeat.className = seatClass("seat seat-human", human);
    els.youSub.textContent = human.position;
    els.youLast.textContent = lastActionText(human.last_action);
    els.youStack.textContent = String(human.stack);
    renderHoleCards(els.youCards, human.hole, animateHand, false);
    renderRank(els.youRank, human.rank);
    setBet(els.youBet, human.bet);
    els.youDealer.hidden = !human.is_button;
    renderDelta(els.youDelta, human.delta);

    const positions = RING[opponents.length] || RING[1];
    const ordered = opponents
      .map((seat) => ({
        seat,
        relative: (seat.seat - human.seat + hand.seats_count) % hand.seats_count,
      }))
      .sort((left, right) => left.relative - right.relative)
      .map((row) => row.seat);

    const nodes = ordered.map((seat, index) =>
      opponentSeatNode(seat, positions[index] || "pos-top", animateHand),
    );
    els.opponentSeats.replaceChildren(...nodes);

    const boardFrom = state.anim ? state.anim.boardFrom : hand.board.length;
    renderBoard(hand.board, boardFrom);
    els.potValue.textContent = String(hand.pot);
    els.streetLabel.textContent = STREET_NAMES[hand.street] || prettify(hand.street);
    els.handSeed.textContent = "seed " + hand.seed;
  }

  function opponentSeatNode(seat, positionClass, animate) {
    const node = document.createElement("div");
    const lower = positionClass.startsWith("pos-lower");
    node.className =
      "seat " + positionClass + (lower ? " is-lower" : "") +
      (seat.turn ? " is-turn" : "") +
      (seat.folded ? " is-folded" : "") +
      (seat.winner ? " is-winner" : "");
    node.dataset.seat = String(seat.seat);
    node.setAttribute(
      "aria-label",
      seat.name + ", " + seat.position + ", " + seat.stack + " chips",
    );

    const plate = document.createElement("div");
    plate.className = "player-plate";
    const avatar = document.createElement("div");
    avatar.className = "avatar avatar-them";
    avatar.textContent = seat.kind === "model" ? "AI" : "R";
    avatar.setAttribute("aria-hidden", "true");
    const meta = document.createElement("div");
    meta.className = "player-meta";
    const name = document.createElement("div");
    name.className = "player-name";
    name.textContent = seat.name;
    name.title = seat.name;
    const sub = document.createElement("div");
    sub.className = "player-sub";
    sub.textContent =
      seat.position + " · " + (seat.kind === "model" ? "trained model" : "fixed policy");
    const last = document.createElement("div");
    last.className = "player-last";
    last.textContent = lastActionText(seat.last_action);
    meta.append(name, sub, last);
    const stack = document.createElement("div");
    stack.className = "stack";
    stack.textContent = String(seat.stack);
    plate.append(avatar, meta, stack);

    const dealer = document.createElement("div");
    dealer.className = "dealer-chip";
    dealer.textContent = "D";
    dealer.title = "Dealer button";
    dealer.hidden = !seat.is_button;
    plate.append(dealer);

    const cards = document.createElement("div");
    cards.className = "cards";
    const mucked = seat.folded || (state.hand && state.hand.over && !seat.hole);
    renderHoleCards(cards, seat.hole || [], animate, mucked);

    const rank = document.createElement("div");
    rank.className = "rank-badge";
    if (seat.rank) {
      rank.textContent = seat.rank;
      rank.hidden = false;
    } else {
      rank.hidden = true;
    }

    const bet = document.createElement("div");
    bet.className = "bet-pill";
    if (Number(seat.bet) > 0) {
      bet.textContent = String(seat.bet);
      bet.hidden = false;
    } else {
      bet.hidden = true;
    }

    const delta = document.createElement("div");
    delta.className = "delta-badge";
    renderDelta(delta, seat.delta);

    node.append(plate, cards, rank, delta, bet);
    return node;
  }

  function seatClass(base, seat) {
    let classes = base;
    if (seat.turn) classes += " is-turn";
    if (seat.folded) classes += " is-folded";
    if (seat.winner) classes += " is-winner";
    return classes;
  }

  function renderRank(node, rank) {
    if (rank) {
      node.textContent = rank;
      node.hidden = false;
    } else {
      node.textContent = "";
      node.hidden = true;
    }
  }

  function setBet(node, bet) {
    if (Number(bet) > 0) {
      node.textContent = String(bet);
      node.hidden = false;
    } else {
      node.textContent = "";
      node.hidden = true;
    }
  }

  function renderDelta(node, delta) {
    if (delta === null || delta === undefined) {
      hideDelta(node);
      return;
    }
    node.textContent = signed(delta);
    node.hidden = false;
    node.classList.toggle("is-negative", Number(delta) < 0);
    node.classList.toggle("is-zero", Number(delta) === 0);
  }

  function hideDelta(node) {
    node.textContent = "";
    node.hidden = true;
    node.classList.remove("is-negative", "is-zero");
  }

  function renderHoleCards(container, cards, animate, mucked) {
    const nodes = [];
    if (cards && cards.length) {
      cards.forEach((card, index) => {
        nodes.push(cardNode(card, { animate: animate && index < 2, mucked }));
      });
    } else {
      nodes.push(cardNode(null, { hidden: true, animate, mucked }));
      nodes.push(cardNode(null, { hidden: true, animate, mucked }));
    }
    container.replaceChildren(...nodes);
  }

  function renderBoard(board, animateFrom) {
    const nodes = [];
    for (let index = 0; index < 5; index += 1) {
      if (index < board.length) {
        nodes.push(cardNode(board[index], { animate: index >= animateFrom }));
      } else {
        nodes.push(slotNode());
      }
    }
    els.board.replaceChildren(...nodes);
  }

  function slotNode() {
    const node = document.createElement("div");
    node.className = "card-slot";
    node.setAttribute("aria-hidden", "true");
    return node;
  }

  function cardNode(code, options = {}) {
    const node = document.createElement("div");
    node.className = "card";

    if (!code || options.hidden) {
      node.classList.add("is-hidden");
      if (options.animate) node.classList.add("is-new");
      if (options.mucked) node.classList.add("is-mucked");
      const mark = document.createElement("span");
      mark.className = "back-mark";
      mark.textContent = "♠";
      node.append(mark);
      node.setAttribute("role", "img");
      node.setAttribute("aria-label", options.mucked ? "Mucked card" : "Hidden card");
      return node;
    }

    const rank = code.slice(0, -1);
    const suit = code.slice(-1).toLowerCase();
    const rankLabel = RANK_LABELS[rank] || rank;
    const symbol = SUITS[suit] || "?";
    if (RED_SUITS.has(suit)) node.classList.add("is-red");
    if (options.animate) node.classList.add("is-new");
    if (options.mucked) node.classList.add("is-mucked");

    const corner = document.createElement("span");
    corner.className = "corner";
    const rankNode = document.createElement("span");
    rankNode.textContent = rankLabel;
    const cornerSuit = document.createElement("span");
    cornerSuit.className = "suit";
    cornerSuit.textContent = symbol;
    corner.append(rankNode, cornerSuit);

    const pip = document.createElement("span");
    pip.className = "pip";
    pip.textContent = symbol;

    node.append(corner, pip);
    node.setAttribute("role", "img");
    node.setAttribute("aria-label", rankLabel + " of " + (SUIT_NAMES[suit] || suit));
    return node;
  }

  function lastActionText(entry) {
    if (!entry) return "";
    return (STREET_NAMES[entry.street] || prettify(entry.street)) + " · " + entry.label;
  }

  function renderSidebar() {
    const hand = state.hand;
    const match = state.match;
    els.sidebarHand.textContent = hand ? "Hand " + hand.hand_number : "—";

    const fragment = document.createDocumentFragment();
    if (!match || !hand) {
      const empty = document.createElement("p");
      empty.className = "log-empty";
      empty.textContent = "Choose an opponent to deal the first hand.";
      fragment.append(empty);
      els.logScroll.replaceChildren(fragment);
      state.logLength = -1;
      return;
    }

    const history = hand.history || [];
    let street = null;
    for (const entry of history) {
      if (entry.street !== street) {
        street = entry.street;
        const head = document.createElement("div");
        head.className = "log-street";
        head.textContent = STREET_NAMES[street] || prettify(street);
        fragment.append(head);
      }
      const row = document.createElement("div");
      row.className = "log-row" + (entry.seat === hand.human.seat ? " is-you" : "");
      const dot = document.createElement("span");
      dot.className = "log-dot";
      const actor = document.createElement("span");
      actor.className = "log-actor";
      actor.textContent = entry.short || entry.name || "Seat";
      const action = document.createElement("span");
      action.className = "log-action";
      action.textContent = entry.label;
      const pot = document.createElement("span");
      pot.className = "log-pot";
      pot.textContent = "pot " + entry.pot;
      row.append(dot, actor, action, pot);
      fragment.append(row);
    }

    if (!history.length) {
      const empty = document.createElement("p");
      empty.className = "log-empty";
      empty.textContent = "The blinds are posted. Waiting for the first action.";
      fragment.append(empty);
    }

    if (hand.over && hand.result) {
      const box = document.createElement("div");
      box.className = "log-result";
      const label = document.createElement("strong");
      label.textContent = "Result";
      const message = document.createElement("div");
      message.textContent = hand.result.message;
      const delta = document.createElement("div");
      delta.className = "log-delta";
      delta.textContent =
        "You " + signed(hand.result.human_delta) +
        " · Table " + signed(hand.result.opponents_delta);
      box.append(label, message, delta);
      fragment.append(box);
    }

    const length = history.length + (hand.over ? 1 : 0);
    els.logScroll.replaceChildren(fragment);
    if (length !== state.logLength) {
      state.logLength = length;
      window.requestAnimationFrame(() => {
        els.logScroll.scrollTop = els.logScroll.scrollHeight;
      });
    }
  }

  function renderLeagueCard() {
    els.leagueCard.replaceChildren();
    const match = state.match;

    if (!match) {
      const table =
        state.league && state.shape ? state.league.shapes[state.shape] : null;
      els.leagueCard.append(
        eyebrow("The table"),
        heading(table ? table.label : "Fixed-limit hold'em", 3),
        paragraph(
          table
            ? table.seats + " seats, " + table.starting_stack +
              " chips each, blinds " + table.blinds.join("/") + "."
            : "Choose a table and a league member to deal in.",
        ),
        metaGrid(
          table
            ? [
                ["Seats", String(table.seats)],
                ["Stacks", String(table.starting_stack)],
                ["Blinds", table.blinds.join(" / ")],
                ["Raises", table.raise_cap ? String(table.raise_cap) : "no cap"],
              ]
            : [
                ["Game", "Hold'em"],
                ["Stacks", "—"],
                ["Blinds", "—"],
                ["Raises", "—"],
              ],
        ),
      );
      return;
    }

    const head = document.createElement("div");
    head.className = "league-card-head";
    head.append(eyebrow("Opponent"));
    const change = document.createElement("button");
    change.type = "button";
    change.className = "link-btn";
    change.textContent = "Change";
    change.setAttribute("data-open-league", "");
    head.append(change);

    const title = heading(match.label, 3);
    els.leagueCard.append(head, title);

    const sub = document.createElement("p");
    sub.className = "league-card-sub";
    sub.textContent =
      match.shape_label + " · " + match.seats + " seats · seed " + match.seed;
    els.leagueCard.append(sub);

    const description = document.createElement("p");
    description.className = "league-card-desc";
    if (match.lineup_mode === "mixed") {
      description.textContent =
        "A seeded mix of the league: the selected member plus other checkpoints and fixed policies.";
    } else {
      description.textContent = match.opponent.description;
    }
    els.leagueCard.append(description);

    if (match.opponents.length > 1) {
      const lineup = document.createElement("div");
      lineup.className = "lineup";
      for (const row of match.opponents) {
        const item = document.createElement("div");
        item.className = "lineup-row";
        const position = document.createElement("span");
        position.className = "lineup-pos";
        position.textContent = SHORT_POSITIONS[row.position] || row.position;
        const name = document.createElement("span");
        name.className = "lineup-name";
        name.textContent = row.short || row.name;
        name.title = row.name;
        const kind = document.createElement("span");
        kind.className = "lineup-kind";
        kind.textContent = row.kind === "model" ? "model" : "fixed";
        item.append(position, name, kind);
        lineup.append(item);
      }
      els.leagueCard.append(lineup);
    }

    const rows = [
      ["Seats", String(match.seats)],
      ["Blinds", match.config.blinds.join(" / ")],
      ["Stack", String(match.config.starting_stack)],
      ["Hands", String(match.hands_started)],
      ["Record", recordLine(match.record)],
      ["Session", signed(match.score.human)],
    ];
    if (match.opponents.length === 1) {
      const member = match.opponents[0];
      rows.splice(
        4,
        0,
        ["Params", formatNumber(member.params)],
        ["Seed", member.seed === null || member.seed === undefined ? "—" : String(member.seed)],
      );
    }
    els.leagueCard.append(metaGrid(rows));
  }

  function renderActions() {
    els.actions.replaceChildren();
    els.actionbar.classList.toggle("is-busy", state.busy);

    const meta = document.createElement("div");
    meta.className = "hand-meta";
    els.handMeta.replaceChildren(meta);

    const match = state.match;
    const hand = state.hand;

    if (state.busy) {
      setHint(
        "Working",
        hand && hand.over ? "Dealing the next hand…" : "Resolving the decision…",
        "The table will be back in a moment.",
      );
      els.actions.append(disabledButton(hand && hand.over ? "Dealing…" : "Thinking…"));
      appendMeta(meta, defaultMeta(match, hand));
      return;
    }

    if (!match || !hand) {
      const table =
        state.league && state.shape ? state.league.shapes[state.shape] : null;
      setHint(
        "Welcome",
        "Choose an opponent",
        state.league
          ? state.league.models.length + " checkpoints and " +
            state.league.baselines.length + " deterministic policies are waiting."
          : "Opening the table…",
      );
      const choose = document.createElement("button");
      choose.type = "button";
      choose.className = "btn btn-primary";
      choose.textContent = "Choose an opponent";
      choose.addEventListener("click", openDrawer);
      els.actions.append(choose);
      appendMeta(meta, table ? tableMeta(table) : defaultMeta(match, hand));
      return;
    }

    if (hand.over && hand.result) {
      const result = hand.result;
      setHint(
        "Hand complete",
        result.message,
        "Hand " + hand.hand_number + " · pot " + result.pot + " · " + recordLine(match.record),
      );

      const next = document.createElement("button");
      next.type = "button";
      next.className = "btn btn-primary";
      next.dataset.next = "";
      next.append(document.createTextNode("Next hand"), kbd("↵"));
      els.actions.append(next);

      const change = document.createElement("button");
      change.type = "button";
      change.className = "btn btn-ghost";
      change.textContent = "Change opponent";
      change.addEventListener("click", openDrawer);
      els.actions.append(change);

      appendMeta(meta, [
        ["Seat", hand.human.position],
        ["Table", match.shape_label],
        ["Record", recordLine(match.record)],
        ["Session", signed(match.score.human)],
      ]);
      return;
    }

    if (hand.phase === "your_turn") {
      const toCall = Number(hand.to_call) || 0;
      setHint(
        "Your turn",
        hand.hint,
        "Hand " + hand.hand_number + " · " +
          (STREET_NAMES[hand.street] || hand.street) +
          " · pot " + hand.pot + (toCall > 0 ? " · to call " + toCall : ""),
      );

      const legal = hand.legal || [];
      const primary = primaryRaise(legal);
      for (const row of legal) {
        let className = "btn";
        let key = "";
        if (row.kind === "fold") {
          className += " btn-danger btn-ghost";
          key = "F";
        } else if (row.kind === "check") {
          className += " btn-primary";
          key = "C";
        } else if (primary && row.action === primary.action) {
          className += " btn-raise";
          key = "R";
        } else {
          className += " btn-ghost";
        }
        const button = document.createElement("button");
        button.type = "button";
        button.className = className;
        button.dataset.action = row.action;
        button.title = row.action;
        button.append(document.createTextNode(row.label));
        if (row.detail) {
          const detail = document.createElement("span");
          detail.className = "btn-sub";
          detail.textContent = row.detail;
          button.append(detail);
        }
        if (key) button.append(kbd(key));
        els.actions.append(button);
      }

      appendMeta(meta, [
        ["Seat", hand.human.position],
        ["Table", match.shape_label],
        ["Record", recordLine(match.record)],
        ["Session", signed(match.score.human)],
      ]);
      return;
    }

    setHint(
      "Opponent turn",
      match.label + " is acting",
      "Hand " + hand.hand_number + " · " +
        (STREET_NAMES[hand.street] || hand.street),
    );
    els.actions.append(disabledButton("Waiting…"));
    appendMeta(meta, defaultMeta(match, hand));
  }

  function primaryRaise(legal) {
    const order = ["raise-half", "raise", "raise-minimum"];
    for (const name of order) {
      const found = legal.find((row) => row.action === name);
      if (found) return found;
    }
    return legal.find((row) => row.kind === "raise") || null;
  }

  function tableMeta(table) {
    return [
      ["Seats", String(table.seats)],
      ["Stacks", String(table.starting_stack)],
      ["Blinds", table.blinds.join(" / ")],
      ["Raises", table.raise_cap ? String(table.raise_cap) : "no cap"],
    ];
  }

  function setHint(eyebrowText, title, sub) {
    els.turnEyebrow.textContent = eyebrowText;
    els.turnTitle.textContent = title;
    els.turnTitle.title = title;
    els.turnSub.textContent = sub;
    els.turnSub.title = sub;
  }

  function defaultMeta(match, hand) {
    if (!match || !hand) {
      const table =
        state.league && state.shape ? state.league.shapes[state.shape] : null;
      return table
        ? tableMeta(table)
        : [
            ["Game", "Hold'em"],
            ["Stacks", "—"],
            ["Blinds", "—"],
            ["Raises", "—"],
          ];
    }
    return [
      ["Seat", hand.human.position],
      ["Table", match.shape_label],
      ["Record", recordLine(match.record)],
      ["Session", signed(match.score.human)],
    ];
  }

  function appendMeta(container, rows) {
    for (const [label, value] of rows) {
      const chip = document.createElement("span");
      chip.className = "meta-chip";
      const name = document.createElement("b");
      name.textContent = label;
      const content = document.createElement("span");
      content.textContent = value;
      chip.append(name, content);
      container.append(chip);
    }
  }

  function disabledButton(label) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "btn";
    button.disabled = true;
    button.textContent = label;
    return button;
  }

  function renderLeagueCounts() {
    if (!state.league) return;
    els.countModels.textContent = String(state.league.models.length);
    els.countBaselines.textContent = String(state.league.baselines.length);
  }

  function renderOpponentList() {
    els.opponentList.replaceChildren();
    if (!state.league) {
      const empty = document.createElement("p");
      empty.className = "opp-empty";
      empty.textContent = "Opening the league…";
      els.opponentList.append(empty);
      return;
    }

    const query = state.query.trim().toLowerCase();
    const matches = (opponent) =>
      !query ||
      [
        opponent.name,
        opponent.subtitle,
        opponent.description,
        opponent.group,
        opponent.source_label,
        opponent.shape_label,
        opponent.step,
        String(opponent.seed),
      ]
        .join(" ")
        .toLowerCase()
        .includes(query);

    const activeId = state.match ? state.match.opponent.id : null;

    if (state.tab === "models") {
      const models = state.league.models.filter(matches);
      if (!models.length) {
        els.opponentList.append(emptyNote());
        return;
      }
      const groups = new Map();
      for (const model of models) {
        const key = model.source_label + "|" + model.group;
        if (!groups.has(key)) groups.set(key, []);
        groups.get(key).push(model);
      }
      for (const rows of groups.values()) {
        const group = document.createElement("section");
        group.className = "opp-group";
        const head = document.createElement("div");
        head.className = "opp-group-head";
        const title = document.createElement("h3");
        title.textContent = rows[0].group;
        const source = document.createElement("span");
        source.className = "source-pill" + (rows[0].source === "probe" ? " is-probe" : "");
        source.textContent = rows[0].source_label;
        const count = document.createElement("span");
        count.className = "opp-group-count";
        count.textContent = rows.length + (rows.length === 1 ? " checkpoint" : " checkpoints");
        head.append(title, source, count);

        const list = document.createElement("div");
        for (const model of rows) list.append(modelRow(model, activeId));
        group.append(head, list);
        els.opponentList.append(group);
      }
      return;
    }

    const baselines = state.league.baselines.filter(matches);
    if (!baselines.length) {
      els.opponentList.append(emptyNote());
      return;
    }
    const group = document.createElement("section");
    group.className = "opp-group";
    const head = document.createElement("div");
    head.className = "opp-group-head";
    const title = document.createElement("h3");
    title.textContent = "Fixed policies";
    const source = document.createElement("span");
    source.className = "source-pill";
    source.textContent = "Any shape";
    const count = document.createElement("span");
    count.className = "opp-group-count";
    count.textContent = baselines.length + " rules";
    head.append(title, source, count);
    const list = document.createElement("div");
    for (const baseline of baselines) list.append(baselineRow(baseline, activeId));
    group.append(head, list);
    els.opponentList.append(group);
  }

  function modelRow(model, activeId) {
    const row = document.createElement("button");
    row.type = "button";
    row.className = "opp-row is-model" + (model.id === activeId ? " is-active" : "");
    row.dataset.id = model.id;
    if (model.id === activeId) row.setAttribute("aria-current", "true");
    if (model.available === false) {
      row.classList.add("is-unavailable");
    }

    const glyph = document.createElement("span");
    glyph.className = "opp-glyph";
    glyph.textContent = "◆";

    const info = document.createElement("span");
    info.className = "opp-info";
    const title = document.createElement("span");
    title.className = "opp-title";
    const seed = model.seed === null || model.seed === undefined ? "?" : model.seed;
    title.append(document.createTextNode("Seed " + seed + " · " + (model.step || "checkpoint")));
    if (model.step === "final") {
      const badge = document.createElement("span");
      badge.className = "opp-badge";
      badge.textContent = "final";
      title.append(badge);
    }
    const sub = document.createElement("span");
    sub.className = "opp-sub";
    sub.textContent =
      formatNumber(model.params) + " params · " + model.shape_label +
      " · " + (model.backend === "torch" ? "torch" : "numpy");
    info.append(title, sub);

    const go = document.createElement("span");
    go.className = "opp-go";
    go.textContent = model.available === false ? "Unavailable" : "Play";

    row.append(glyph, info, go);
    row.title =
      model.name + "\n" + model.subtitle + "\n" +
      (model.available === false ? model.unavailable_reason : model.path || "");
    return row;
  }

  function baselineRow(baseline, activeId) {
    const row = document.createElement("button");
    row.type = "button";
    row.className = "opp-row" + (baseline.id === activeId ? " is-active" : "");
    row.dataset.id = baseline.id;
    if (baseline.id === activeId) row.setAttribute("aria-current", "true");

    const glyph = document.createElement("span");
    glyph.className = "opp-glyph";
    glyph.textContent = "◇";

    const info = document.createElement("span");
    info.className = "opp-info";
    const title = document.createElement("span");
    title.className = "opp-title";
    title.append(document.createTextNode(baseline.name));
    if (baseline.anchor) {
      const badge = document.createElement("span");
      badge.className = "opp-badge is-anchor";
      badge.textContent = "anchor";
      title.append(badge);
    }
    const sub = document.createElement("span");
    sub.className = "opp-sub";
    sub.textContent = baseline.description || "Fixed policy";
    info.append(title, sub);

    const go = document.createElement("span");
    go.className = "opp-go";
    go.textContent = "Play";

    row.append(glyph, info, go);
    row.title = baseline.name + "\n" + (baseline.description || "");
    return row;
  }

  function emptyNote() {
    const empty = document.createElement("p");
    empty.className = "opp-empty";
    empty.textContent = "No league member matches that search.";
    return empty;
  }

  /* --- drawer / log ------------------------------------------------------ */

  function openDrawer() {
    state.query = "";
    els.search.value = "";
    renderOpponentList();
    els.body.classList.remove("log-open");
    els.body.classList.add("drawer-open");
    els.drawer.setAttribute("aria-hidden", "false");
    els.restartBtn.disabled = !state.match || state.busy;
    updateDrawerNote();
  }

  function closeDrawer() {
    els.body.classList.remove("drawer-open");
    els.drawer.setAttribute("aria-hidden", "true");
  }

  function openLog() {
    els.body.classList.remove("drawer-open");
    els.body.classList.add("log-open");
  }

  function closeLog() {
    els.body.classList.remove("log-open");
  }

  /* --- small helpers ----------------------------------------------------- */

  function signed(number) {
    const value = Number(number) || 0;
    if (value > 0) return "+" + value;
    if (value < 0) return "−" + Math.abs(value);
    return "0";
  }

  function recordLine(record) {
    if (!record) return "0–0–0";
    return record.wins + "–" + record.losses + "–" + record.ties;
  }

  function formatNumber(value) {
    const number = Number(value) || 0;
    return number.toLocaleString("en-US");
  }

  function prettify(text) {
    return String(text || "")
      .replace(/[-_]/g, " ")
      .replace(/\b\w/g, (letter) => letter.toUpperCase());
  }

  function eyebrow(text) {
    const node = document.createElement("p");
    node.className = "eyebrow";
    node.textContent = text;
    return node;
  }

  function heading(text, level) {
    const node = document.createElement("h" + level);
    node.textContent = text;
    return node;
  }

  function paragraph(text) {
    const node = document.createElement("p");
    node.className = "league-card-desc";
    node.textContent = text;
    return node;
  }

  function metaGrid(rows) {
    const grid = document.createElement("dl");
    grid.className = "meta-grid";
    for (const [label, value] of rows) {
      const item = document.createElement("div");
      const term = document.createElement("dt");
      term.textContent = label;
      const detail = document.createElement("dd");
      detail.textContent = value;
      detail.title = value;
      item.append(term, detail);
      grid.append(item);
    }
    return grid;
  }

  function kbd(text) {
    const node = document.createElement("span");
    node.className = "kbd";
    node.textContent = text;
    return node;
  }

  function toast(message, isError = false) {
    window.clearTimeout(state.toastTimer);
    els.toast.textContent = message;
    els.toast.classList.toggle("is-error", Boolean(isError));
    els.toast.classList.add("is-on");
    state.toastTimer = window.setTimeout(() => {
      els.toast.classList.remove("is-on");
    }, 3800);
  }

  /* The table's two dialogs are mutually exclusive when the window changes. */
  window.addEventListener("resize", () => {
    if (window.innerWidth > 960) {
      els.body.classList.remove("log-open");
    }
  });
})();
