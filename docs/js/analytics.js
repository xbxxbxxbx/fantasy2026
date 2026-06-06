(function (app) {
  app.buildAnalytics = function buildAnalytics(managers) {
    const teamCount = managers.length;
    const playerMap = new Map();

    for (const manager of managers) {
      for (const player of manager.players) {
        const key = app.canonicalPlayerName(player.player);
        const existing = playerMap.get(key) || {
          player: key,
          points: 0,
          owners: [],
        };
        existing.points = Math.max(existing.points, app.parseNumber(player.points));
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
      ownershipRows.map((row) => [app.canonicalPlayerName(row.player), row.ownerCount])
    );
    const playerPointsByName = new Map(
      ownershipRows.map((row) => [app.canonicalPlayerName(row.player), row.points])
    );
    const leader = managers[0] || null;
    const leaderPlayers = new Set(
      (leader?.players || []).map((player) => app.canonicalPlayerName(player.player))
    );

    const overlapRows = managers.map((manager) => {
      const playerSet = new Set(
        manager.players.map((player) => app.canonicalPlayerName(player.player))
      );
      const rivals = managers
        .filter((rival) => rival.name !== manager.name)
        .map((rival) => {
          const sharedPlayers = rival.players
            .map((player) => app.canonicalPlayerName(player.player))
            .filter((playerName) => playerSet.has(playerName))
            .sort((left, right) => {
              const leftPoints = playerPointsByName.get(app.canonicalPlayerName(left)) || 0;
              const rightPoints = playerPointsByName.get(app.canonicalPlayerName(right)) || 0;
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
        totalPoints: manager.totalPoints,
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
        const playerName = app.canonicalPlayerName(player.player);
        const ownerCount = playerOwnerCount.get(playerName) || 1;
        const points = app.parseNumber(player.points);

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

      const managerPlayerSet = new Set(
        manager.players.map((player) => app.canonicalPlayerName(player.player))
      );
      const leadersSharedPlayers = Array.from(managerPlayerSet).filter((player) =>
        leaderPlayers.has(player)
      );
      const leadersSharedWithTeam = leadersSharedPlayers.length;
      const leadersSharedAgainstTeam = (leader?.players || [])
        .filter((player) => managerPlayerSet.has(app.canonicalPlayerName(player.player)))
        .reduce((sum, player) => sum + app.parseNumber(player.points), 0);
      const higherTeams = managers.slice(0, index);
      const playersAheadSet = new Set(
        higherTeams.flatMap((higherTeam) =>
          higherTeam.players.map((player) => app.canonicalPlayerName(player.player))
        )
      );
      const blockedOverlapCount = Array.from(managerPlayerSet).filter((player) =>
        playersAheadSet.has(player)
      ).length;
      const sharedPoints = semiSharedPoints + crowdedPoints;
      const uniqueShare = manager.totalPoints > 0 ? uniquePoints / manager.totalPoints : 0;
      const chaseGap = leader ? leader.totalPoints - manager.totalPoints : 0;

      let routeSummary =
        "Needs both shared stars to hold and one or two unique draftees to separate.";
      if (index === 0) {
        routeSummary =
          uniquePoints > sharedPoints
            ? "Controls its own path; gains from continued scoring by unique core."
            : "Still leading, but shared draftees let trailing teams keep pace.";
      } else if (
        leadersSharedWithTeam >= 3 ||
        leadersSharedAgainstTeam > manager.totalPoints * 0.5
      ) {
        routeSummary =
          "Needs non-shared production because leader gains from many of the same scores.";
      } else if (uniqueShare >= 0.35 || uniquePlayers.length >= 3) {
        routeSummary =
          "Can gain ground if its unique players score, since those points do not also help the leaders.";
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
  };

  app.buildViewModel = function buildViewModel(snapshot, activeSnapshot) {
    const managers = (snapshot.managers || []).map((manager) => ({
      name: manager.managerName,
      teamName: manager.teamName,
      url: manager.url,
      totalPoints: app.parseNumber(manager.totalPoints),
      pointsChange: app.parseNumber(manager.pointsChange),
      players: (manager.players || []).map((player) => ({
        player: app.canonicalPlayerName(player.player),
        points: app.parseNumber(player.points),
        isActive: false,
        isUnique: false,
      })),
    }));

    const analytics = app.buildAnalytics(managers);
    const uniquePlayerSet = new Set(
      analytics.ownershipRows
        .filter((row) => row.ownerCount === 1)
        .map((row) => app.canonicalPlayerName(row.player))
    );
    const rosterPlayerSet = new Set(
      managers.flatMap((manager) =>
        manager.players.map((player) => app.canonicalPlayerName(player.player))
      )
    );
    const liveSweats = (activeSnapshot.players || [])
      .filter((player) => rosterPlayerSet.has(app.canonicalPlayerName(player.player)))
      .sort((left, right) => left.player.localeCompare(right.player));
    const activePlayerSet = new Set(
      liveSweats.map((player) => app.canonicalPlayerName(player.player))
    );

    managers.forEach((manager) => {
      manager.hasActivePlayer = false;
      manager.players.forEach((player) => {
        player.isUnique = uniquePlayerSet.has(app.canonicalPlayerName(player.player));
        player.isActive = activePlayerSet.has(app.canonicalPlayerName(player.player));
        if (player.isActive) {
          manager.hasActivePlayer = true;
        }
      });
    });

    return {
      analytics,
      generatedAt: snapshot.generatedAt || null,
      liveSweats,
      managers,
      metadata: {
        leagueName: snapshot.leagueName || null,
        sourceLabel: snapshot.sourceLabel || null,
        sourceUrl: snapshot.sourceUrl || null,
        updateCadenceLabel: snapshot.updateCadenceLabel || null,
      },
      pointsChangeLabel: snapshot.pointsChangeLabel || "today",
      signature: app.snapshotSignature(snapshot),
    };
  };
})(window.FantasyLeaderboardApp);
