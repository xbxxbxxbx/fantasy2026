const config = window.LEADERBOARD_CONFIG;

const elements = {
  leagueName: document.querySelector("#league-name"),
  leagueDescription: document.querySelector("#league-description"),
  statusBanner: document.querySelector("#status-banner"),
  leaderboardBody: document.querySelector("#leaderboard-body"),
  managerCards: document.querySelector("#manager-cards"),
  refreshButton: document.querySelector("#refresh-button"),
  refreshToast: document.querySelector("#refresh-toast"),
};

let lastSnapshotSignature = "";
let toastTimeoutId = null;

function normalizeName(value) {
  return String(value || "")
    .trim()
    .replace(/\s+/g, " ")
    .toLowerCase();
}

function canonicalPlayerName(name) {
  return String(name || "").trim();
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function parseNumber(value) {
  if (typeof value === "number") {
    return value;
  }

  const cleaned = String(value || "")
    .replace(/[$,%]/g, "")
    .replace(/\(([^)]+)\)/g, "-$1")
    .replace(/[^\d.-]/g, "");
  const parsed = Number.parseFloat(cleaned);
  return Number.isFinite(parsed) ? parsed : 0;
}

async function fetchSnapshot() {
  const response = await fetch("./data.json", { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Request failed with ${response.status}`);
  }

  return response.json();
}

function renderHeaderStats() {
  elements.leagueName.textContent = config.leagueName;
  elements.leagueDescription.textContent = config.leagueDescription;
}

function renderLeaderboard(managers) {
  elements.leaderboardBody.innerHTML = managers
    .map(
      (manager, index) => `
        <tr>
          <td><span class="rank-badge">${index + 1}</span></td>
          <td>${escapeHtml(manager.name)}</td>
          <td class="points-cell">${Math.round(manager.totalPoints)}</td>
          <td>${manager.teamName ? escapeHtml(manager.teamName) : "-"}</td>
          <td class="view-link-cell">
            <a
              class="view-link"
              href="${escapeHtml(manager.url || "#")}"
              target="_blank"
              rel="noreferrer"
              aria-label="View ${escapeHtml(manager.teamName || manager.name)} on Poker.org"
              title="View on Poker.org"
            >
              <span class="view-link-text">View on</span>
              <img
                class="view-link-icon"
                src="./favicon-32x32.18bb06ad.png"
                alt=""
                aria-hidden="true"
              />
            </a>
          </td>
        </tr>
      `
    )
    .join("");
}

function renderManagerCards(managers) {
  elements.managerCards.innerHTML = managers
    .map(
      (manager) => `
        <article class="manager-card">
          <div class="card-header">
            <div>
              <h3>${escapeHtml(manager.name)}</h3>
            </div>
            <div class="card-total">${Math.round(manager.totalPoints)} pts</div>
          </div>
          <p class="player-meta">${escapeHtml(manager.teamName)}</p>
          <div class="player-list">
            ${manager.players
              .map(
                (player) => `
                  <div class="player-row">
                    <div>
                      <div class="player-name">${escapeHtml(player.player)}</div>
                    </div>
                    <div class="player-points">${Math.round(player.points)}</div>
                  </div>
                `
              )
              .join("")}
          </div>
        </article>
      `
    )
    .join("");
}

function setStatus(message, state) {
  elements.statusBanner.textContent = message;
  elements.statusBanner.className = `status-banner ${state}`;
}

function snapshotSignature(snapshot) {
  return JSON.stringify({
    generatedAt: snapshot.generatedAt || null,
    managers: (snapshot.managers || []).map((manager) => ({
      managerName: manager.managerName,
      teamName: manager.teamName,
      totalPoints: parseNumber(manager.totalPoints),
      players: (manager.players || []).map((player) => ({
        player: canonicalPlayerName(player.player),
        points: parseNumber(player.points),
      })),
    })),
  });
}

function showRefreshToast(message) {
  if (!elements.refreshToast) {
    return;
  }

  elements.refreshToast.textContent = message;
  elements.refreshToast.classList.add("is-visible");

  if (toastTimeoutId) {
    window.clearTimeout(toastTimeoutId);
  }

  toastTimeoutId = window.setTimeout(() => {
    elements.refreshToast.classList.remove("is-visible");
  }, 2600);
}

async function loadLeaderboard({ manual = false } = {}) {
  const existingStatus = elements.statusBanner.textContent.trim();
  const existingState = elements.statusBanner.className.replace("status-banner", "").trim();
  if (!existingStatus) {
    setStatus("Loading latest leaderboard snapshot...", "status-loading");
  }
  elements.refreshButton.disabled = true;

  try {
    const snapshot = await fetchSnapshot();
    const nextSignature = snapshotSignature(snapshot);
    const hasChanged = lastSnapshotSignature !== "" && nextSignature !== lastSnapshotSignature;
    const managers = (snapshot.managers || []).map((manager) => ({
      name: manager.managerName,
      teamName: manager.teamName,
      url: manager.url,
      totalPoints: parseNumber(manager.totalPoints),
      players: (manager.players || []).map((player) => ({
        player: canonicalPlayerName(player.player),
        points: parseNumber(player.points),
      })),
    }));

    elements.leagueName.textContent = snapshot.leagueName || config.leagueName;
    elements.leagueDescription.textContent =
      snapshot.leagueDescription || config.leagueDescription;

    renderLeaderboard(managers);
    renderManagerCards(managers);

    if (snapshot.generatedAt) {
      setStatus(
        `Last updated ${new Date(snapshot.generatedAt).toLocaleString()}.`,
        "status-ok"
      );
    } else {
      setStatus("No data yet. Run the scraper to populate docs/data.json.", "status-loading");
    }

    if (manual) {
      showRefreshToast(
        hasChanged
          ? "Leaderboard updated with new data."
          : "Checked for updates. No score changes yet."
      );
    }

    lastSnapshotSignature = nextSignature;
  } catch (error) {
    renderLeaderboard([]);
    renderManagerCards([]);
    setStatus(
      error instanceof Error ? error.message : "Could not load docs/data.json.",
      "status-error"
    );
    if (manual) {
      showRefreshToast("Refresh failed. Try again in a moment.");
    }
  }

  if (existingStatus && existingState && !elements.statusBanner.textContent.trim()) {
    setStatus(existingStatus, existingState);
  }

  elements.refreshButton.disabled = false;
}

renderHeaderStats();
elements.refreshButton.addEventListener("click", () => loadLeaderboard({ manual: true }));
loadLeaderboard();
