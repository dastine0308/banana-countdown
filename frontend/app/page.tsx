"use client";

import { useState, useCallback } from "react";
import Uploader from "@/components/Uploader";
import ResultCard from "@/components/ResultCard";
import Header from "@/components/Header";

export type Detection = {
  class_label: string;
  confidence: number;
  bounding_box: [number, number, number, number];
  days_remaining: number;
};

export type PredictResponse = {
  detections: Detection[];
  annotated_image: string; // base64 PNG
};

export default function Home() {
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState<string | null>(null);
  const [result, setResult]     = useState<PredictResponse | null>(null);
  const [preview, setPreview]   = useState<string | null>(null);

  const handleFile = useCallback(async (file: File) => {
    setError(null);
    setResult(null);

    // Local preview
    const reader = new FileReader();
    reader.onload = (e) => setPreview(e.target?.result as string);
    reader.readAsDataURL(file);

    // Send to Flask API
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("image", file);

      const res = await fetch("/api/predict", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.error ?? `Server error ${res.status}`);
      }

      const data: PredictResponse = await res.json();

      if (!data.detections || data.detections.length === 0) {
        throw new Error("No banana detected in this image. Try a clearer photo.");
      }

      setResult(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }, []);

  const handleReset = () => {
    setResult(null);
    setPreview(null);
    setError(null);
  };

  return (
    <main className="min-h-screen flex flex-col" style={{ background: "var(--bg)" }}>
      <Header />

      <div className="flex-1 flex flex-col items-center px-4 pb-20 pt-8">

        {/* ── Upload zone (shown until result) ── */}
        {!result && (
          <div className="w-full max-w-xl fade-up">
            <Uploader onFile={handleFile} loading={loading} preview={preview} />
            {error && (
              <p className="mt-4 text-center text-sm fade-up"
                 style={{ color: "var(--red)", fontFamily: "var(--font-mono)" }}>
                ⚠ {error}
              </p>
            )}
          </div>
        )}

        {/* ── Results ── */}
        {result && (
          <div className="w-full max-w-4xl fade-up">
            <ResultCard result={result} onReset={handleReset} />
          </div>
        )}
      </div>
    </main>
  );
}
