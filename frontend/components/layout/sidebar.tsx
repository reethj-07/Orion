"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/utils";

const links = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/workflow/new", label: "New workflow" },
  { href: "/documents", label: "Documents" },
  { href: "/search", label: "Search" },
  { href: "/analytics", label: "Analytics" },
  { href: "/settings", label: "Settings" },
];

/**
 * Primary navigation sidebar for authenticated application pages.
 */
export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="hidden w-64 flex-col border-r bg-card/40 p-4 md:flex">
      <div className="mb-8 text-lg font-semibold tracking-tight">Orion</div>
      <nav className="flex flex-1 flex-col gap-1">
        {links.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            className={cn(
              "rounded-md px-3 py-2 text-sm font-medium transition hover:bg-accent",
              pathname.startsWith(link.href) && "bg-accent",
            )}
          >
            {link.label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
