(function (window, document) {
  const app = window.FantasyLeaderboardApp || {};

  app.config = window.LEADERBOARD_CONFIG;
  app.elements = {
    leagueName: document.querySelector("#league-name"),
    leagueDescription: document.querySelector("#league-description"),
    heroPolling: document.querySelector("#hero-polling"),
    liveSweatsNav: document.querySelector("#live-sweats-nav"),
    liveSweatsNavIndicator: document.querySelector("#live-sweats-nav-indicator"),
    liveSweatsSection: document.querySelector("#live-sweats"),
    liveSweatsStatus: document.querySelector("#live-sweats-status"),
    liveSweatsCountdown: document.querySelector("#live-sweats-countdown"),
    liveSweatsBody: document.querySelector("#live-sweats-body"),
    leaderboardHelperLive: document.querySelector(".leaderboard-helper-live"),
    leaderboardHelperLive: document.querySelector("#leaderboard-helper-live"),
    leaderboardBody: document.querySelector("#leaderboard-body"),
    managerCards: document.querySelector("#manager-cards"),
    ownershipBody: document.querySelector("#ownership-body"),
    overlapGrid: document.querySelector("#overlap-grid"),
    routesGrid: document.querySelector("#routes-grid"),
    bestLeverageList: document.querySelector("#best-leverage-list"),
    mostBlockedList: document.querySelector("#most-blocked-list"),
    backToTop: document.querySelector("#back-to-top"),
    refreshToast: document.querySelector("#refresh-toast"),
  };

  app.state = {
    currentPointsChangeLabel: "today",
    lastSnapshotSignature: "",
    lastLiveSweatsAvailability: null,
    latestLiveSweats: [],
    latestManagers: [],
    liveSweatsCountdownTimerId: 0,
    playerHistoryCache: null,
    playerHistoryDismissInitialized: false,
    revealAnimationTimeoutId: 0,
    toastTimeoutId: null,
  };

  window.FantasyLeaderboardApp = app;
})(window, document);
