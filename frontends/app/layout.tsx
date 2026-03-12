import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Contact Form Agent",
  description: "AI powered contact form automation",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
