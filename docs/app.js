(function (app) {
  const AUTO_REFRESH_INTERVAL_MS = 10 * 60 * 1000;
  const EXPECTED_CRON_MINUTES = [3, 13, 23, 33, 43, 53];
  const POST_CRON_REFRESH_DELAY_MINUTES = 2;

  function buildPlayerPointsMap(managers) {
    const playerPoints = new Map();

    for (const manager of managers || []) {
      for (const player of manager.players || []) {
        const playerName = app.canonicalPlayerName(player.player);
        const points = app.parseNumber(player.points);
        const existingPoints = playerPoints.get(playerName);
        if (existingPoints === undefined || points > existingPoints) {
          playerPoints.set(playerName, points);
        }
      }
    }

    return playerPoints;
  }

  function getPointGains(previousPoints, nextPoints) {
    if (!previousPoints) {
      return [];
    }

    return Array.from(nextPoints.entries())
      .map(([player, totalPoints]) => {
        const previousTotal = previousPoints.get(player);
        const pointsGained =
          previousTotal === undefined ? 0 : app.parseNumber(totalPoints) - app.parseNumber(previousTotal);
        return {
          player,
          pointsGained,
          totalPoints,
        };
      })
      .filter((gain) => gain.pointsGained > 0)
      .sort(
        (left, right) =>
          right.pointsGained - left.pointsGained ||
          right.totalPoints - left.totalPoints ||
          left.player.localeCompare(right.player)
      );
  }

  function getNextPostCronRefreshDelay(now = new Date()) {
    const refreshMinutes = EXPECTED_CRON_MINUTES.map(
      (minute) => (minute + POST_CRON_REFRESH_DELAY_MINUTES) % 60
    );

    for (const minute of refreshMinutes) {
      const next = new Date(now);
      next.setMinutes(minute, 0, 0);
      if (next.getTime() > now.getTime()) {
        return next.getTime() - now.getTime();
      }
    }

    const next = new Date(now);
    next.setHours(next.getHours() + 1, refreshMinutes[0], 0, 0);
    return next.getTime() - now.getTime();
  }

  async function loadLeaderboard({ manual = false } = {}) {
    if (app.state.refreshInFlight) {
      return;
    }

    app.state.refreshInFlight = true;

    try {
      const [snapshot, activeSnapshot] = await Promise.all([
        app.fetchSnapshot(),
        app.fetchActivePlayers().catch(() => ({ players: [] })),
      ]);
      const viewModel = app.buildViewModel(snapshot, activeSnapshot);
      app.state.currentPointsChangeLabel = viewModel.pointsChangeLabel;
      app.state.latestPointsChangeComparisonDate = viewModel.pointsChangeComparisonDate;
      const hasChanged =
        app.state.lastSnapshotSignature !== "" &&
        viewModel.signature !== app.state.lastSnapshotSignature;

      app.state.latestManagers = viewModel.managers;
      app.state.latestLiveSweats = viewModel.liveSweats;

      const nextPlayerPoints = buildPlayerPointsMap(viewModel.managers);
      const pointGains = getPointGains(app.state.latestPlayerPointsByName, nextPlayerPoints);

      app.renderLiveSweats(viewModel.liveSweats);
      app.renderHeaderStats(viewModel.metadata);
      app.renderLeaderboard(viewModel.managers);
      app.renderManagerCards(viewModel.managers);
      app.renderOwnership(viewModel.analytics.ownershipRows);
      app.renderOverlap(viewModel.analytics.overlapRows);
      app.renderRouteLists(
        viewModel.analytics.bestLeverageTeams,
        viewModel.analytics.mostBlockedTeams
      );
      app.renderRoutes(viewModel.analytics.routeRows);

      if (app.elements.heroPolling && viewModel.generatedAt) {
        app.elements.heroPolling.textContent = `Updated ${app.formatUpdatedAt(viewModel.generatedAt)}`;
      }
      app.setStatus();

      if (manual) {
        app.showRefreshToast(
          hasChanged
            ? "Leaderboard updated with new data."
            : "Checked for updates. No score changes yet."
        );
      }

      if (pointGains.length) {
        app.showPointGainsToast(pointGains);
      }

      app.state.lastSnapshotSignature = viewModel.signature;
      app.state.latestPlayerPointsByName = nextPlayerPoints;
    } catch (error) {
      app.state.latestManagers = [];
      app.state.latestLiveSweats = [];
      app.renderLiveSweats([]);
      app.renderLeaderboard([]);
      app.renderManagerCards([]);
      app.renderOwnership([]);
      app.renderOverlap([]);
      app.renderRouteLists([], []);
      app.renderRoutes([]);
      app.setStatus(
        error instanceof Error ? error.message : "Could not load docs/data.json.",
        "status-error"
      );
      if (manual) {
        app.showRefreshToast("Refresh failed. Try again in a moment.");
      }
    } finally {
      app.state.refreshInFlight = false;
    }
  }

  function startAutoRefresh() {
    if (app.state.refreshStartTimeoutId || app.state.refreshIntervalId) {
      return;
    }

    app.state.refreshStartTimeoutId = window.setTimeout(() => {
      loadLeaderboard();
      app.state.refreshIntervalId = window.setInterval(loadLeaderboard, AUTO_REFRESH_INTERVAL_MS);
    }, getNextPostCronRefreshDelay());
  }

  function initializeRefreshToastTestTrigger() {
    const testTrigger = document.querySelector("#refresh-toast-test");
    if (!testTrigger || app.state.refreshToastTestInitialized) {
      return;
    }

    const testPlayers = [
      "Phil Ivey",
      "Kristen Foxen",
      "Daniel Negreanu",
      "Maria Ho",
      "Jason Koon",
      "Vanessa Selbst",
    ];

    testTrigger.addEventListener("click", () => {
      const shuffledPlayers = [...testPlayers].sort(() => Math.random() - 0.5);
      const gainCount = 1 + Math.floor(Math.random() * 3);
      const gains = shuffledPlayers.slice(0, gainCount).map((player) => {
        const pointsGained = 1 + Math.floor(Math.random() * 12);
        return {
          player,
          pointsGained,
          totalPoints: pointsGained + 20 + Math.floor(Math.random() * 240),
        };
      });
      app.showPointGainsToast(gains);
    });

    app.state.refreshToastTestInitialized = true;
  }

  async function initializeConfig() {
    if (window.LEADERBOARD_CONFIG_READY) {
      app.config = await window.LEADERBOARD_CONFIG_READY;
    } else {
      app.config = window.LEADERBOARD_CONFIG || app.config || {};
    }
    app.renderHeaderStats();
    app.startLiveSweatsCountdown();
  }

  function initializeApp() {
    app.initializeCommitEasterEgg();
    app.initializeCollapsiblePanels();
    app.initializeNavigation();
    app.initializeRosterJumpLinks();
    app.initializePointContributorModal();
    app.initializePlayerHistoryWidgets();
    initializeRefreshToastTestTrigger();
    initializeConfig();
    loadLeaderboard();
    startAutoRefresh();
  }

  app.loadLeaderboard = loadLeaderboard;
  app.initializeApp = initializeApp;

  initializeApp();
})(window.FantasyLeaderboardApp);
