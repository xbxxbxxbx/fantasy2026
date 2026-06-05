(function (app) {
  app.slugify = function slugify(value) {
    return String(value || "")
      .trim()
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "");
  };

  app.normalizeName = function normalizeName(value) {
    return String(value || "")
      .trim()
      .replace(/\s+/g, " ")
      .toLowerCase();
  };

  app.canonicalPlayerName = function canonicalPlayerName(name) {
    return String(name || "").trim();
  };

  app.escapeHtml = function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  };

  app.parseNumber = function parseNumber(value) {
    if (typeof value === "number") {
      return value;
    }

    const cleaned = String(value || "")
      .replace(/[$,%]/g, "")
      .replace(/\(([^)]+)\)/g, "-$1")
      .replace(/[^\d.-]/g, "");
    const parsed = Number.parseFloat(cleaned);
    return Number.isFinite(parsed) ? parsed : 0;
  };

  app.formatPercent = function formatPercent(value) {
    return `${Math.round(value)}%`;
  };

  app.formatAmericanOdds = function formatAmericanOdds(value) {
    if (!Number.isFinite(value)) {
      return "—";
    }
    if (value > 0) {
      return `+${Math.round(value)}`;
    }
    return `${Math.round(value)}`;
  };

  app.snapshotSignature = function snapshotSignature(snapshot) {
    return JSON.stringify({
      generatedAt: snapshot.generatedAt || null,
      managers: (snapshot.managers || []).map((manager) => ({
        managerName: manager.managerName,
        teamName: manager.teamName,
        totalPoints: app.parseNumber(manager.totalPoints),
        titleWinProbability: app.parseNumber(manager.titleWinProbability),
        titleAmericanOdds:
          manager.titleAmericanOdds === null || manager.titleAmericanOdds === undefined
            ? null
            : app.parseNumber(manager.titleAmericanOdds),
        players: (manager.players || []).map((player) => ({
          player: app.canonicalPlayerName(player.player),
          points: app.parseNumber(player.points),
        })),
      })),
    });
  };
})(window.FantasyLeaderboardApp);
