(function (app) {
  app.getNewYorkNow = function getNewYorkNow(now = new Date()) {
    return new Date(now.toLocaleString("en-US", { timeZone: "America/New_York" }));
  };

  app.getLiveSweatsAvailability = function getLiveSweatsAvailability() {
    if (!app.config.liveSweatsTimeGateEnabled) {
      return { isLive: true, countdownText: "" };
    }

    const nyNow = app.getNewYorkNow();
    const target = new Date(nyNow);
    target.setHours(18, 0, 0, 0);
    const isLive = nyNow >= target;

    if (isLive) {
      return { isLive: true, countdownText: "" };
    }

    const diffMs = target.getTime() - nyNow.getTime();
    const totalMinutes = Math.max(0, Math.floor(diffMs / 60000));
    const hours = Math.floor(totalMinutes / 60);
    const minutes = totalMinutes % 60;

    return {
      isLive: false,
      countdownText: `Starting in ${hours} hour${hours === 1 ? "" : "s"} ${minutes} minute${minutes === 1 ? "" : "s"}`,
    };
  };

  app.formatUpdatedAt = function formatUpdatedAt(value) {
    const date = new Date(value);
    return new Intl.DateTimeFormat("en-US", {
      month: "long",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
    }).format(date);
  };
})(window.FantasyLeaderboardApp);
