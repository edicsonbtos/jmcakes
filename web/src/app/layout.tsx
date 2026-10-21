import type { Metadata, Viewport } from "next";
import "@fontsource-variable/archivo/wdth.css";
import "./globals.css";
import { displayBusinessName, getPublicSettings } from "@/lib/settings";
import { ToastProvider } from "@/components/ui/Toast";

export async function generateMetadata(): Promise<Metadata> {
  const name = displayBusinessName(await getPublicSettings());
  return {
    title: { default: name, template: `%s · ${name}` },
    description: "Panel del negocio: clientes, fiado, abonos, productos y tasa.",
    robots: { index: false, follow: false },
  };
}

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#FFFFFF" },
    { media: "(prefers-color-scheme: dark)", color: "#0F0F0F" },
  ],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es-VE">
      <body className="min-h-dvh bg-canvas text-ink antialiased">
        <ToastProvider>{children}</ToastProvider>
      </body>
    </html>
  );
}
