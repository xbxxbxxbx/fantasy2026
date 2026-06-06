(function (window) {
  window.LEADERBOARD_CONFIG = {};
  window.LEADERBOARD_CONFIG_READY = fetch("./config.json", { cache: "no-store" })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`Config request failed with ${response.status}`);
      }
      return response.json();
    })
    .then((config) => {
      window.LEADERBOARD_CONFIG = config;
      return config;
    })
    .catch((error) => {
      console.error(error);
      return window.LEADERBOARD_CONFIG;
    });
})(window);
