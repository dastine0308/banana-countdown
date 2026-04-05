"use client";

export default function Header() {
  return (
    <header
      className="w-full flex items-center justify-between px-8 py-5"
      style={{ borderBottom: "1px solid var(--border)" }}
    >
      <div className="flex items-center gap-3">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src="/images/banana-upload.png"
          alt="banana logo"
          style={{ width: "32px", height: "32px", objectFit: "contain", imageRendering: "pixelated" }}
        />
        <span
          style={{
            fontFamily: "var(--font-display)",
            fontWeight: 800,
            fontSize: "1.1rem",
            letterSpacing: "-0.02em",
            color: "var(--yellow)",
          }}
        >
          Banana Countdown
        </span>
      </div>

      {/* <div
        style={{
          fontFamily: "var(--font-mono)",
          fontSize: "0.7rem",
          color: "var(--text-muted)",
          letterSpacing: "0.08em",
        }}
      >
        ENSF617 · Computer Vision
      </div> */}
    </header>
  );
}
