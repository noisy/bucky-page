// Small progressive touches; the page works fully without this file.

// Remember an explicit language choice so the root page sends the visitor back to it.
document.querySelectorAll("[data-lang-switch]").forEach(function (link) {
  link.addEventListener("click", function () {
    try { localStorage.setItem("bucky-lang", link.dataset.langSwitch); } catch (e) {}
  });
});

// A hairline under the sticky header once the page is scrolled.
var header = document.querySelector("[data-header]");
if (header) {
  var onScroll = function () { header.classList.toggle("scrolled", window.scrollY > 8); };
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();
}
