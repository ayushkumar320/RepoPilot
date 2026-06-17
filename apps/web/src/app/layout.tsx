import type { ReactNode } from "react";
import type { Metadata } from "next";
import ".globals.css";

export const metadata: Metadata = {
  title: "RepoPilot Phase 4",
  description: "Purpose-driven, grounded codebase onboarding tours with a synchronized code viewer.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
