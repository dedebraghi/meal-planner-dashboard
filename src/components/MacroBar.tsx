"use client";

import React from "react";
import { MacroTarget } from "@/types/meal-plan";

interface MacroBarProps {
  target: MacroTarget;
  actual: {
    kcal: number;
    carbs_g: number;
    proteins_g: number;
    fats_g: number;
  };
  dayName: string;
}

export function MacroBar({ target, actual, dayName }: MacroBarProps) {
  const kcalPercent = Math.min(100, Math.round((actual.kcal / target.kcal) * 100));
  const proteinPercent = Math.min(100, Math.round((actual.proteins_g / target.proteins_g) * 100));
  const carbsPercent = Math.min(100, Math.round((actual.carbs_g / target.carbs_g) * 100));
  const fatsPercent = Math.min(100, Math.round((actual.fats_g / target.fats_g) * 100));

  return (
    <section className="border-b border-[#E7E5E4] bg-white">
      <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-stone-500">
              Bilancio Nutrizionale • {dayName}
            </span>
            <span className="text-xs text-stone-300">|</span>
            <span className="text-xs text-stone-500">Target Bromatologico Giornaliero</span>
          </div>
          <div className="text-xs text-stone-500">
            Fabbisogno calorico base: <strong className="font-semibold text-stone-800">{target.kcal} kcal</strong> (Fibra: {target.fiber_g}g)
          </div>
        </div>

        {/* 4 Macro Cards Grid */}
        <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-4 sm:gap-4">
          {/* Calorie */}
          <div className="rounded-lg border border-[#E7E5E4] bg-[#FAF9F6] p-3">
            <div className="flex items-baseline justify-between">
              <span className="text-xs font-medium text-stone-500">Energia</span>
              <span className="text-[11px] font-semibold text-stone-700">{kcalPercent}%</span>
            </div>
            <div className="mt-1 flex items-baseline gap-1">
              <span className="font-serif text-lg font-semibold text-[#1A1A1A]">{actual.kcal}</span>
              <span className="text-xs text-stone-500">/ {target.kcal} kcal</span>
            </div>
            <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-stone-200">
              <div
                className="h-full rounded-full bg-[#1A1A1A] transition-all duration-300"
                style={{ width: `${kcalPercent}%` }}
              />
            </div>
          </div>

          {/* Proteine */}
          <div className="rounded-lg border border-[#E7E5E4] bg-[#FAF9F6] p-3">
            <div className="flex items-baseline justify-between">
              <span className="text-xs font-medium text-stone-500">Proteine (22%)</span>
              <span className="text-[11px] font-semibold text-[#4A6B53]">{proteinPercent}%</span>
            </div>
            <div className="mt-1 flex items-baseline gap-1">
              <span className="font-serif text-lg font-semibold text-[#1A1A1A]">{actual.proteins_g}g</span>
              <span className="text-xs text-stone-500">/ {target.proteins_g}g</span>
            </div>
            <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-stone-200">
              <div
                className="h-full rounded-full bg-[#4A6B53] transition-all duration-300"
                style={{ width: `${proteinPercent}%` }}
              />
            </div>
          </div>

          {/* Carboidrati */}
          <div className="rounded-lg border border-[#E7E5E4] bg-[#FAF9F6] p-3">
            <div className="flex items-baseline justify-between">
              <span className="text-xs font-medium text-stone-500">Carboidrati (49%)</span>
              <span className="text-[11px] font-semibold text-stone-700">{carbsPercent}%</span>
            </div>
            <div className="mt-1 flex items-baseline gap-1">
              <span className="font-serif text-lg font-semibold text-[#1A1A1A]">{actual.carbs_g}g</span>
              <span className="text-xs text-stone-500">/ {target.carbs_g}g</span>
            </div>
            <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-stone-200">
              <div
                className="h-full rounded-full bg-[#C25E3F] transition-all duration-300"
                style={{ width: `${carbsPercent}%` }}
              />
            </div>
          </div>

          {/* Grassi */}
          <div className="rounded-lg border border-[#E7E5E4] bg-[#FAF9F6] p-3">
            <div className="flex items-baseline justify-between">
              <span className="text-xs font-medium text-stone-500">Grassi (29%)</span>
              <span className="text-[11px] font-semibold text-stone-700">{fatsPercent}%</span>
            </div>
            <div className="mt-1 flex items-baseline gap-1">
              <span className="font-serif text-lg font-semibold text-[#1A1A1A]">{actual.fats_g}g</span>
              <span className="text-xs text-stone-500">/ {target.fats_g}g</span>
            </div>
            <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-stone-200">
              <div
                className="h-full rounded-full bg-stone-500 transition-all duration-300"
                style={{ width: `${fatsPercent}%` }}
              />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
