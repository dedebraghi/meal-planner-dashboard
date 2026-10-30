import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Piano Nutrizionale • Davide Braghiroli",
  description: "Menu settimanale editoriale e spesa automatizzata Esselunga secondo le linee guida della Dott.ssa Caglioni",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="it" className="h-full bg-[#FAF9F6] antialiased">
      <body className="min-h-full font-sans text-[#1A1A1A] selection:bg-[#4A6B53]/20">
        {children}
      </body>
    </html>
  );
}
