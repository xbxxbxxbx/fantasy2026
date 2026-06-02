const config = window.LEADERBOARD_CONFIG;

const elements = {
  leagueName: document.querySelector("#league-name"),
  leagueDescription: document.querySelector("#league-description"),
  statusBanner: document.querySelector("#status-banner"),
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

function formatPercent(value) {
  return `${Math.round(value)}%`;
}

function buildAnalytics(managers) {
  const teamCount = managers.length;
  const playerMap = new Map();

  for (const manager of managers) {
    for (const player of manager.players) {
      const key = canonicalPlayerName(player.player);
      const existing = playerMap.get(key) || {
        player: key,
        points: 0,
        owners: [],
      };
      existing.points = Math.max(existing.points, parseNumber(player.points));
      existing.owners.push(manager.name);
      playerMap.set(key, existing);
    }
  }

  const ownershipRows = Array.from(playerMap.values())
    .map((entry) => ({
      player: entry.player,
      points: entry.points,
      ownerCount: entry.owners.length,
      ownershipPercent: (entry.owners.length / teamCount) * 100,
      owners: [...entry.owners].sort(),
    }))
    .sort(
      (left, right) =>
        right.ownerCount - left.ownerCount ||
        right.points - left.points ||
        left.player.localeCompare(right.player)
    );

  const playerOwnerCount = new Map(
    ownershipRows.map((row) => [canonicalPlayerName(row.player), row.ownerCount])
  );
  const leader = managers[0] || null;
  const leaderPlayers = new Set((leader?.players || []).map((player) => canonicalPlayerName(player.player)));

  const overlapRows = managers.map((manager) => {
    const playerSet = new Set(manager.players.map((player) => canonicalPlayerName(player.player)));
    const rivals = managers
      .filter((rival) => rival.name !== manager.name)
      .map((rival) => {
        const sharedPlayers = rival.players
          .map((player) => canonicalPlayerName(player.player))
          .filter((playerName) => playerSet.has(playerName))
          .sort((left, right) => {
            const leftPoints = ownershipRows.find((row) => row.player === left)?.points || 0;
            const rightPoints = ownershipRows.find((row) => row.player === right)?.points || 0;
            return rightPoints - leftPoints || left.localeCompare(right);
          });
        return {
          rivalName: rival.name,
          overlapCount: sharedPlayers.length,
          sharedPlayers,
        };
      })
      .sort(
        (left, right) =>
          right.overlapCount - left.overlapCount ||
          left.rivalName.localeCompare(right.rivalName)
      );

    return {
      team: manager.name,
      teamName: manager.teamName,
      bestRival: rivals[0] || null,
      rivals,
    };
  });

  const routeRows = managers.map((manager, index) => {
    const uniquePlayers = [];
    const sharedPlayers = [];
    let uniquePoints = 0;
    let semiSharedPoints = 0;
    let crowdedPoints = 0;

    for (const player of manager.players) {
      const playerName = canonicalPlayerName(player.player);
      const ownerCount = playerOwnerCount.get(playerName) || 1;
      const points = parseNumber(player.points);

      if (ownerCount === 1) {
        uniquePlayers.push(playerName);
        uniquePoints += points;
      } else {
        sharedPlayers.push(playerName);
        if (ownerCount === 2) {
          semiSharedPoints += points;
        } else {
          crowdedPoints += points;
        }
      }
    }

    const managerPlayerSet = new Set(manager.players.map((player) => canonicalPlayerName(player.player)));
    const leadersSharedPlayers = Array.from(managerPlayerSet).filter((player) => leaderPlayers.has(player));
    const leadersSharedWithTeam = leadersSharedPlayers.length;
    const leadersSharedAgainstTeam = (leader?.players || [])
      .filter((player) => managerPlayerSet.has(canonicalPlayerName(player.player)))
      .reduce((sum, player) => sum + parseNumber(player.points), 0);
    const higherTeams = managers.slice(0, index);
    const blockedOverlapCount = higherTeams.reduce((sum, higherTeam) => {
      const higherSet = new Set(
        higherTeam.players.map((player) => canonicalPlayerName(player.player))
      );
      return (
        sum +
        Array.from(managerPlayerSet).filter((player) => higherSet.has(player)).length
      );
    }, 0);
    const sharedPoints = semiSharedPoints + crowdedPoints;
    const uniqueShare = manager.totalPoints > 0 ? uniquePoints / manager.totalPoints : 0;
    const chaseGap = leader ? leader.totalPoints - manager.totalPoints : 0;

    let routeSummary = "Needs both shared stars to hold and one or two unique draftees to separate.";
    if (index === 0) {
      routeSummary =
        uniquePoints > sharedPoints
          ? "Controls its own path; gains from continued scoring by unique core."
          : "Still leading, but shared draftees let trailing teams keep pace.";
    } else if (leadersSharedWithTeam >= 3 || leadersSharedAgainstTeam > manager.totalPoints * 0.5) {
      routeSummary =
        "Needs non-shared production because leader gains from many of the same scores.";
    } else if (uniqueShare >= 0.35 || uniquePlayers.length >= 3) {
      routeSummary =
        "Has live outs if unique draftees surge; less blocked by leaders.";
    }

    return {
      ...manager,
      rank: index + 1,
      uniquePlayerCount: uniquePlayers.length,
      sharedPlayerCount: sharedPlayers.length,
      uniquePoints,
      semiSharedPoints,
      crowdedPoints,
      sharedPoints,
      leadersSharedWithTeam,
      leadersSharedAgainstTeam,
      chaseGap,
      routeSummary,
      uniqueShare,
      blockedOverlapCount,
    };
  });

  const bestLeverageTeams = [...routeRows]
    .sort(
      (left, right) =>
        right.uniqueShare - left.uniqueShare ||
        right.uniquePoints - left.uniquePoints ||
        left.rank - right.rank
    )
    .slice(0, 3);

  const mostBlockedTeams = [...routeRows]
    .sort(
      (left, right) =>
        right.blockedOverlapCount - left.blockedOverlapCount ||
        right.leadersSharedAgainstTeam - left.leadersSharedAgainstTeam ||
        left.rank - right.rank
    )
    .slice(0, 3);

  return {
    ownershipRows,
    overlapRows,
    routeRows,
    bestLeverageTeams,
    mostBlockedTeams,
  };
}

function renderOwnership(ownershipRows) {
  elements.ownershipBody.innerHTML = ownershipRows
    .map((row) => {
      const bucketClass =
        row.ownerCount === 1 ? "ownership-unique" : row.ownerCount === 2 ? "ownership-shared" : "ownership-crowded";
      return `
        <tr>
          <td>${escapeHtml(row.player)}</td>
          <td class="points-cell">${Math.round(row.points)}</td>
          <td>${row.ownerCount}</td>
          <td><span class="ownership-pill ${bucketClass}">${formatPercent(row.ownershipPercent)}</span></td>
          <td class="teams-cell">${escapeHtml(row.owners.join(", "))}</td>
        </tr>
      `;
    })
    .join("");
}

function renderOverlap(overlapRows) {
  elements.overlapGrid.innerHTML = overlapRows
    .map((row) => {
      const bestRivalName = row.bestRival?.rivalName || "None";
      const bestRivalCount = row.bestRival?.overlapCount || 0;
      return `
        <article class="overlap-card">
          <div class="card-header">
            <div>
              <h3>${escapeHtml(row.team)}</h3>
              <p class="player-meta">${escapeHtml(row.teamName)}</p>
            </div>
            <div class="overlap-highlight">${bestRivalCount} with ${escapeHtml(bestRivalName)}</div>
          </div>
          <div class="overlap-list">
            ${row.rivals
              .map(
                (rival) => `
                  <div class="overlap-row ${rival.rivalName === bestRivalName ? "is-top-rival" : ""}">
                    <div>
                      <div class="player-name">${escapeHtml(rival.rivalName)}</div>
                      <div class="player-meta">${escapeHtml(
                        rival.sharedPlayers.slice(0, 3).join(", ") || "No shared players"
                      )}</div>
                    </div>
                    <div class="overlap-count">${rival.overlapCount}</div>
                  </div>
                `
              )
              .join("")}
          </div>
        </article>
      `;
    })
    .join("");
}

function renderRouteLists(bestLeverageTeams, mostBlockedTeams) {
  elements.bestLeverageList.innerHTML = bestLeverageTeams
    .map(
      (team) => `
        <li>${escapeHtml(team.name)} <span>${Math.round(team.uniquePoints)} unique pts</span></li>
      `
    )
    .join("");
  elements.mostBlockedList.innerHTML = mostBlockedTeams
    .map(
      (team) => `
        <li>${escapeHtml(team.name)} <span>${team.blockedOverlapCount} shared with teams ahead</span></li>
      `
    )
    .join("");
}

function renderRoutes(routeRows) {
  elements.routesGrid.innerHTML = routeRows
    .map(
      (team) => `
        <article class="route-card">
          <div class="card-header">
            <div>
              <p class="section-kicker">Rank #${team.rank}</p>
              <h3>${escapeHtml(team.name)}</h3>
            </div>
            <div class="card-total">${Math.round(team.totalPoints)} pts</div>
          </div>
          <p class="route-summary">${escapeHtml(team.routeSummary)}</p>
          <div class="route-metrics">
            <div class="route-metric"><span>Unique players</span><strong>${team.uniquePlayerCount}</strong></div>
            <div class="route-metric"><span>Shared players</span><strong>${team.sharedPlayerCount}</strong></div>
            <div class="route-metric"><span>Unique points</span><strong>${Math.round(team.uniquePoints)}</strong></div>
            <div class="route-metric"><span>Shared points</span><strong>${Math.round(team.sharedPoints)}</strong></div>
            <div class="route-metric"><span>Leader overlap</span><strong>${team.leadersSharedWithTeam}</strong></div>
            <div class="route-metric"><span>Gap to first</span><strong>${Math.round(team.chaseGap)}</strong></div>
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

function formatUpdatedAt(value) {
  const date = new Date(value);
  return new Intl.DateTimeFormat("en-US", {
    month: "long",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(date);
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

function initializeCollapsiblePanels() {
  document.querySelectorAll(".collapse-button").forEach((button) => {
    button.addEventListener("click", () => {
      const targetId = button.getAttribute("data-target");
      const content = targetId ? document.getElementById(targetId) : null;
      if (!content) {
        return;
      }

      const isCollapsed = content.classList.toggle("is-collapsed");
      button.setAttribute("aria-expanded", String(!isCollapsed));
      button.textContent = isCollapsed ? "Expand" : "Collapse";
    });
  });
}

function expandSectionFromNav(hash) {
  if (!hash || hash === "#top") {
    return null;
  }

  const section = document.querySelector(hash);
  if (!section) {
    return null;
  }

  const content = section.querySelector(".panel-content");
  const button = section.querySelector(".collapse-button");
  if (!content || !button || !content.classList.contains("is-collapsed")) {
    return section;
  }

  content.classList.remove("is-collapsed");
  button.setAttribute("aria-expanded", "true");
  button.textContent = "Collapse";
  return section;
}

function updateBackToTopVisibility() {
  if (!elements.backToTop) {
    return;
  }

  const shouldShow = window.scrollY > 320;
  elements.backToTop.classList.toggle("is-visible", shouldShow);
}

async function loadLeaderboard({ manual = false } = {}) {
  const existingStatus = elements.statusBanner.textContent.trim();
  const existingState = elements.statusBanner.className.replace("status-banner", "").trim();
  if (!existingStatus) {
    setStatus("Loading latest leaderboard snapshot...", "status-loading");
  }

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
    const analytics = buildAnalytics(managers);
    renderOwnership(analytics.ownershipRows);
    renderOverlap(analytics.overlapRows);
    renderRouteLists(analytics.bestLeverageTeams, analytics.mostBlockedTeams);
    renderRoutes(analytics.routeRows);

    if (snapshot.generatedAt) {
      setStatus(`Last updated ${formatUpdatedAt(snapshot.generatedAt)}.`, "status-ok");
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
    renderOwnership([]);
    renderOverlap([]);
    renderRouteLists([], []);
    renderRoutes([]);
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
}

renderHeaderStats();
initializeCollapsiblePanels();
document.querySelectorAll(".section-nav-link").forEach((link) => {
  link.addEventListener("click", (event) => {
    const hash = link.getAttribute("href");
    if (!hash) {
      return;
    }

    event.preventDefault();
    const section = expandSectionFromNav(hash);
    if (!section) {
      return;
    }

    section.scrollIntoView({ behavior: "smooth", block: "start" });
    window.history.replaceState(null, "", hash);
  });
});
window.addEventListener("scroll", updateBackToTopVisibility, { passive: true });
updateBackToTopVisibility();
loadLeaderboard();
