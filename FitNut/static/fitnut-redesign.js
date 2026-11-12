"use strict";

document.addEventListener("DOMContentLoaded", () => {
  const reduceMotion = window.matchMedia(
    "(prefers-reduced-motion: reduce)"
  );


  /* Real almond cursor — follows mouse, never rotates */

  const finePointer = window.matchMedia(
    "(hover: hover) and (pointer: fine)"
  );

  if (finePointer.matches && !reduceMotion.matches) {
    const cursor = document.createElement("div");

    cursor.className = "almond-cursor";
    cursor.setAttribute("aria-hidden", "true");

    document.body.append(cursor);
    document.body.classList.add("almond-cursor-enabled");

    document.addEventListener(
      "pointermove",
      event => {
        if (event.pointerType !== "mouse") return;

        const target = event.target;

        const isTextInput =
          target instanceof Element &&
          Boolean(
            target.closest(
              "input, textarea, select, [contenteditable]"
            )
          );

        cursor.style.left = `${event.clientX}px`;
        cursor.style.top = `${event.clientY}px`;
        cursor.style.opacity = isTextInput ? "0" : "1";
      },
      { passive: true }
    );

    document.addEventListener("pointerout", event => {
      if (!event.relatedTarget) {
        cursor.style.opacity = "0";
      }
    });

    window.addEventListener("blur", () => {
      cursor.style.opacity = "0";
    });
  }




  /* Reveal animations */

  const revealItems = document.querySelectorAll(
    ".dashboard-card, .dashboard-section, .ai-day"
  );

  if (!reduceMotion.matches) {
    const revealObserver = new IntersectionObserver(
      (entries, observer) => {
        for (const entry of entries) {
          if (!entry.isIntersecting) continue;

          entry.target.classList.add(
            "fitnut-reveal"
          );

          observer.unobserve(entry.target);
        }
      },
      { threshold: 0.08 }
    );

    revealItems.forEach(item => {
      revealObserver.observe(item);
    });
  }

  /* Animated progress rings */

  document.querySelectorAll(
    "[data-fitnut-ring]"
  ).forEach(ring => {
    const percent = Math.max(
      0,
      Math.min(
        100,
        Number(ring.dataset.percent) || 0
      )
    );

    const circle = ring.querySelector(
      ".fitnut-ring-progress"
    );

    const number = ring.querySelector(
      ".fitnut-ring-number"
    );

    if (!circle || !number) return;

    const circumference = 2 * Math.PI * 42;

    circle.style.strokeDasharray =
      String(circumference);

    circle.style.strokeDashoffset =
      String(circumference);

    const animate = () => {
      circle.style.strokeDashoffset = String(
        circumference * (1 - percent / 100)
      );

      if (reduceMotion.matches) {
        number.textContent = `${percent}%`;
        return;
      }

      const start = performance.now();
      const duration = 1100;

      function frame(now) {
        const progress = Math.min(
          1,
          (now - start) / duration
        );

        const eased =
          1 - Math.pow(1 - progress, 3);

        number.textContent =
          `${Math.round(percent * eased)}%`;

        if (progress < 1) {
          requestAnimationFrame(frame);
        }
      }

      requestAnimationFrame(frame);
    };

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          animate();
          observer.disconnect();
        }
      },
      { threshold: 0.2 }
    );

    observer.observe(ring);
  });

  /* Existing dashboard trend bars */

  document.querySelectorAll(
    ".trend-chart"
  ).forEach(chart => {
    const observer = new IntersectionObserver(
      entries => {
        if (!entries[0].isIntersecting) return;

        chart.classList.add(
          "fitnut-chart-visible"
        );

        observer.disconnect();
      },
      { threshold: 0.1 }
    );

    observer.observe(chart);
  });

  /* Milestone celebration */

  window.FitNutCelebrate = function () {
    if (reduceMotion.matches) return;

    const colors = [
      "#d6ad60",
      "#e8d4b1",
      "#f5e5c4"
    ];

    for (let i = 0; i < 28; i++) {
      const particle =
        document.createElement("span");

      particle.style.position = "fixed";
      particle.style.left =
        `${20 + Math.random() * 60}vw`;

      particle.style.top = "-15px";
      particle.style.width = "6px";
      particle.style.height = "9px";

      particle.style.background =
        colors[i % colors.length];

      particle.style.pointerEvents = "none";
      particle.style.zIndex = "99998";

      document.body.append(particle);

      const horizontal =
        (Math.random() - .5) * 220;

      particle.animate(
        [
          {
            transform: "translate(0, 0) rotate(0deg)",
            opacity: 1
          },
          {
            transform:
              `translate(${horizontal}px, 80vh) rotate(540deg)`,
            opacity: 0
          }
        ],
        {
          duration: 1400 + Math.random() * 900,
          easing: "ease-out"
        }
      ).finished.finally(() => particle.remove());
    }
  };

  /* Celebrate newly reached dashboard goals */

  document.querySelectorAll(
    "[data-fitnut-milestone]"
  ).forEach(element => {
    const key = element.dataset.fitnutMilestone;
    const reached =
      element.dataset.reached === "true";

    if (!key || !reached) return;

    const storageKey = `fitnut-milestone-${key}`;

    try {
      if (sessionStorage.getItem(storageKey)) return;

      sessionStorage.setItem(storageKey, "1");
      window.FitNutCelebrate();
    } catch {
      /* Storage may be unavailable. */
    }
  });
});