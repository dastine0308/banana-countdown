"use client";

import { useCallback, useEffect, useRef, useState, type ChangeEvent } from "react";

type WebcamCaptureProps = {
  isOpen: boolean;
  onClose: () => void;
  onCapture: (file: File) => void;
  disabled?: boolean;
};

function stopTracks(stream: MediaStream | null) {
  stream?.getTracks().forEach((t) => t.stop());
}

export default function WebcamCapture({
  isOpen,
  onClose,
  onCapture,
  disabled = false,
}: WebcamCaptureProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [ready, setReady] = useState(false);

  const cleanupStream = useCallback(() => {
    stopTracks(streamRef.current);
    streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
    setReady(false);
  }, []);

  useEffect(() => {
    if (!isOpen) {
      cleanupStream();
      setError(null);
      return;
    }

    let cancelled = false;

    async function startCamera() {
      setError(null);
      setReady(false);

      if (!navigator.mediaDevices?.getUserMedia) {
        setError("This browser does not support camera access.");
        return;
      }

      const attempts: MediaStreamConstraints[] = [
        { video: { facingMode: { ideal: "environment" } }, audio: false },
        { video: { facingMode: "environment" }, audio: false },
        { video: { facingMode: { ideal: "user" } }, audio: false },
        { video: true, audio: false },
      ];

      for (const constraints of attempts) {
        try {
          const stream = await navigator.mediaDevices.getUserMedia(constraints);
          if (cancelled) {
            stopTracks(stream);
            return;
          }
          streamRef.current = stream;
          const el = videoRef.current;
          if (el) {
            el.srcObject = stream;
            await el.play().catch(() => {});
          }
          setReady(true);
          return;
        } catch {
          /* try next */
        }
      }

      setError("Could not open camera. Check permissions or use upload below.");
    }

    startCamera();

    return () => {
      cancelled = true;
      cleanupStream();
    };
  }, [isOpen, cleanupStream]);

  const handleCapture = () => {
    const video = videoRef.current;
    if (!video || !ready || disabled) return;

    const w = video.videoWidth;
    const h = video.videoHeight;
    if (!w || !h) return;

    const canvas = document.createElement("canvas");
    canvas.width = w;
    canvas.height = h;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.drawImage(video, 0, 0, w, h);

    canvas.toBlob(
      (blob) => {
        if (!blob) return;
        const file = new File([blob], "camera-capture.jpg", { type: "image/jpeg" });
        cleanupStream();
        onCapture(file);
        onClose();
      },
      "image/jpeg",
      0.92
    );
  };

  const handleNativeChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    cleanupStream();
    onCapture(file);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-[10050] flex items-center justify-center p-4"
      style={{ background: "rgba(14, 14, 14, 0.92)" }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="webcam-title"
    >
      <div
        className="w-full max-w-lg flex flex-col gap-4 rounded-xl p-5"
        style={{
          background: "var(--surface)",
          border: "1px solid var(--border)",
          boxShadow: "0 24px 80px rgba(0,0,0,0.55)",
        }}
      >
        <div className="flex items-start justify-between gap-3">
          <h2
            id="webcam-title"
            style={{
              fontFamily: "var(--font-display)",
              fontWeight: 700,
              fontSize: "1.1rem",
              color: "var(--text)",
              letterSpacing: "-0.02em",
            }}
          >
            Camera
          </h2>
          <button
            type="button"
            onClick={() => {
              cleanupStream();
              onClose();
            }}
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: "0.7rem",
              color: "var(--text-muted)",
              background: "transparent",
              border: "1px solid var(--border)",
              borderRadius: "6px",
              padding: "6px 12px",
              cursor: "pointer",
            }}
          >
            CLOSE
          </button>
        </div>

        <div
          className="relative w-full overflow-hidden rounded-lg"
          style={{
            aspectRatio: "4 / 3",
            background: "var(--surface-2)",
            border: "1px solid var(--border)",
          }}
        >
          {!error && (
            <>
              <video
                ref={videoRef}
                className="h-full w-full object-cover"
                autoPlay
                playsInline
                muted
                style={{ transform: "scaleX(1)" }}
              />
              {!ready && (
                <div
                  className="absolute inset-0 flex items-center justify-center"
                  style={{
                    background: "rgba(14, 14, 14, 0.65)",
                    fontFamily: "var(--font-mono)",
                    fontSize: "0.7rem",
                    color: "var(--yellow)",
                    letterSpacing: "0.08em",
                  }}
                >
                  STARTING CAMERA…
                </div>
              )}
            </>
          )}
          {error && (
            <div
              className="flex h-full min-h-[200px] flex-col items-center justify-center gap-3 px-4 text-center"
              style={{ fontFamily: "var(--font-body)", fontSize: "0.85rem", color: "var(--text-muted)" }}
            >
              <p>{error}</p>
              <label
                style={{
                  fontFamily: "var(--font-display)",
                  fontWeight: 700,
                  fontSize: "0.8rem",
                  letterSpacing: "0.06em",
                  background: "var(--yellow)",
                  color: "#0e0e0e",
                  borderRadius: "6px",
                  padding: "10px 18px",
                  cursor: "pointer",
                }}
              >
                <input
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  capture="environment"
                  className="hidden"
                  onChange={handleNativeChange}
                />
                OPEN DEVICE CAMERA
              </label>
              <p style={{ fontSize: "0.75rem", opacity: 0.85 }}>
                Uses your phone or tablet&apos;s native camera when live preview isn&apos;t available.
              </p>
            </div>
          )}
        </div>

        {!error && (
          <div className="flex flex-wrap items-center justify-center gap-3">
            <button
              type="button"
              onClick={handleCapture}
              disabled={!ready || disabled}
              style={{
                fontFamily: "var(--font-display)",
                fontWeight: 700,
                fontSize: "0.85rem",
                letterSpacing: "0.06em",
                background: ready && !disabled ? "var(--yellow)" : "var(--border)",
                color: "#0e0e0e",
                border: "none",
                borderRadius: "6px",
                padding: "12px 28px",
                cursor: ready && !disabled ? "pointer" : "not-allowed",
                opacity: ready && !disabled ? 1 : 0.6,
              }}
            >
              CAPTURE
            </button>
            <label
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: "0.7rem",
                color: "var(--yellow-dim)",
                cursor: "pointer",
                textDecoration: "underline",
                textUnderlineOffset: "3px",
              }}
            >
              <input
                type="file"
                accept="image/jpeg,image/png,image/webp"
                capture="environment"
                className="hidden"
                onChange={handleNativeChange}
              />
              Use native camera app
            </label>
          </div>
        )}

        {error && (
          <p
            className="text-center"
            style={{ fontFamily: "var(--font-mono)", fontSize: "0.65rem", color: "var(--text-muted)" }}
          >
            HTTPS or localhost is required for live camera in most browsers.
          </p>
        )}
      </div>
    </div>
  );
}
