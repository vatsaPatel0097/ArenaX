import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ArenaX | Open-Source LLM Battleground & Evaluation Platform",
  description: "Compare, evaluate, and rank LLM models side-by-side with real-time SSE streaming and Elo rating leaderboards.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
