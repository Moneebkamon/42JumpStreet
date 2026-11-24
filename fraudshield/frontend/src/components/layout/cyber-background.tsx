"use client";

import { useEffect, useRef } from "react";

/**
 * Animated backdrop that mirrors what Manee does:
 *  - a drifting network of nodes (links, domains, devices) with data packets travelling between them,
 *  - now and then a node turns red (a threat appears),
 *  - a scan wave sweeps out from the centre and, when it reaches a threat, neutralises it with a shield pulse.
 * Rendered on one fixed canvas behind the page. It pauses when the tab is hidden and draws a still frame
 * for people who prefer reduced motion.
 */

type Node = {
  x: number;
  y: number;
  vx: number;
  vy: number;
  r: number;
  threat: number; // 0 = clean, >0 = threat strength (fades in)
  shield: number; // >0 while the "neutralised" pulse is playing (1 → 0)
};

type Packet = { a: number; b: number; t: number; speed: number };

const LINK_DIST = 150;
const WAVE_PERIOD = 7000; // ms between scan waves
const THREAT_EVERY = 1800; // ms between new threats

function readColor(name: string, fallback: string): string {
  if (typeof window === "undefined") return fallback;
  const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return v || fallback;
}

function hexToRgb(hex: string): [number, number, number] {
  const m = hex.replace("#", "").match(/^([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})$/i);
  if (!m) return [34, 211, 238];
  return [parseInt(m[1], 16), parseInt(m[2], 16), parseInt(m[3], 16)];
}

