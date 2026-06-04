(function (app, document, window) {
  app.renderHeaderStats = function renderHeaderStats() {
    app.elements.leagueName.textContent = app.config.leagueName;
    if (app.elements.leagueDescription) {
      const sourceLabel = app.escapeHtml(app.config.sourceLabel || "source");
      const sourceUrl = app.escapeHtml(app.config.sourceUrl || "#");
      const updateCadenceLabel = app.escapeHtml(app.config.updateCadenceLabel || "regularly");
      app.elements.leagueDescription.innerHTML = `Live leaderboard from <a href="${sourceUrl}" target="_blank" rel="noreferrer">${sourceLabel}</a> updated ${updateCadenceLabel}`;
    }
    if (app.elements.heroPolling) {
      app.elements.heroPolling.textContent = "";
    }
  };

  app.renderLeaderboard = function renderLeaderboard(managers) {
    const hasVisibleLiveSweats = managers.some((manager) => manager.hasActivePlayer);
    if (app.elements.leaderboardHelperLive) {
      app.elements.leaderboardHelperLive.hidden = !hasVisibleLiveSweats;
      app.elements.leaderboardHelperLive.style.display = hasVisibleLiveSweats ? "" : "none";
    }
    app.elements.leaderboardBody.innerHTML = managers
      .map((manager, index) => {
        const rosterId = `roster-${app.slugify(manager.name)}`;
        const pointsDelta = app.parseNumber(manager.pointsChange);
        const deltaMarkup =
          pointsDelta === 0
            ? ""
            : `<span class="points-delta ${pointsDelta > 0 ? "points-delta-up" : "points-delta-down"}">${
                pointsDelta > 0 ? "+" : ""
              }${Math.round(pointsDelta)}</span>`;

        return `
        <tr>
          <td><span class="rank-badge">${index + 1}</span></td>
          <td>
            <span class="manager-name-shell">
              ${
                manager.hasActivePlayer
                  ? '<span class="live-player-mark manager-live-mark" title="Manager has an active live sweat" aria-label="Manager has an active live sweat"></span>'
                  : ""
              }
              <span class="manager-name-text">${app.escapeHtml(manager.name)}</span>
            </span>
          </td>
          <td class="points-cell">
            <span class="points-cell-content">
              <span class="points-value-shell">
                <span class="points-total-slot">
                  <span class="points-total">${Math.round(manager.totalPoints)}</span>
                </span>
                ${
                  deltaMarkup
                    ? deltaMarkup.replace(
                        '<span class="points-delta ',
                        `<span title="Points gained ${app.escapeHtml(app.state.currentPointsChangeLabel)}" aria-label="Points gained ${app.escapeHtml(app.state.currentPointsChangeLabel)}" class="points-delta `
                      )
                    : ""
                }
              </span>
            </span>
          </td>
          <td>${
            manager.teamName
              ? `<a class="roster-jump-link" href="#${rosterId}" data-roster-id="${rosterId}">${app.escapeHtml(manager.teamName)}</a>`
              : "-"
          }</td>
          <td class="view-link-cell">
            <a
              class="view-link"
              href="${app.escapeHtml(manager.url || "#")}"
              target="_blank"
              rel="noreferrer"
              aria-label="View ${app.escapeHtml(manager.teamName || manager.name)} on Poker.org"
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
      `;
      })
      .join("");
  };

  app.renderLiveSweats = function renderLiveSweats(players) {
    if (!app.elements.liveSweatsSection || !app.elements.liveSweatsBody || !app.elements.liveSweatsStatus) {
      return;
    }

    const availability = app.getLiveSweatsAvailability();
    const liveContent = document.getElementById("live-sweats-content");
    const liveButton = app.elements.liveSweatsSection.querySelector(".collapse-button");

    if (!availability.isLive) {
      app.elements.liveSweatsStatus.hidden = false;
      if (app.elements.liveSweatsCountdown) {
        app.elements.liveSweatsCountdown.textContent = availability.countdownText;
      }
      if (app.elements.liveSweatsNav) {
        app.elements.liveSweatsNav.hidden = true;
      }
      if (app.elements.liveSweatsNavIndicator) {
        app.elements.liveSweatsNavIndicator.hidden = true;
      }
      if (liveContent) {
        liveContent.hidden = true;
      }
      if (liveButton) {
        liveButton.hidden = true;
      }
      app.elements.liveSweatsBody.innerHTML = "";
      return;
    }

    app.elements.liveSweatsStatus.hidden = true;
    if (app.elements.liveSweatsNav) {
      app.elements.liveSweatsNav.hidden = false;
    }
    if (app.elements.liveSweatsNavIndicator) {
      app.elements.liveSweatsNavIndicator.hidden = players.length === 0;
    }
    if (liveContent) {
      liveContent.hidden = false;
    }
    if (liveButton) {
      liveButton.hidden = false;
    }

    if (!players.length) {
      app.elements.liveSweatsBody.innerHTML = "";
      return;
    }

    app.elements.liveSweatsBody.innerHTML = players
      .map(
        (player) => `
        <tr>
          <td>${app.escapeHtml(player.player)}</td>
          <td>${
            player.eventUrl
              ? `<a class="live-event-link" href="${app.escapeHtml(player.eventUrl)}" target="_blank" rel="noreferrer">${app.escapeHtml(player.event)}</a>`
              : app.escapeHtml(player.event)
          }</td>
          <td>${app.escapeHtml(player.rank)}</td>
        </tr>
      `
      )
      .join("");
  };

  app.renderManagerCards = function renderManagerCards(managers) {
    const hasVisibleLiveSweats = managers.some((manager) => manager.hasActivePlayer);
    app.elements.managerCards.innerHTML = managers
      .map(
        (manager) => `
        <article class="manager-card" id="roster-${app.slugify(manager.name)}">
          <div class="card-header">
            <div>
              <h3>${app.escapeHtml(manager.name)}</h3>
            </div>
            <div class="card-total">${Math.round(manager.totalPoints)} pts</div>
          </div>
          <p class="player-meta">${app.escapeHtml(manager.teamName)}</p>
          <div class="player-list">
            ${manager.players
              .map(
                (player) => `
                  <div class="player-row">
                    <div class="player-name-wrap">
                      <button class="player-name player-history-trigger" type="button" data-player-name="${app.escapeHtml(player.player)}">
                        ${hasVisibleLiveSweats && player.isActive ? '<span class="live-player-mark" title="Currently live in sweat data" aria-label="Currently live in sweat data"></span>' : ""}${app.escapeHtml(player.player)}${player.isUnique ? '<span class="unique-player-mark" title="Unique to this roster" aria-label="Unique to this roster">*</span>' : ""}
                      </button>
                    </div>
                    <div class="player-points">${Math.round(player.points)}</div>
                    <div class="player-history-slot"></div>
                  </div>
                `
              )
              .join("")}
          </div>
        </article>
      `
      )
      .join("");
  };

  app.renderOwnership = function renderOwnership(ownershipRows) {
    app.elements.ownershipBody.innerHTML = ownershipRows
      .map((row) => {
        const bucketClass =
          row.ownerCount === 1
            ? "ownership-unique"
            : row.ownerCount === 2
              ? "ownership-shared"
              : "ownership-crowded";
        return `
        <tr>
          <td>${app.escapeHtml(row.player)}</td>
          <td class="points-cell">${Math.round(row.points)}</td>
          <td>${row.ownerCount}</td>
          <td><span class="ownership-pill ${bucketClass}">${app.formatPercent(row.ownershipPercent)}</span></td>
          <td class="teams-cell">${app.escapeHtml(row.owners.join(", "))}</td>
        </tr>
      `;
      })
      .join("");
  };

  app.renderOverlap = function renderOverlap(overlapRows) {
    app.elements.overlapGrid.innerHTML = overlapRows
      .map((row) => {
        return `
        <article class="overlap-card">
          <div class="card-header">
            <div>
              <h3>${app.escapeHtml(row.team)}</h3>
              <p class="player-meta">${app.escapeHtml(row.teamName)}</p>
            </div>
          </div>
          <div class="overlap-list">
            ${row.rivals
              .map(
                (rival) => `
                  <div class="overlap-row">
                    <div>
                      <div class="overlap-rival-name">${app.escapeHtml(rival.rivalName)}</div>
                      <div class="overlap-shared-players">${app.escapeHtml(
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
  };

  app.renderRouteLists = function renderRouteLists(bestLeverageTeams, mostBlockedTeams) {
    app.elements.bestLeverageList.innerHTML = bestLeverageTeams
      .map(
        (team) => `
        <li>${app.escapeHtml(team.name)} <span>${Math.round(team.uniquePoints)} unique pts</span></li>
      `
      )
      .join("");
    app.elements.mostBlockedList.innerHTML = mostBlockedTeams
      .map(
        (team) => `
        <li>${app.escapeHtml(team.name)} <span>${team.blockedOverlapCount} shared with teams ahead</span></li>
      `
      )
      .join("");
  };

  app.renderRoutes = function renderRoutes(routeRows) {
    app.elements.routesGrid.innerHTML = routeRows
      .map(
        (team) => `
        <article class="route-card">
          <div class="card-header">
            <div>
              <p class="section-kicker">Rank #${team.rank}</p>
              <h3>${app.escapeHtml(team.name)}</h3>
            </div>
            <div class="card-total">${Math.round(team.totalPoints)} pts</div>
          </div>
          <p class="route-summary">${app.escapeHtml(team.routeSummary)}</p>
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
  };

  app.setStatus = function setStatus(message, state) {
    return { message, state };
  };

  app.showRefreshToast = function showRefreshToast(message) {
    if (!app.elements.refreshToast) {
      return;
    }

    app.elements.refreshToast.textContent = message;
    app.elements.refreshToast.classList.add("is-visible");

    if (app.state.toastTimeoutId) {
      window.clearTimeout(app.state.toastTimeoutId);
    }

    app.state.toastTimeoutId = window.setTimeout(() => {
      app.elements.refreshToast.classList.remove("is-visible");
    }, 2600);
  };
})(window.FantasyLeaderboardApp, document, window);
