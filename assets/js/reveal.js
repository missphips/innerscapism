/* Sections and cards fade up gently as they scroll into view.
   Only elements below the first screen are animated, nothing stays hidden
   if this script doesn't run, and it is skipped for reduced-motion users. */
(function () {
  if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  var targets = document.querySelectorAll('main > section, main > div, .half, .door, .quote, .collage');
  var pending = [];
  var fold = window.innerHeight;
  [].forEach.call(targets, function (el) {
    if (el.getBoundingClientRect().top < fold) return;
    el.classList.add('reveal');
    pending.push(el);
  });
  function show(el) { el.classList.add('is-visible'); }
  function check() {
    var limit = window.innerHeight * 0.92;
    pending = pending.filter(function (el) {
      if (el.getBoundingClientRect().top < limit) { show(el); return false; }
      return true;
    });
    if (!pending.length) { window.removeEventListener('scroll', onScroll); window.removeEventListener('resize', onScroll); }
  }
  var ticking = false;
  function onScroll() {
    if (ticking) return;
    ticking = true;
    setTimeout(function () { ticking = false; check(); }, 60);
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', onScroll);
  check();
})();