export function CyberBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext("2d");
    if (!canvas || !ctx) return;

    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const [br, bg, bb] = hexToRgb(readColor("--brand", "#22d3ee"));
    const [ir, ig, ib] = hexToRgb(readColor("--brand-2", "#818cf8"));
    const [tr, tg, tb] = hexToRgb(readColor("--threat", "#fb7185"));
    const brand = (a: number) => `rgba(${br},${bg},${bb},${a})`;
    const indigo = (a: number) => `rgba(${ir},${ig},${ib},${a})`;
    const threat = (a: number) => `rgba(${tr},${tg},${tb},${a})`;

    let w = 0;
    let h = 0;
    let dpr = 1;
    const nodes: Node[] = [];
    let packets: Packet[] = [];
    let raf = 0;
    let last = performance.now();
    let waveStart = last - WAVE_PERIOD * 0.6;
    let lastThreat = last;
    const mouse = { x: -9999, y: -9999 };

    function resize() {
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      w = window.innerWidth;
      h = window.innerHeight;
      canvas!.width = Math.floor(w * dpr);
      canvas!.height = Math.floor(h * dpr);
      canvas!.style.width = `${w}px`;
      canvas!.style.height = `${h}px`;
      ctx!.setTransform(dpr, 0, 0, dpr, 0, 0);

      const target = Math.min(90, Math.max(28, Math.round((w * h) / 17000)));
      while (nodes.length < target) nodes.push(makeNode());
      nodes.length = target;
      for (const n of nodes) {
        n.x = Math.min(n.x, w);
        n.y = Math.min(n.y, h);
      }
      packets = packets.filter((p) => p.a < target && p.b < target);
    }

    function makeNode(): Node {
      const speed = 0.08 + Math.random() * 0.14;
      const angle = Math.random() * Math.PI * 2;
      return {
        x: Math.random() * (w || window.innerWidth),
        y: Math.random() * (h || window.innerHeight),
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed,
        r: 1 + Math.random() * 1.6,
        threat: 0,
        shield: 0,
      };
    }

    function spawnPacket() {
      const a = Math.floor(Math.random() * nodes.length);
      let best = -1;
      let bestD = Infinity;
      for (let i = 0; i < nodes.length; i++) {
        if (i === a) continue;
        const d = Math.hypot(nodes[i].x - nodes[a].x, nodes[i].y - nodes[a].y);
        if (d < LINK_DIST && d < bestD && Math.random() > 0.3) {
          best = i;
          bestD = d;
        }
      }
      if (best >= 0) packets.push({ a, b: best, t: 0, speed: 0.004 + Math.random() * 0.006 });
    }

    function frame(now: number) {
      const dt = Math.min(now - last, 50);
      last = now;
      const step = dt / 16.67;

      ctx!.clearRect(0, 0, w, h);

      // Scan wave: an expanding ring from the upper centre, where the scanner sits.
      const cx = w / 2;
      const cy = Math.min(h * 0.32, 300);
      const maxR = Math.hypot(Math.max(cx, w - cx), Math.max(cy, h - cy));
      if (now - waveStart > WAVE_PERIOD) waveStart = now;
      const waveP = (now - waveStart) / WAVE_PERIOD;
      const waveR = waveP * maxR * 1.05;

      if (!reduced) {
        const ringAlpha = 0.16 * (1 - waveP);
        const grad = ctx!.createRadialGradient(cx, cy, Math.max(0, waveR - 60), cx, cy, waveR);
        grad.addColorStop(0, brand(0));
        grad.addColorStop(1, brand(ringAlpha * 0.5));
        ctx!.fillStyle = grad;
        ctx!.beginPath();
        ctx!.arc(cx, cy, waveR, 0, Math.PI * 2);
        ctx!.fill();
        ctx!.strokeStyle = brand(ringAlpha);
        ctx!.lineWidth = 1;
        ctx!.stroke();
      }

      // New threats appear on clean nodes.
      if (!reduced && now - lastThreat > THREAT_EVERY) {
        lastThreat = now;
        const clean = nodes.filter((n) => n.threat === 0 && n.shield === 0);
        if (clean.length) clean[Math.floor(Math.random() * clean.length)].threat = 0.01;
      }

      // Move nodes.
      for (const n of nodes) {
        if (!reduced) {
          n.x += n.vx * step;
          n.y += n.vy * step;
          if (n.x < -20) n.x = w + 20;
          if (n.x > w + 20) n.x = -20;
          if (n.y < -20) n.y = h + 20;
          if (n.y > h + 20) n.y = -20;
        }
        if (n.threat > 0) {
          n.threat = Math.min(1, n.threat + 0.02 * step);
          const d = Math.hypot(n.x - cx, n.y - cy);
          // The wave front reached this threat: neutralise it.
          if (!reduced && Math.abs(d - waveR) < 14 && n.threat > 0.5) {
            n.threat = 0;
            n.shield = 1;
          }
        }
        if (n.shield > 0) n.shield = Math.max(0, n.shield - 0.012 * step);
      }

      // Links.
      ctx!.lineWidth = 0.6;
      for (let i = 0; i < nodes.length; i++) {
        const a = nodes[i];
        for (let j = i + 1; j < nodes.length; j++) {
          const b = nodes[j];
          const dx = a.x - b.x;
          const dy = a.y - b.y;
          const d2 = dx * dx + dy * dy;
          if (d2 > LINK_DIST * LINK_DIST) continue;
          const k = 1 - Math.sqrt(d2) / LINK_DIST;
          const hot = Math.max(a.threat, b.threat);
          ctx!.strokeStyle = hot > 0.3 ? threat(0.18 * k * hot) : (i + j) % 3 === 0 ? indigo(0.16 * k) : brand(0.14 * k);
          ctx!.beginPath();
          ctx!.moveTo(a.x, a.y);
          ctx!.lineTo(b.x, b.y);
          ctx!.stroke();
        }
      }

      // Packets of data travelling along links.
      if (!reduced) {
        if (packets.length < nodes.length / 3 && Math.random() < 0.15 * step) spawnPacket();
        packets = packets.filter((p) => {
          p.t += p.speed * step;
          const a = nodes[p.a];
          const b = nodes[p.b];
          if (!a || !b || p.t >= 1) return false;
          if (Math.hypot(a.x - b.x, a.y - b.y) > LINK_DIST * 1.2) return false;
          const x = a.x + (b.x - a.x) * p.t;
          const y = a.y + (b.y - a.y) * p.t;
          const g = ctx!.createRadialGradient(x, y, 0, x, y, 6);
          g.addColorStop(0, brand(0.9));
          g.addColorStop(1, brand(0));
          ctx!.fillStyle = g;
          ctx!.beginPath();
          ctx!.arc(x, y, 6, 0, Math.PI * 2);
          ctx!.fill();
          return true;
        });
      }

      // Nodes.
      for (const n of nodes) {
        const near = Math.max(0, 1 - Math.hypot(n.x - mouse.x, n.y - mouse.y) / 180);
        if (n.threat > 0) {
          const pulse = 0.5 + 0.5 * Math.sin(now / 220);
          ctx!.fillStyle = threat(0.12 * n.threat * (0.6 + pulse * 0.4));
          ctx!.beginPath();
          ctx!.arc(n.x, n.y, 10 + pulse * 4, 0, Math.PI * 2);
          ctx!.fill();
          ctx!.fillStyle = threat(0.85 * n.threat);
          ctx!.beginPath();
          ctx!.arc(n.x, n.y, n.r + 1.2, 0, Math.PI * 2);
          ctx!.fill();
        } else {
          ctx!.fillStyle = brand(0.45 + near * 0.5);
          ctx!.beginPath();
          ctx!.arc(n.x, n.y, n.r + near * 1.2, 0, Math.PI * 2);
          ctx!.fill();
        }
        if (n.shield > 0) {
          // Shield pulse: expanding ring plus a small hexagon "lock".
          const s = 1 - n.shield;
          ctx!.strokeStyle = brand(0.7 * n.shield);
          ctx!.lineWidth = 1.2;
          ctx!.beginPath();
          ctx!.arc(n.x, n.y, 4 + s * 26, 0, Math.PI * 2);
          ctx!.stroke();
          ctx!.beginPath();
          for (let k = 0; k < 6; k++) {
            const ang = (Math.PI / 3) * k + Math.PI / 6;
            const px = n.x + Math.cos(ang) * 7;
            const py = n.y + Math.sin(ang) * 7;
            if (k === 0) ctx!.moveTo(px, py);
            else ctx!.lineTo(px, py);
          }
          ctx!.closePath();
          ctx!.strokeStyle = brand(0.9 * n.shield);
          ctx!.stroke();
        }
      }

      if (!reduced) raf = requestAnimationFrame(frame);
    }

    function onVisibility() {
      cancelAnimationFrame(raf);
      if (!document.hidden && !reduced) {
        last = performance.now();
        raf = requestAnimationFrame(frame);
      }
    }
    function onMove(e: PointerEvent) {
      mouse.x = e.clientX;
      mouse.y = e.clientY;
    }

    resize();
    raf = requestAnimationFrame(frame);
    window.addEventListener("resize", resize);
    window.addEventListener("pointermove", onMove, { passive: true });
    document.addEventListener("visibilitychange", onVisibility);
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", resize);
      window.removeEventListener("pointermove", onMove);
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, []);

  return (
    <div aria-hidden="true" className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
      {/* Fine cyber grid that fades out toward the edges. */}
      <div
        className="absolute inset-0 opacity-[0.35]"
        style={{
          backgroundImage:
            "linear-gradient(to right, color-mix(in srgb, var(--brand) 9%, transparent) 1px, transparent 1px), linear-gradient(to bottom, color-mix(in srgb, var(--brand) 9%, transparent) 1px, transparent 1px)",
          backgroundSize: "48px 48px",
          maskImage: "radial-gradient(ellipse 80% 60% at 50% 30%, #000 30%, transparent 80%)",
          WebkitMaskImage: "radial-gradient(ellipse 80% 60% at 50% 30%, #000 30%, transparent 80%)",
        }}
      />
      {/* Ambient colour blooms. */}
      <div className="absolute -top-40 left-1/2 h-[520px] w-[820px] -translate-x-1/2 rounded-full bg-brand/10 blur-3xl" />
      <div className="absolute -right-40 top-1/3 h-[420px] w-[420px] rounded-full bg-brand-2/10 blur-3xl" />
      <canvas ref={canvasRef} className="absolute inset-0" />
      {/* Vignette keeps text readable over the motion. */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,transparent_40%,var(--background)_100%)] opacity-70" />
    </div>
  );
}
