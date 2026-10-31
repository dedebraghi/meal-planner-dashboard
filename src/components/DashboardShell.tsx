"use client";

import React, { useState } from "react";
import { WeeklyPlanData, Meal } from "@/types/meal-plan";
import { Header } from "./Header";
import { MacroBar } from "./MacroBar";
import { DayTabs } from "./DayTabs";
import { DayView } from "./DayView";
import { RecipeDrawer } from "./RecipeDrawer";
import { CartModal } from "./CartModal";
import { X, CheckCircle2, ShieldCheck, Heart } from "lucide-react";

interface DashboardShellProps {
  initialData: WeeklyPlanData;
}

export function DashboardShell({ initialData }: DashboardShellProps) {
  const [selectedDayId, setSelectedDayId] = useState<string>(
    initialData.days[0]?.id || "sabato-2026-10-31"
  );
  const [activeRecipeMeal, setActiveRecipeMeal] = useState<Meal | null>(null);
  const [isCartOpen, setIsCartOpen] = useState<boolean>(false);
  const [isDietInfoOpen, setIsDietInfoOpen] = useState<boolean>(false);

  const selectedDay =
    initialData.days.find((d) => d.id === selectedDayId) || initialData.days[0];

  return (
    <div className="flex min-h-screen flex-col">
      {/* 1. Header with Cart Summary & Navigation */}
      <Header
        cartSummary={initialData.cart_summary}
        onOpenCart={() => setIsCartOpen(true)}
        onOpenDietInfo={() => setIsDietInfoOpen(true)}
      />

      {/* 2. Macro Nutrition Bar comparing Day Actuals vs 2063 kcal Target */}
      <MacroBar
        target={initialData.macro_target}
        actual={selectedDay.daily_macros}
        dayName={selectedDay.day_name}
      />

      {/* 3. 7-Day Navigation Tabs (Sabato 31 Ott - Venerdì 06 Nov) */}
      <DayTabs
        days={initialData.days}
        selectedDayId={selectedDayId}
        onSelectDay={(dayId) => setSelectedDayId(dayId)}
      />

      {/* 4. Active Day Meal Timeline View (5 meals) */}
      <main className="flex-1">
        <DayView
          key={selectedDay.id}
          day={selectedDay}
          onOpenRecipe={(meal) => setActiveRecipeMeal(meal)}
        />
      </main>

      {/* 5. Interactive Recipe Drawer for Cooking Steps & Raw Ingredients */}
      <RecipeDrawer
        meal={activeRecipeMeal}
        onClose={() => setActiveRecipeMeal(null)}
      />

      {/* 6. Esselunga Weekly Cart Review Modal */}
      <CartModal
        cartSummary={initialData.cart_summary}
        isOpen={isCartOpen}
        onClose={() => setIsCartOpen(false)}
      />

      {/* 7. Nutritionist Clinical Guidelines Modal */}
      {isDietInfoOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div
            className="fixed inset-0 bg-stone-900/50 backdrop-blur-xs"
            onClick={() => setIsDietInfoOpen(false)}
          />
          <div className="relative w-full max-w-2xl rounded-xl border border-[#E7E5E4] bg-white p-6 shadow-2xl sm:p-8">
            <div className="flex items-start justify-between border-b border-stone-200 pb-4">
              <div>
                <span className="text-xs font-semibold uppercase tracking-wider text-[#4A6B53]">
                  Linee Guida Nutrizionali
                </span>
                <h3 className="mt-1 font-serif text-2xl font-semibold text-[#1A1A1A]">
                  Schema Dott.ssa Caglioni
                </h3>
                <p className="text-xs text-stone-500">
                  Davide Braghiroli • Regime 2.063 kcal / 112g Proteine
                </p>
              </div>
              <button
                onClick={() => setIsDietInfoOpen(false)}
                className="rounded-md p-1.5 text-stone-400 hover:bg-stone-100 hover:text-stone-700"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="mt-6 max-h-[60vh] space-y-5 overflow-y-auto pr-2 text-xs leading-relaxed text-stone-700">
              <div className="rounded-lg border border-[#4A6B53]/20 bg-[#4A6B53]/5 p-4">
                <div className="flex items-center gap-2 text-[#4A6B53]">
                  <Heart className="h-4 w-4 shrink-0" />
                  <span className="font-semibold text-xs">Regole Fondamentali</span>
                </div>
                <ul className="mt-2 space-y-1.5 text-stone-600">
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 text-[#4A6B53] shrink-0" />
                    <span>Tutti i pesi indicati sono intesi <strong>a crudo e al netto degli scarti</strong>.</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 text-[#4A6B53] shrink-0" />
                    <span>Bevi almeno <strong>2.0 litri di acqua al giorno</strong> per supportare il metabolismo.</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 text-[#4A6B53] shrink-0" />
                    <span>Usa succo di <strong>limone fresco</strong> per favorire l&apos;assorbimento del ferro vegetale e animale.</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 text-[#4A6B53] shrink-0" />
                    <span>Cottura pasta <strong>al dente</strong> e pane <strong>tostato</strong> per ridurre l&apos;impatto glicemico e prolungare la sazietà.</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 text-[#4A6B53] shrink-0" />
                    <span>Condimento massimo: <strong>10g olio extravergine d&apos;oliva a crudo</strong> a pranzo e cena.</span>
                  </li>
                </ul>
              </div>

              <div>
                <h4 className="font-serif text-sm font-semibold text-[#1A1A1A]">
                  Frequenze Proteiche Settimanali (14 Pasti Principali)
                </h4>
                <div className="mt-2 grid grid-cols-2 gap-2 text-stone-600 sm:grid-cols-4">
                  <div className="rounded border border-stone-200 bg-[#FAF9F6] p-2 text-center">
                    <strong className="block text-stone-900">Carne Bianca</strong>
                    <span>2 volte (150g)</span>
                  </div>
                  <div className="rounded border border-stone-200 bg-[#FAF9F6] p-2 text-center">
                    <strong className="block text-stone-900">Carne Rossa</strong>
                    <span>1 volta (120g)</span>
                  </div>
                  <div className="rounded border border-stone-200 bg-[#FAF9F6] p-2 text-center">
                    <strong className="block text-stone-900">Affettati Magri</strong>
                    <span>1 volta (100g)</span>
                  </div>
                  <div className="rounded border border-stone-200 bg-[#FAF9F6] p-2 text-center">
                    <strong className="block text-stone-900">Pesce</strong>
                    <span>2 volte (200g/125g)</span>
                  </div>
                  <div className="rounded border border-stone-200 bg-[#FAF9F6] p-2 text-center">
                    <strong className="block text-stone-900">Uova</strong>
                    <span>2 volte (2 uova)</span>
                  </div>
                  <div className="rounded border border-stone-200 bg-[#FAF9F6] p-2 text-center">
                    <strong className="block text-stone-900">Legumi/Tofu</strong>
                    <span>3 volte (150g/125g)</span>
                  </div>
                  <div className="rounded border border-stone-200 bg-[#FAF9F6] p-2 text-center">
                    <strong className="block text-stone-900">Formaggi</strong>
                    <span>2 volte (100g/70g)</span>
                  </div>
                  <div className="rounded border border-stone-200 bg-[#FAF9F6] p-2 text-center">
                    <strong className="block text-stone-900">Pasto Libero</strong>
                    <span>1 volta (Pizza)</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2 border-t border-stone-200 pt-3 text-[11px] text-stone-500">
                <ShieldCheck className="h-4 w-4 text-[#4A6B53] shrink-0" />
                <span>È consentito invertire liberamente il pranzo con la cena dello stesso giorno se gradito.</span>
              </div>
            </div>

            <div className="mt-6 border-t border-stone-200 pt-4">
              <button
                onClick={() => setIsDietInfoOpen(false)}
                className="w-full rounded-md bg-[#1A1A1A] py-2 text-xs font-semibold text-white transition-colors hover:bg-stone-800"
              >
                Ho Capito
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
