import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "🍌 Banana Countdown",
  description: "AI-powered banana ripeness detector and shelf-life predictor — ENSF617",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
