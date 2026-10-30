"use client";

import React from "react";
import { DayPlan, Meal } from "@/types/meal-plan";
import { MealCard } from "./MealCard";

interface DayViewProps {
  day: DayPlan;
  onOpenRecipe: (meal: Meal) => void;
}

export function DayView({ day, onOpenRecipe }: DayViewProps) {
  const { colazione, pranzo, spuntino_pomeriggio, cena, dopocena } = day.meals;

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      {/* Editorial Section: Pasti Principali (Pranzo e Cena) */}
      <section className="mb-10">
        <div className="mb-4 flex items-center justify-between border-b border-[#E7E5E4] pb-2">
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-[#4A6B53]">
              Pasti Principali • Frequenze Nutrizionali
            </span>
            <h2 className="font-serif text-xl font-semibold text-[#1A1A1A]">
              Pranzo & Cena
            </h2>
          </div>
          <span className="text-xs text-stone-500">
            Min. 200g verdura • 10g Olio EVO a crudo
          </span>
        </div>

        <div className="grid grid-cols-1 gap-6 md:grid-cols-12">
          <MealCard meal={pranzo} isMainMeal={true} onOpenRecipe={onOpenRecipe} />
          <MealCard meal={cena} isMainMeal={true} onOpenRecipe={onOpenRecipe} />
        </div>
      </section>

      {/* Editorial Section: Colazione e Spuntini */}
      <section>
        <div className="mb-4 flex items-center justify-between border-b border-[#E7E5E4] pb-2">
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-stone-500">
              Energia Costante • Rilascio Graduale
            </span>
            <h2 className="font-serif text-xl font-semibold text-[#1A1A1A]">
              Colazione e Spuntini
            </h2>
          </div>
          <span className="text-xs text-stone-500">
            Frutta fresca 150g • Yogurt greco 0% 150g • Frutta secca 20g
          </span>
        </div>

        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 md:grid-cols-12">
          <MealCard meal={colazione} isMainMeal={false} onOpenRecipe={onOpenRecipe} />
          <MealCard meal={spuntino_pomeriggio} isMainMeal={false} onOpenRecipe={onOpenRecipe} />
          <MealCard meal={dopocena} isMainMeal={false} onOpenRecipe={onOpenRecipe} />
        </div>
      </section>
    </div>
  );
}
