import type { Metadata } from "next";
import { Suspense } from "react";
import { Geist, Geist_Mono } from "next/font/google";
import { Footer } from "@/components/layout/footer";
import { Navbar, NavbarFallback } from "@/components/layout/navbar";
import { PreferencesProvider } from "@/i18n/provider";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Manee | منيع - check a suspicious link",
  description: "Check suspicious links, protect your browser and your messages, with the reasons why.",
  manifest: "/manifest.webmanifest",
};

// Runs before first paint so there is no light/dark or LTR/RTL flash. Dark is the default theme.
const PREFS_SCRIPT = `try{var d=document.documentElement;var l=localStorage.getItem("fs-lang")||"en";d.dataset.theme="dark";d.lang=l==="ar"?"ar":"en";d.dir=l==="ar"?"rtl":"ltr"}catch(e){document.documentElement.dataset.theme="dark"}`;

// Registers the service worker that lets the phone install Manee and list it in the Share menu.
const SW_SCRIPT = `if("serviceWorker"in navigator)addEventListener("load",function(){navigator.serviceWorker.register("/sw.js").catch(function(){})})`;

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      data-theme="dark"
      suppressHydrationWarning
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <head>
        <script dangerouslySetInnerHTML={{ __html: PREFS_SCRIPT }} />
        <script dangerouslySetInnerHTML={{ __html: SW_SCRIPT }} />
      </head>
      <body suppressHydrationWarning className="min-h-full flex flex-col">
        <PreferencesProvider>
          <Suspense fallback={<NavbarFallback />}>
            <Navbar />
          </Suspense>
          {children}
          <Footer />
        </PreferencesProvider>
      </body>
    </html>
  );
}
