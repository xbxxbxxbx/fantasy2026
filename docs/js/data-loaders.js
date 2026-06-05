(function (app) {
  app.fetchSnapshot = async function fetchSnapshot() {
    const response = await fetch("./data.json", { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`Request failed with ${response.status}`);
    }

    return response.json();
  };

  app.fetchActivePlayers = async function fetchActivePlayers() {
    const response = await fetch("./active-players.json", { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`Active players request failed with ${response.status}`);
    }

    return response.json();
  };

  app.fetchPlayerHistory = async function fetchPlayerHistory() {
    if (app.state.playerHistoryCache) {
      return app.state.playerHistoryCache;
    }

    const response = await fetch("./25k-player-history.json", { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`History request failed with ${response.status}`);
    }

    app.state.playerHistoryCache = await response.json();
    return app.state.playerHistoryCache;
  };

  app.fetchLatestChanges = async function fetchLatestChanges() {
    if (app.state.latestChangesCache) {
      return app.state.latestChangesCache;
    }

    const response = await fetch("./latest-changes.json", { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`Latest changes request failed with ${response.status}`);
    }

    app.state.latestChangesCache = await response.json();
    return app.state.latestChangesCache;
  };
})(window.FantasyLeaderboardApp);
