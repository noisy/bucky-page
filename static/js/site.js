// Small progressive touches; the page works fully without this file.

// Remember an explicit language choice so the root page sends the visitor back to it.
document.querySelectorAll("[data-lang-switch]").forEach(function (link) {
  link.addEventListener("click", function () {
    try { localStorage.setItem("bucky-lang", link.dataset.langSwitch); } catch (e) {}
  });
});

// Close the language menu on a click outside it or on Escape.
document.querySelectorAll("[data-lang-menu]").forEach(function (menu) {
  document.addEventListener("click", function (event) {
    if (!menu.contains(event.target)) menu.open = false;
  });
  menu.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && menu.open) {
      menu.open = false;
      menu.querySelector("summary").focus();
    }
  });
});

// A hairline under the sticky header once the page is scrolled.
var header = document.querySelector("[data-header]");
if (header) {
  var onScroll = function () { header.classList.toggle("scrolled", window.scrollY > 8); };
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();
}
