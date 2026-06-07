(function (app, document, window) {
  app.closeAllPlayerHistoryWidgets = function closeAllPlayerHistoryWidgets() {
    document.querySelectorAll(".player-history-widget").forEach((widget) => widget.remove());
    document
      .querySelectorAll(".player-history-trigger.is-open")
      .forEach((trigger) => trigger.classList.remove("is-open"));
  };

  app.buildPlayerHistoryWidget = function buildPlayerHistoryWidget(playerName, historyByYear) {
    const years = Object.keys(historyByYear || {}).sort(
      (left, right) => Number(right) - Number(left)
    );
    const rows =
      years.length === 0
        ? '<div class="player-history-empty">No historical 25K data found.</div>'
        : years
            .map(
              (year) => `
              <div class="player-history-year-row">
                <span>${year}</span>
                <strong>${Math.round(app.parseNumber(historyByYear[year]))}</strong>
              </div>
            `
            )
            .join("");

    return `
    <div class="player-history-widget" role="dialog" aria-label="Historical points for ${app.escapeHtml(playerName)}">
      <div class="player-history-header">
        <span class="player-history-title">Historical points</span>
        <button class="player-history-close" type="button" aria-label="Close historical points">×</button>
      </div>
      <div class="player-history-body">
        ${rows}
      </div>
    </div>
  `;
  };

  app.initializePlayerHistoryWidgets = function initializePlayerHistoryWidgets() {
    if (app.state.playerHistoryWidgetsInitialized || !app.elements.managerCards) {
      return;
    }

    app.elements.managerCards.addEventListener("click", async (event) => {
      const target = event.target;
      if (!(target instanceof Element)) {
        return;
      }

      const closeButton = target.closest(".player-history-close");
      if (closeButton && app.elements.managerCards.contains(closeButton)) {
        event.stopPropagation();
        const playerRow = closeButton.closest(".player-row");
        playerRow?.querySelector(".player-history-widget")?.remove();
        playerRow?.querySelector(".player-history-trigger")?.classList.remove("is-open");
        return;
      }

      const trigger = target.closest(".player-history-trigger");
      if (!trigger || !app.elements.managerCards.contains(trigger)) {
        return;
      }

      event.stopPropagation();
      const playerName = trigger.getAttribute("data-player-name");
      const playerWrap = trigger.closest(".player-name-wrap");
      const playerRow = trigger.closest(".player-row");
      const playerHistorySlot = playerRow?.querySelector(".player-history-slot");
      if (!playerName || !playerWrap || !playerRow || !playerHistorySlot) {
        return;
      }

      const existingWidget = playerHistorySlot.querySelector(".player-history-widget");
      if (existingWidget) {
        existingWidget.remove();
        trigger.classList.remove("is-open");
        return;
      }

      app.closeAllPlayerHistoryWidgets();

      try {
        const history = await app.fetchPlayerHistory();
        const historyByYear = history[playerName] || {};
        playerHistorySlot.innerHTML = app.buildPlayerHistoryWidget(playerName, historyByYear);
      } catch (error) {
        playerHistorySlot.innerHTML = app.buildPlayerHistoryWidget(playerName, {});
      }
      trigger.classList.add("is-open");
    });

    if (!app.state.playerHistoryDismissInitialized) {
      document.addEventListener("click", (event) => {
        const target = event.target;
        if (!(target instanceof Element)) {
          app.closeAllPlayerHistoryWidgets();
          return;
        }

        if (!target.closest(".player-name-wrap")) {
          app.closeAllPlayerHistoryWidgets();
        }
      });
      app.state.playerHistoryDismissInitialized = true;
    }
    app.state.playerHistoryWidgetsInitialized = true;
  };

  app.initializeRosterJumpLinks = function initializeRosterJumpLinks() {
    if (app.state.rosterJumpLinksInitialized || !app.elements.leaderboardBody) {
      return;
    }

    app.elements.leaderboardBody.addEventListener("click", (event) => {
      const target = event.target;
      if (!(target instanceof Element)) {
        return;
      }

      const link = target.closest(".roster-jump-link");
      if (!link || !app.elements.leaderboardBody.contains(link)) {
        return;
      }

      const rosterId = link.getAttribute("data-roster-id");
      if (!rosterId) {
        return;
      }

      const rostersSection = document.getElementById("rosters");
      const rostersContent = rostersSection?.querySelector(".panel-content");
      const rostersButton = rostersSection?.querySelector(".collapse-button");
      const targetCard = document.getElementById(rosterId);
      if (!rostersSection || !rostersContent || !rostersButton || !targetCard) {
        return;
      }

      event.preventDefault();

      if (rostersContent.classList.contains("is-collapsed")) {
        app.setPanelCollapsed(rostersContent, rostersButton, false);
        app.syncSectionNavToggle();
      }

      window.requestAnimationFrame(() => {
        targetCard.scrollIntoView({ behavior: app.getScrollBehavior(), block: "start" });
        window.history.replaceState(null, "", `#${rosterId}`);
      });
    });
    app.state.rosterJumpLinksInitialized = true;
  };

  app.closePointContributorModal = function closePointContributorModal() {
    if (app.elements.pointContributorModal) {
      app.elements.pointContributorModal.hidden = true;
    }
  };

  app.getPointContributors = function getPointContributors(manager, comparisonSnapshot) {
    const baselineManager = (comparisonSnapshot?.managers || []).find(
      (entry) => app.normalizeName(entry.managerName) === app.normalizeName(manager.name)
    );
    if (!baselineManager) {
      throw new Error("Comparison data for this team was not found.");
    }

    const baselinePointsByPlayer = new Map(
      (baselineManager.players || []).map((player) => [
        app.canonicalPlayerName(player.player),
        app.parseNumber(player.points),
      ])
    );

    return (manager.players || [])
      .map((player) => {
        const playerName = app.canonicalPlayerName(player.player);
        const previousPoints = baselinePointsByPlayer.get(playerName) || 0;
        const totalPoints = app.parseNumber(player.points);
        return {
          player: playerName,
          pointsGained: totalPoints - previousPoints,
          totalPoints,
        };
      })
      .filter((player) => player.pointsGained > 0)
      .sort(
        (left, right) =>
          right.pointsGained - left.pointsGained ||
          right.totalPoints - left.totalPoints ||
          left.player.localeCompare(right.player)
      );
  };

  app.renderPointContributorBody = function renderPointContributorBody(manager, contributors) {
    if (!contributors.length) {
      return `
        <p class="commit-modal-message">No individual player gains were found for ${app.escapeHtml(manager.name)}.</p>
      `;
    }

    const rows = contributors
      .map(
        (contributor) => `
          <div class="point-contributor-row">
            <span>${app.escapeHtml(contributor.player)}</span>
            <strong>+${Math.round(contributor.pointsGained)}</strong>
          </div>
        `
      )
      .join("");
    const totalGained = contributors.reduce(
      (sum, contributor) => sum + app.parseNumber(contributor.pointsGained),
      0
    );

    return `
      <div class="point-contributor-list">${rows}</div>
      <div class="point-contributor-total">
        <span>Total</span>
        <strong>+${Math.round(totalGained)}</strong>
      </div>
    `;
  };

  app.initializePointContributorModal = function initializePointContributorModal() {
    if (
      app.state.pointContributorModalInitialized ||
      !app.elements.leaderboardBody ||
      !app.elements.pointContributorModal ||
      !app.elements.pointContributorBody
    ) {
      return;
    }

    app.elements.leaderboardBody.addEventListener("click", async (event) => {
      const target = event.target;
      if (!(target instanceof Element)) {
        return;
      }

      const trigger = target.closest(".points-delta-button");
      if (!trigger || !app.elements.leaderboardBody.contains(trigger)) {
        return;
      }

      event.preventDefault();
      event.stopPropagation();

      const managerName = trigger.getAttribute("data-manager-name");
      const manager = app.state.latestManagers.find((entry) => entry.name === managerName);
      if (!manager) {
        return;
      }

      app.elements.pointContributorModal.hidden = false;
      if (app.elements.pointContributorTitle) {
        app.elements.pointContributorTitle.textContent = `${manager.name} +${Math.round(
          app.parseNumber(manager.pointsChange)
        )}`;
      }
      app.elements.pointContributorBody.innerHTML =
        '<p class="commit-modal-loading">Loading point contributors…</p>';

      try {
        const comparisonSnapshot = await app.fetchComparisonSnapshot(
          app.state.latestPointsChangeComparisonDate
        );
        const contributors = app.getPointContributors(manager, comparisonSnapshot);
        app.elements.pointContributorBody.innerHTML = app.renderPointContributorBody(
          manager,
          contributors
        );
      } catch (error) {
        app.elements.pointContributorBody.innerHTML = `
          <p class="commit-modal-message">Could not load point contributors for ${app.escapeHtml(manager.name)}.</p>
        `;
      }
    });

    app.elements.pointContributorClose?.addEventListener("click", app.closePointContributorModal);
    app.elements.pointContributorBackdrop?.addEventListener("click", app.closePointContributorModal);
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        app.closePointContributorModal();
      }
    });

    app.state.pointContributorModalInitialized = true;
  };

  app.closeCommitEasterEggModal = function closeCommitEasterEggModal() {
    if (app.elements.commitEasterEggModal) {
      app.elements.commitEasterEggModal.hidden = true;
    }
  };

  app.renderCommitEasterEggBody = function renderCommitEasterEggBody(payload) {
    const changes = payload?.changes || [];
    if (!changes.length) {
      return `
        <p class="commit-modal-message">Could not load the latest changes right now.</p>
      `;
    }

    return changes
      .map((change) => {
        const shortSha = app.escapeHtml(String(change.commit || "").slice(0, 7));
        const url = app.escapeHtml(change.url || "https://github.com/xbxxbxxbx/fantasy2026/commits/master");
        const timestamp = app.escapeHtml(app.formatUpdatedAt(change.publishedAt));
        const bullets = (change.summary || [])
          .slice(0, 3)
          .map((item) => `<li>${app.escapeHtml(item)}</li>`)
          .join("");

        return `
          <article class="commit-change">
            <p class="commit-modal-meta">
              <a class="commit-modal-link" href="${url}" target="_blank" rel="noreferrer">${shortSha}</a>${timestamp ? ` · ${timestamp}` : ""}
            </p>
            <ul class="commit-change-list">
              ${bullets}
            </ul>
          </article>
        `;
      })
      .join("");
  };

  app.initializeCommitEasterEgg = function initializeCommitEasterEgg() {
    if (app.state.commitEasterEggInitialized || !app.elements.commitEasterEggTrigger) {
      return;
    }

    const openModal = async () => {
      if (!app.elements.commitEasterEggModal || !app.elements.commitEasterEggBody) {
        return;
      }

      app.elements.commitEasterEggModal.hidden = false;
      app.elements.commitEasterEggBody.innerHTML =
        '<p class="commit-modal-loading">Loading latest changes…</p>';

      try {
        const payload = await app.fetchLatestChanges();
        const title = app.escapeHtml(payload?.title || "Latest changes");
        const titleElement = document.getElementById("commit-modal-title");
        if (titleElement) {
          titleElement.textContent = title;
        }
        app.elements.commitEasterEggBody.innerHTML = app.renderCommitEasterEggBody(payload);
      } catch (error) {
        app.elements.commitEasterEggBody.innerHTML = app.renderCommitEasterEggBody(null);
      }
    };

    app.elements.commitEasterEggTrigger.addEventListener("click", openModal);
    app.elements.commitEasterEggClose?.addEventListener("click", app.closeCommitEasterEggModal);
    app.elements.commitEasterEggBackdrop?.addEventListener("click", app.closeCommitEasterEggModal);
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        app.closeCommitEasterEggModal();
      }
    });

    app.state.commitEasterEggInitialized = true;
  };

  app.syncLiveSweatsAvailability = function syncLiveSweatsAvailability(force = false) {
    const availability = app.getLiveSweatsAvailability();
    if (app.elements.liveSweatsCountdown && !availability.isLive) {
      app.elements.liveSweatsCountdown.textContent = availability.countdownText;
    }
    if (app.elements.liveSweatsHelperLive && !availability.isLive) {
      app.elements.liveSweatsHelperLive.hidden = true;
    }

    if (force || app.state.lastLiveSweatsAvailability !== availability.isLive) {
      app.state.lastLiveSweatsAvailability = availability.isLive;
      if (app.state.latestManagers.length) {
        app.renderLeaderboard(app.state.latestManagers);
        app.renderManagerCards(app.state.latestManagers);
      }
      app.renderLiveSweats(app.state.latestLiveSweats);
    }
  };

  app.startLiveSweatsCountdown = function startLiveSweatsCountdown() {
    if (app.state.liveSweatsCountdownTimerId) {
      window.clearInterval(app.state.liveSweatsCountdownTimerId);
    }

    app.syncLiveSweatsAvailability(true);
    app.state.liveSweatsCountdownTimerId = window.setInterval(() => {
      app.syncLiveSweatsAvailability();
    }, 60000);
  };

  app.initializeNavigation = function initializeNavigation() {
    document.querySelectorAll(".section-nav-link").forEach((link) => {
      link.addEventListener("click", (event) => {
        const hash = link.getAttribute("href");
        if (!hash) {
          return;
        }

        event.preventDefault();
        const section = app.expandSectionFromNav(hash);
        if (!section) {
          return;
        }

        section.scrollIntoView({ behavior: app.getScrollBehavior(), block: "start" });
        window.history.replaceState(null, "", hash);
      });
    });

    window.addEventListener("scroll", app.updateBackToTopVisibility, { passive: true });
    app.updateBackToTopVisibility();
  };
})(window.FantasyLeaderboardApp, document, window);
