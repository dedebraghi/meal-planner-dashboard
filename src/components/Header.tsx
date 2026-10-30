"use client";

import React from "react";
import { ShoppingCart, BookOpen, Calendar } from "lucide-react";
import { CartSummary } from "@/types/meal-plan";

interface HeaderProps {
  cartSummary: CartSummary;
  onOpenCart: () => void;
  onOpenDietInfo: () => void;
}

export function Header({ cartSummary, onOpenCart, onOpenDietInfo }: HeaderProps) {
  return (
    <header className="sticky top-0 z-30 border-b border-[#E7E5E4] bg-white/95 backdrop-blur-sm">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
        {/* Brand & Editorial Title */}
        <div className="flex flex-col">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold tracking-wider text-[#4A6B53] uppercase">
              Protocollo Nutrizionale
            </span>
            <span className="text-xs text-stone-400">•</span>
            <span className="text-xs text-stone-500">Dott.ssa Caglioni</span>
          </div>
          <h1 className="font-serif text-2xl font-semibold tracking-tight text-[#1A1A1A] sm:text-3xl">
            Menu Settimanale
          </h1>
          <div className="mt-1 flex items-center gap-2 text-xs text-stone-500">
            <Calendar className="h-3.5 w-3.5 text-stone-400" />
            <span>31 Ottobre – 06 Novembre 2026</span>
            <span>•</span>
            <span className="font-medium text-stone-700">Target 2.063 kcal / 112g Proteine</span>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-3">
          {/* Nutritionist Guidelines Button */}
          <button
            onClick={onOpenDietInfo}
            className="hidden items-center gap-2 rounded-md border border-[#E7E5E4] bg-white px-3 py-2 text-xs font-medium text-stone-700 transition-colors hover:bg-stone-50 sm:flex"
            title="Linee guida e indicazioni della Dott.ssa Caglioni"
          >
            <BookOpen className="h-4 w-4 text-stone-500" />
            <span>Linee Guida</span>
          </button>

          {/* Esselunga Cart Button */}
          <button
            onClick={onOpenCart}
            className="flex items-center gap-2.5 rounded-md border border-[#C25E3F]/40 bg-[#FAF9F6] px-3.5 py-2 text-xs font-semibold text-[#1A1A1A] transition-colors hover:border-[#C25E3F] hover:bg-white"
          >
            <ShoppingCart className="h-4 w-4 text-[#C25E3F]" />
            <div className="flex flex-col text-left">
              <span className="leading-tight">Carrello Esselunga</span>
              <span className="text-[11px] font-normal text-stone-500">
                {cartSummary.items_count} art. • {cartSummary.total_estimated_eur.toFixed(2)} €
              </span>
            </div>
          </button>
        </div>
      </div>
    </header>
  );
}
