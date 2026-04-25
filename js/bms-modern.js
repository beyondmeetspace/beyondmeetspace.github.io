/* Beyond Meet Space — modern site behaviors.
   Sticky-nav scroll state, mobile menu toggle, scroll-in fades. */
(function () {
    'use strict';

    // ---- Nav: add scroll-state shadow ----
    var nav = document.querySelector('.bms-nav');
    if (nav) {
        var onScroll = function () {
            if (window.scrollY > 4) nav.classList.add('is-scrolled');
            else nav.classList.remove('is-scrolled');
        };
        window.addEventListener('scroll', onScroll, { passive: true });
        onScroll();
    }

    // ---- Mobile nav toggle ----
    var toggle = document.querySelector('.bms-nav__toggle');
    var links = document.querySelector('.bms-nav__links');
    if (toggle && links) {
        toggle.addEventListener('click', function () {
            var open = links.classList.toggle('is-open');
            toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
        });
        // Close on link tap
        links.querySelectorAll('a').forEach(function (a) {
            a.addEventListener('click', function () {
                links.classList.remove('is-open');
                toggle.setAttribute('aria-expanded', 'false');
            });
        });
    }

    // ---- Fade-in on scroll (IntersectionObserver) ----
    if ('IntersectionObserver' in window) {
        var io = new IntersectionObserver(function (entries) {
            entries.forEach(function (e) {
                if (e.isIntersecting) {
                    e.target.classList.add('is-visible');
                    io.unobserve(e.target);
                }
            });
        }, { rootMargin: '0px 0px -10% 0px', threshold: 0.05 });
        document.querySelectorAll('.bms-fade-in').forEach(function (el) { io.observe(el); });
    } else {
        // Fallback: show everything
        document.querySelectorAll('.bms-fade-in').forEach(function (el) { el.classList.add('is-visible'); });
    }
})();
