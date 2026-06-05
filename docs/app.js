(function (app) {
  async function loadLeaderboard({ manual = false } = {}) {
    try {
      const [snapshot, activeSnapshot] = await Promise.all([
        app.fetchSnapshot(),
        app.fetchActivePlayers().catch(() => ({ players: [] })),
      ]);
      const viewModel = app.buildViewModel(snapshot, activeSnapshot);
      app.state.currentPointsChangeLabel = viewModel.pointsChangeLabel;
      const hasChanged =
        app.state.lastSnapshotSignature !== "" &&
        viewModel.signature !== app.state.lastSnapshotSignature;

      app.state.latestManagers = viewModel.managers;
      app.state.latestLiveSweats = viewModel.liveSweats;

      app.renderLiveSweats(viewModel.liveSweats);
      app.renderHeaderStats(viewModel.metadata);
      app.renderLeaderboard(viewModel.managers);
      app.renderManagerCards(viewModel.managers);
      app.initializeRosterJumpLinks();
      app.initializePlayerHistoryWidgets();
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

      if (manual) {
        app.showRefreshToast(
          hasChanged
            ? "Leaderboard updated with new data."
            : "Checked for updates. No score changes yet."
        );
      }

      app.state.lastSnapshotSignature = viewModel.signature;
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
    }
  }

  function initializeApp() {
    app.renderHeaderStats();
    app.initializeCommitEasterEgg();
    app.initializeCollapsiblePanels();
    app.initializeNavigation();
    app.startLiveSweatsCountdown();
    loadLeaderboard();
  }

  app.loadLeaderboard = loadLeaderboard;
  app.initializeApp = initializeApp;

  initializeApp();
})(window.FantasyLeaderboardApp);
