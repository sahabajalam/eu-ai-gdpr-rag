import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "EU AI & GDPR Assistant",
  description: "RAG Assistant for EU AI Act and GDPR",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
