"use client";

import React from "react";
import { DayPlan } from "@/types/meal-plan";

interface DayTabsProps {
  days: DayPlan[];
  selectedDayId: string;
  onSelectDay: (dayId: string) => void;
}

export function DayTabs({ days, selectedDayId, onSelectDay }: DayTabsProps) {
  // Format short date (e.g. "2026-10-31" -> "31 Ott")
  const formatShortDate = (dateStr: string) => {
    const parts = dateStr.split("-");
    if (parts.length === 3) {
      const day = parts[2];
      const monthNum = parts[1];
      const months = ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu", "Lug", "Ago", "Set", "Ott", "Nov", "Dic"];
      const monthName = months[parseInt(monthNum, 10) - 1] || "";
      return `${day} ${monthName}`;
    }
    return dateStr;
  };

  return (
    <nav className="border-b border-[#E7E5E4] bg-white py-3">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex space-x-2 overflow-x-auto pb-1 scrollbar-none sm:space-x-3">
          {days.map((day) => {
            const isSelected = day.id === selectedDayId;
            const hasFreeMeal = day.meals.cena.is_free_meal;

            return (
              <button
                key={day.id}
                onClick={() => onSelectDay(day.id)}
                className={`flex flex-col items-center justify-center rounded-lg px-4 py-2.5 text-center transition-all min-w-[100px] sm:min-w-[120px] ${
                  isSelected
                    ? "border-2 border-[#1A1A1A] bg-[#1A1A1A] text-white shadow-sm"
                    : "border border-[#E7E5E4] bg-[#FAF9F6] text-stone-700 hover:border-stone-400 hover:bg-white"
                }`}
              >
                <div className="flex items-center gap-1.5">
                  <span className={`text-xs font-semibold ${isSelected ? "text-white" : "text-[#1A1A1A]"}`}>
                    {day.day_name}
                  </span>
                  {hasFreeMeal && (
                    <span
                      title="Pasto Libero (Pizza Margherita)"
                      className={`h-1.5 w-1.5 rounded-full ${
                        isSelected ? "bg-[#C25E3F]" : "bg-[#C25E3F]"
                      }`}
                    />
                  )}
                </div>
                <span
                  className={`mt-0.5 text-[11px] ${
                    isSelected ? "text-stone-300" : "text-stone-500"
                  }`}
                >
                  {formatShortDate(day.date)}
                </span>
                <span
                  className={`mt-1 font-serif text-[11px] ${
                    isSelected ? "text-stone-200" : "text-stone-600"
                  }`}
                >
                  {day.daily_macros.kcal} kcal
                </span>
              </button>
            );
          })}
        </div>
      </div>
    </nav>
  );
}
