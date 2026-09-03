import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "WEXSPACE ProofDesk — Governed Human-Agent Work",
  description:
    "A WebMCP-powered evidence workbench where humans and browser agents share one governed, auditable workflow.",
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
