import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Navbar } from "@/components/layout/navbar";
import { Sidebar } from "@/components/layout/sidebar";
import { AgentProvider } from "@/lib/agent-context";
import { ThemeProvider } from "@/lib/theme-context";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "AI Coding Agents Industry Analysis",
  description: "Track and compare how AI coding assistants (Claude Code, GitHub Copilot, OpenAI Codex, Cursor AI) are being adopted across different industries using NAICS classification.",
  keywords: ["AI coding", "Claude Code", "GitHub Copilot", "Cursor AI", "OpenAI Codex", "industry analysis", "NAICS"],
  authors: [{ name: "Alexander Quispe" }],
  openGraph: {
    title: "AI Coding Agents Industry Analysis",
    description: "Track and compare AI coding assistant adoption across industries",
    type: "website",
  },
};

// Inline script to prevent flash of wrong theme
const themeScript = `
(function() {
  try {
    var t = localStorage.getItem('theme');
    if (!t || !['dark','light','system'].includes(t)) t = 'dark';
    var resolved = t;
    if (t === 'system') {
      resolved = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    document.documentElement.classList.add(resolved);
  } catch(e) {
    document.documentElement.classList.add('dark');
  }
})();
`;

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="scroll-smooth" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased min-h-screen flex flex-col bg-[var(--bg-primary)]`}
      >
        <ThemeProvider>
          <AgentProvider>
            <Navbar />
            <div className="flex flex-1">
              <Sidebar />
              <main className="flex-1 overflow-x-hidden">
                {children}
              </main>
            </div>
          </AgentProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
