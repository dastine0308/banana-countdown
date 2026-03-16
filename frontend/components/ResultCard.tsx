"use client";

import type { PredictResponse, Detection } from "@/app/page";

const CLASS_BADGE: Record<string, string> = {
  "Fresh Unripe": "badge-fresh-unripe",
  "Fresh Ripe":   "badge-fresh-ripe",
  "Ripe":         "badge-ripe",
  "Overripe":     "badge-overripe",
  "Rotten":       "badge-rotten",
  "Unripe":       "badge-unripe",
};

const CLASS_IMG: Record<string, string> = {
  "Fresh Unripe": "/images/banana-upload.png",
  "Fresh Ripe":   "/images/banana-upload.png",
  "Ripe":         "/images/banana-detect.png",
  "Overripe":     "/images/banana-detect.png",
  "Rotten":       "/images/banana-peel.png",
  "Unripe":       "/images/banana-upload.png",
};

const SHELF_ADVICE: Record<string, string> = {
  "Fresh Unripe": "Leave at room temperature for a few days.",
  "Fresh Ripe":   "Best eaten within a day or two.",
  "Ripe":         "Perfect for eating now.",
  "Overripe":     "Use immediately — great for banana bread!",
  "Rotten":       "Discard or compost this one.",
  "Unripe":       "Give it a few more days to ripen.",
};

interface ResultCardProps {
  result: PredictResponse;
  onReset: () => void;
}

export default function ResultCard({ result, onReset }: ResultCardProps) {
  const { detections, annotated_image } = result;

  return (
    <div className="flex flex-col gap-8 fade-up">

      {/* ── Top bar ── */}
      <div className="flex items-center justify-between">
        <h2
          style={{
            fontFamily: "var(--font-display)",
            fontWeight: 800,
            fontSize: "1.3rem",
            letterSpacing: "-0.03em",
            color: "var(--text)",
          }}
        >
          {detections.length} banana{detections.length > 1 ? "s" : ""} detected
        </h2>
        <button
          onClick={onReset}
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: "0.7rem",
            letterSpacing: "0.06em",
            color: "var(--text-muted)",
            background: "none",
            border: "1px solid var(--border)",
            borderRadius: "6px",
            padding: "6px 14px",
            cursor: "pointer",
          }}
        >
          ← NEW IMAGE
        </button>
      </div>

      {/* ── Two-column layout: annotated image + detection cards ── */}
      <div className="grid gap-6" style={{ gridTemplateColumns: "1fr 1fr" }}>

        {/* Annotated image */}
        <div
          style={{
            borderRadius: "12px",
            overflow: "hidden",
            border: "1px solid var(--border)",
            background: "var(--surface)",
          }}
        >
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={annotated_image ? `data:image/png;base64,${annotated_image}` : "/images/banana-peeled.png"}
            alt="Annotated result"
            className="w-full h-full object-contain"
            style={{ maxHeight: "460px", display: "block", imageRendering: annotated_image ? "auto" : "pixelated" }}
          />
        </div>

        {/* Detection cards */}
        <div className="flex flex-col gap-4">
          {detections.map((det, i) => (
            <DetectionCard key={i} det={det} index={i} />
          ))}
        </div>
      </div>
    </div>
  );
}

function DetectionCard({ det, index }: { det: Detection; index: number }) {
  const badgeClass = CLASS_BADGE[det.class_label] ?? "";
  const imgSrc     = CLASS_IMG[det.class_label] ?? "/images/banana-detect.png";
  const advice     = SHELF_ADVICE[det.class_label] ?? "";
  const daysLabel  = det.days_remaining === 0
    ? "Use now"
    : det.days_remaining < 1
    ? `< 1 day left`
    : `${det.days_remaining} day${det.days_remaining !== 1 ? "s" : ""} left`;

  return (
    <div
      className="fade-up-delay"
      style={{
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderRadius: "12px",
        padding: "20px",
        display: "flex",
        flexDirection: "column",
        gap: "14px",
        animationDelay: `${index * 0.08}s`,
      }}
    >
      {/* Row 1: emoji + label + badge */}
      <div className="flex items-center gap-3">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={imgSrc}
          alt={det.class_label}
          style={{ width: "36px", height: "36px", objectFit: "contain", imageRendering: "pixelated", flexShrink: 0 }}
        />
        <div className="flex-1">
          <span
            style={{
              fontFamily: "var(--font-display)",
              fontWeight: 700,
              fontSize: "1rem",
              color: "var(--text)",
            }}
          >
            {det.class_label}
          </span>
          {detections_length_hint(index)}
        </div>
        <span
          className={`${badgeClass}`}
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: "0.65rem",
            fontWeight: 500,
            padding: "3px 8px",
            borderRadius: "4px",
            letterSpacing: "0.04em",
          }}
        >
          {(det.confidence * 100).toFixed(0)}% conf
        </span>
      </div>

      {/* Row 2: shelf life bar */}
      <div>
        <div className="flex items-center justify-between mb-1">
          <span
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: "0.65rem",
              color: "var(--text-muted)",
              letterSpacing: "0.05em",
            }}
          >
            SHELF LIFE
          </span>
          <span
            style={{
              fontFamily: "var(--font-display)",
              fontWeight: 700,
              fontSize: "0.85rem",
              color: shelfColor(det.days_remaining),
            }}
          >
            {daysLabel}
          </span>
        </div>
        <ShelfBar days={det.days_remaining} />
      </div>

      {/* Row 3: advice */}
      <p
        style={{
          fontFamily: "var(--font-body)",
          fontSize: "0.8rem",
          color: "var(--text-muted)",
          fontWeight: 300,
          lineHeight: 1.5,
        }}
      >
        {advice}
      </p>
    </div>
  );
}

// Tiny helper — avoids referencing outer scope detections array
function detections_length_hint(_index: number) { return null; }

function shelfColor(days: number): string {
  if (days <= 0)  return "var(--red)";
  if (days <= 1)  return "var(--orange)";
  if (days <= 3)  return "var(--yellow)";
  return "var(--green)";
}

function ShelfBar({ days }: { days: number }) {
  const MAX_DAYS = 10;
  const pct = Math.min(100, (days / MAX_DAYS) * 100);
  const color = shelfColor(days);

  return (
    <div
      style={{
        height: "6px",
        background: "var(--surface-2)",
        borderRadius: "3px",
        overflow: "hidden",
      }}
    >
      <div
        style={{
          height: "100%",
          width: `${pct}%`,
          background: color,
          borderRadius: "3px",
          transition: "width 0.6s ease",
        }}
      />
    </div>
  );
}
