"use client";

import React, { useState, useEffect } from "react";
import Image from "next/image";
import { Utensils, Clock, Flame, ChevronRight, Sparkles } from "lucide-react";
import { Meal } from "@/types/meal-plan";

interface MealCardProps {
  meal: Meal;
  isMainMeal?: boolean;
  onOpenRecipe: (meal: Meal) => void;
}

export function MealCard({ meal, isMainMeal = false, onOpenRecipe }: MealCardProps) {
  const [imgSrc, setImgSrc] = useState<string>(meal.image_url || "/placeholder-dish.svg");

  useEffect(() => {
    setImgSrc(meal.image_url || "/placeholder-dish.svg");
  }, [meal.image_url, meal.id]);

  const mealTypeLabels: Record<Meal["meal_type"], string> = {
    colazione: "Colazione",
    pranzo: "Pranzo",
    spuntino_pomeriggio: "Spuntino Pomeriggio",
    cena: "Cena",
    dopocena: "Spuntino Dopocena",
  };

  const isFreeMeal = meal.is_free_meal;

  return (
    <article
      onClick={() => onOpenRecipe(meal)}
      className={`group relative flex cursor-pointer flex-col justify-between overflow-hidden rounded-xl border border-[#E7E5E4] bg-white transition-all hover:border-stone-400 hover:shadow-sm ${
        isMainMeal ? "md:col-span-6 lg:col-span-6" : "md:col-span-4 lg:col-span-4"
      }`}
    >
      <div>
        {/* Main meal hero dish image */}
        {isMainMeal && (
          <div className="relative aspect-[16/9] w-full overflow-hidden bg-stone-100 border-b border-[#E7E5E4]">
            <Image
              src={imgSrc}
              alt={meal.title}
              fill
              className="object-cover transition-transform duration-300 group-hover:scale-[1.02]"
              onError={() => setImgSrc("/placeholder-dish.svg")}
              sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
            />
            {/* Category Pill on Image */}
            <div className="absolute left-3 top-3 flex items-center gap-1.5">
              <span className="rounded-md border border-[#E7E5E4]/80 bg-white/95 px-2.5 py-1 text-[11px] font-semibold text-stone-800 shadow-sm backdrop-blur-xs">
                {mealTypeLabels[meal.meal_type]}
              </span>
              {isFreeMeal ? (
                <span className="flex items-center gap-1 rounded-md border border-[#C25E3F] bg-[#C25E3F] px-2.5 py-1 text-[11px] font-semibold text-white shadow-sm">
                  <Sparkles className="h-3 w-3" />
                  Pasto Libero
                </span>
              ) : (
                <span className="rounded-md border border-[#4A6B53]/30 bg-[#4A6B53]/10 px-2 py-1 text-[11px] font-medium text-[#4A6B53] backdrop-blur-xs">
                  {meal.category}
                </span>
              )}
            </div>
          </div>
        )}

        {/* Card Body */}
        <div className="p-4 sm:p-6">
          {!isMainMeal && (
            <div className="mb-2 flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-stone-500">
                {mealTypeLabels[meal.meal_type]}
              </span>
              <span className="rounded-md bg-stone-100 px-2 py-0.5 text-[11px] font-medium text-stone-600">
                {meal.category}
              </span>
            </div>
          )}

          <h2 className="font-serif text-lg font-semibold tracking-tight text-[#1A1A1A] group-hover:text-stone-700">
            {meal.title}
          </h2>

          {meal.subtitle && (
            <p className="mt-1 text-xs text-stone-500 line-clamp-2 leading-relaxed">
              {meal.subtitle}
            </p>
          )}

          {/* Key Ingredients Summary */}
          <div className="mt-4 border-t border-stone-100 pt-3">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-stone-400">
              Ingredienti Chiave
            </span>
            <ul className="mt-1.5 space-y-1">
              {meal.ingredients.slice(0, 3).map((ing, idx) => (
                <li key={idx} className="flex items-center justify-between text-xs text-stone-600">
                  <span className="truncate pr-2">{ing.name}</span>
                  <span className="font-medium text-stone-900 shrink-0">{ing.qty}</span>
                </li>
              ))}
              {meal.ingredients.length > 3 && (
                <li className="text-[11px] italic text-stone-400">
                  + altri {meal.ingredients.length - 3} ingredienti
                </li>
              )}
            </ul>
          </div>
        </div>
      </div>

      {/* Card Footer: Macros & CTA */}
      <div className="border-t border-[#E7E5E4] bg-[#FAF9F6] p-4 sm:px-6 sm:py-3.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1 text-xs font-semibold text-[#1A1A1A]">
              <Flame className="h-3.5 w-3.5 text-[#C25E3F]" />
              <span>{meal.kcal} kcal</span>
            </div>
            <div className="hidden text-[11px] text-stone-500 sm:flex sm:gap-2">
              <span>P: <strong className="font-semibold text-stone-800">{meal.macros.proteins_g}g</strong></span>
              <span>C: <strong className="font-semibold text-stone-800">{meal.macros.carbs_g}g</strong></span>
              <span>G: <strong className="font-semibold text-stone-800">{meal.macros.fats_g}g</strong></span>
            </div>
          </div>

          <button
            type="button"
            className="flex items-center gap-1 text-xs font-semibold text-stone-800 transition-colors group-hover:text-[#4A6B53]"
          >
            {meal.recipe_steps && meal.recipe_steps.length > 0 ? (
              <>
                <Utensils className="h-3.5 w-3.5" />
                <span>Ricetta</span>
              </>
            ) : (
              <span>Dettagli</span>
            )}
            <ChevronRight className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>
    </article>
  );
}
