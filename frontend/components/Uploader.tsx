"use client";

import { useRef, useState, DragEvent, ChangeEvent } from "react";
import WebcamCapture from "@/components/WebcamCapture";

interface UploaderProps {
  onFile: (file: File) => void;
  loading: boolean;
  preview: string | null;
}

const ACCEPTED = ["image/jpeg", "image/png", "image/webp"];

export default function Uploader({ onFile, loading, preview }: UploaderProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [webcamOpen, setWebcamOpen] = useState(false);

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file && ACCEPTED.includes(file.type)) onFile(file);
  };

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) onFile(file);
  };

  return (
    <div className="flex flex-col items-center gap-6">
      {/* ── Hero label ── */}
      <div className="text-center">
        <h1
          style={{
            fontFamily: "var(--font-display)",
            fontWeight: 800,
            fontSize: "clamp(2rem, 6vw, 3.2rem)",
            letterSpacing: "-0.04em",
            lineHeight: 1.2,
            color: "var(--text)",
          }}
        >
          How ripe is your
          <br />
          <span style={{ color: "var(--yellow)" }}>banana?</span>
        </h1>
        <p
          className="mt-3"
          style={{
            fontFamily: "var(--font-body)",
            fontSize: "0.9rem",
            color: "var(--text-muted)",
            fontWeight: 300,
          }}
        >
          Upload a photo or use your camera — AI detects ripeness &amp; estimates shelf life.
        </p>
      </div>

      {/* ── Drop zone ── */}
      <div
        className={`drop-zone w-full flex flex-col items-center justify-center gap-4 ${dragging ? "dragging" : ""} ${loading ? "pulse-glow" : ""}`}
        style={{
          minHeight: preview ? "auto" : "260px",
          padding: preview ? "12px" : "40px 24px",
          position: "relative",
        }}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => !loading && inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          className="hidden"
          onChange={handleChange}
        />

        {loading ? (
          <div className="flex flex-col items-center gap-3">
            <Spinner />
            <span
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: "0.75rem",
                color: "var(--yellow)",
                letterSpacing: "0.06em",
              }}
            >
              RUNNING PIPELINE…
            </span>
          </div>
        ) : preview ? (
          <div className="flex flex-col items-center gap-2 w-full">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={preview}
              alt="Preview"
              className="rounded-lg w-full object-contain"
              style={{ maxHeight: "320px" }}
            />
            <div className="flex flex-col items-center gap-2 w-full">
              <span
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: "0.65rem",
                  color: "var(--text-muted)",
                }}
              >
                tap image to pick a file, or use camera
              </span>
              <div className="flex flex-wrap justify-center gap-2">
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    if (!loading) setWebcamOpen(true);
                  }}
                  style={{
                    fontFamily: "var(--font-display)",
                    fontWeight: 700,
                    fontSize: "0.75rem",
                    letterSpacing: "0.06em",
                    background: "transparent",
                    color: "var(--yellow)",
                    border: "1px solid var(--yellow)",
                    borderRadius: "6px",
                    padding: "6px 14px",
                    cursor: loading ? "not-allowed" : "pointer",
                    opacity: loading ? 0.5 : 1,
                  }}
                >
                  USE CAMERA
                </button>
              </div>
            </div>
          </div>
        ) : (
          <>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src="/images/banana-upload.png"
              alt="banana"
              style={{ width: "90px", height: "90px", objectFit: "contain", imageRendering: "pixelated", opacity: 0.7 }}
            />
            <div className="text-center">
              <p
                style={{
                  fontFamily: "var(--font-display)",
                  fontWeight: 600,
                  fontSize: "0.95rem",
                  color: "var(--text)",
                }}
              >
                Drop image here
              </p>
              <p
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: "0.7rem",
                  color: "var(--text-muted)",
                  marginTop: "4px",
                }}
              >
                JPG · PNG · WEBP
              </p>
            </div>
            <div
              className="flex flex-wrap justify-center gap-2"
              style={{ marginTop: "4px" }}
              onClick={(e) => e.stopPropagation()}
            >
              <button
                type="button"
                onClick={() => !loading && inputRef.current?.click()}
                style={{
                  fontFamily: "var(--font-display)",
                  fontWeight: 700,
                  fontSize: "0.8rem",
                  letterSpacing: "0.06em",
                  background: "var(--yellow)",
                  color: "#0e0e0e",
                  border: "none",
                  borderRadius: "6px",
                  padding: "8px 20px",
                  cursor: loading ? "not-allowed" : "pointer",
                  opacity: loading ? 0.6 : 1,
                }}
              >
                BROWSE FILE
              </button>
              <button
                type="button"
                onClick={() => !loading && setWebcamOpen(true)}
                style={{
                  fontFamily: "var(--font-display)",
                  fontWeight: 700,
                  fontSize: "0.8rem",
                  letterSpacing: "0.06em",
                  background: "transparent",
                  color: "var(--yellow)",
                  border: "1px solid var(--yellow)",
                  borderRadius: "6px",
                  padding: "8px 20px",
                  cursor: loading ? "not-allowed" : "pointer",
                  opacity: loading ? 0.6 : 1,
                }}
              >
                USE CAMERA
              </button>
            </div>
          </>
        )}
      </div>

      <WebcamCapture
        isOpen={webcamOpen}
        onClose={() => setWebcamOpen(false)}
        onCapture={onFile}
        disabled={loading}
      />
    </div>
  );
}

function Spinner() {
  return (
    <div
      style={{
        width: "36px",
        height: "36px",
        border: "2.5px solid var(--border)",
        borderTop: "2.5px solid var(--yellow)",
        borderRadius: "50%",
        animation: "spin 0.8s linear infinite",
      }}
    />
  );
}
