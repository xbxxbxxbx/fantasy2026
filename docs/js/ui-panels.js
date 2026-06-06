(function (app, window, document) {
  app.triggerPanelReveal = function triggerPanelReveal(content) {
    content.classList.remove("is-revealing");
    void content.offsetWidth;
    content.classList.add("is-revealing");

    if (app.state.revealAnimationTimeoutId) {
      window.clearTimeout(app.state.revealAnimationTimeoutId);
    }

    app.state.revealAnimationTimeoutId = window.setTimeout(() => {
      content.classList.remove("is-revealing");
    }, 700);
  };

  app.collapsePanelContent = function collapsePanelContent(content) {
    content.style.maxHeight = `${content.scrollHeight}px`;
    content.classList.add("is-collapsed");
    window.requestAnimationFrame(() => {
      content.style.maxHeight = "0px";
    });
  };

  app.expandPanelContent = function expandPanelContent(content) {
    content.classList.remove("is-collapsed");
    content.style.maxHeight = `${content.scrollHeight}px`;
    app.triggerPanelReveal(content);
    const clearHeight = () => {
      if (!content.classList.contains("is-collapsed")) {
        content.style.maxHeight = "none";
      }
      content.removeEventListener("transitionend", clearHeight);
    };
    content.addEventListener("transitionend", clearHeight);
  };

  app.getVisibleCollapsiblePanels = function getVisibleCollapsiblePanels() {
    return Array.from(document.querySelectorAll(".collapsible-panel"))
      .map((section) => ({
        content: section.querySelector(".panel-content"),
        button: section.querySelector(".collapse-button"),
      }))
      .filter(({ content, button }) => content && button && !content.hidden && !button.hidden);
  };

  app.setPanelCollapsed = function setPanelCollapsed(content, button, shouldCollapse) {
    const isCollapsed = content.classList.contains("is-collapsed");
    if (shouldCollapse && !isCollapsed) {
      app.collapsePanelContent(content);
    } else if (!shouldCollapse && isCollapsed) {
      app.expandPanelContent(content);
    }

    button.setAttribute("aria-expanded", String(!shouldCollapse));
    button.textContent = shouldCollapse ? "Expand" : "Collapse";
  };

  app.syncSectionNavToggle = function syncSectionNavToggle() {
    if (!app.elements.sectionNavToggle) {
      return;
    }

    const panels = app.getVisibleCollapsiblePanels();
    if (!panels.length) {
      app.elements.sectionNavToggle.hidden = true;
      return;
    }

    app.elements.sectionNavToggle.hidden = false;
    const allCollapsed = panels.every(({ content }) => content.classList.contains("is-collapsed"));
    app.elements.sectionNavToggle.textContent = allCollapsed ? "Expand" : "Collapse";
  };

  app.initializeCollapsiblePanels = function initializeCollapsiblePanels() {
    document.querySelectorAll(".panel-content").forEach((content) => {
      content.style.maxHeight = "none";
    });

    document.querySelectorAll(".collapse-button").forEach((button) => {
      button.addEventListener("click", () => {
        const targetId = button.getAttribute("data-target");
        const content = targetId ? document.getElementById(targetId) : null;
        if (!content) {
          return;
        }

        const isCollapsed = content.classList.contains("is-collapsed");
        app.setPanelCollapsed(content, button, !isCollapsed);
        app.syncSectionNavToggle();
      });
    });

    app.elements.sectionNavToggle?.addEventListener("click", () => {
      const panels = app.getVisibleCollapsiblePanels();
      if (!panels.length) {
        return;
      }

      const allCollapsed = panels.every(({ content }) => content.classList.contains("is-collapsed"));
      const shouldCollapse = !allCollapsed;
      panels.forEach(({ content, button }) => {
        app.setPanelCollapsed(content, button, shouldCollapse);
      });
      app.syncSectionNavToggle();
    });

    app.syncSectionNavToggle();
  };

  app.expandSectionFromNav = function expandSectionFromNav(hash) {
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

    app.setPanelCollapsed(content, button, false);
    app.syncSectionNavToggle();
    return section;
  };

  app.updateBackToTopVisibility = function updateBackToTopVisibility() {
    if (!app.elements.backToTop) {
      return;
    }

    const shouldShow = window.scrollY > 320;
    app.elements.backToTop.classList.toggle("is-visible", shouldShow);
  };
})(window.FantasyLeaderboardApp, window, document);
