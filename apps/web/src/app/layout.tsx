import type { Metadata, ReactNode } from "next";

export const metadata: Metadata = {
  title: "RepoPilot",
  description: "Purpose-driven, grounded codebase onboarding tours.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
