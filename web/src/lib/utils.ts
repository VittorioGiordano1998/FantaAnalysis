import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/** Unisce classi Tailwind senza conflitti (pattern shadcn/Sphynx). */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}
