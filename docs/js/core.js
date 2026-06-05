(function (window, document) {
  const app = window.FantasyLeaderboardApp || {};

  app.config = window.LEADERBOARD_CONFIG;
  app.elements = {
    leagueName: document.querySelector("#league-name"),
    leagueDescription: document.querySelector("#league-description"),
    heroPolling: document.querySelector("#hero-polling"),
    commitEasterEggTrigger: document.querySelector("#commit-easter-egg-trigger"),
    commitEasterEggModal: document.querySelector("#commit-easter-egg-modal"),
    commitEasterEggBackdrop: document.querySelector("#commit-easter-egg-backdrop"),
    commitEasterEggClose: document.querySelector("#commit-easter-egg-close"),
    commitEasterEggBody: document.querySelector("#commit-easter-egg-body"),
    liveSweatsNav: document.querySelector("#live-sweats-nav"),
    liveSweatsNavIndicator: document.querySelector("#live-sweats-nav-indicator"),
    liveSweatsSection: document.querySelector("#live-sweats"),
    liveSweatsStatus: document.querySelector("#live-sweats-status"),
    liveSweatsCountdown: document.querySelector("#live-sweats-countdown"),
    liveSweatsEmpty: document.querySelector("#live-sweats-empty"),
    liveSweatsTable: document.querySelector("#live-sweats-table"),
    liveSweatsBody: document.querySelector("#live-sweats-body"),
    liveSweatsHelperLive: document.querySelector("#live-sweats-helper-live"),
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
    latestChangesCache: null,
    playerHistoryDismissInitialized: false,
    commitEasterEggInitialized: false,
    revealAnimationTimeoutId: 0,
    toastTimeoutId: null,
  };

  window.FantasyLeaderboardApp = app;
})(window, document);
