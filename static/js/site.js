// Small progressive touches; the page works fully without this file.

// Remember an explicit language choice so the root page sends the visitor back to it.
document.querySelectorAll("[data-lang-switch]").forEach(function (link) {
  link.addEventListener("click", function () {
    try { localStorage.setItem("bucky-lang", link.dataset.langSwitch); } catch (e) {}
  });
});

// Menus (language and the phone menu) close on an outside click, on Escape
// and, for the phone menu, after a link was followed.
document.querySelectorAll("[data-lang-menu], [data-menu]").forEach(function (menu) {
  document.addEventListener("click", function (event) {
    if (!menu.contains(event.target)) menu.open = false;
  });
  menu.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && menu.open) {
      menu.open = false;
      menu.querySelector("summary").focus();
    }
  });
  menu.querySelectorAll("a").forEach(function (link) {
    link.addEventListener("click", function () { menu.open = false; });
  });
});

// A hairline under the sticky header once the page is scrolled.
var header = document.querySelector("[data-header]");
if (header) {
  var onScroll = function () { header.classList.toggle("scrolled", window.scrollY > 8); };
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();
}

// The phone download dock stays out of the way while the hero's own download
// button is on screen.
var dock = document.querySelector("[data-dock]");
var heroActions = document.querySelector("[data-hero-actions]");
if (dock && heroActions) {
  var updateDock = function () {
    var box = heroActions.getBoundingClientRect();
    dock.classList.toggle("is-hidden", box.bottom > 0 && box.top < window.innerHeight);
  };
  window.addEventListener("scroll", updateDock, { passive: true });
  window.addEventListener("resize", updateDock);
  updateDock();
}
