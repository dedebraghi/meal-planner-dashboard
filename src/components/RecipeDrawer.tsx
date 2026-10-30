"use client";

import React, { useState, useEffect } from "react";
import Image from "next/image";
import { X, Clock, Flame, Check, Info, Sparkles, ChefHat } from "lucide-react";
import { Meal } from "@/types/meal-plan";

interface RecipeDrawerProps {
  meal: Meal | null;
  onClose: () => void;
}

export function RecipeDrawer({ meal, onClose }: RecipeDrawerProps) {
  const [checkedIngredients, setCheckedIngredients] = useState<Record<number, boolean>>({});
  const [imgSrc, setImgSrc] = useState<string>("/placeholder-dish.svg");

  useEffect(() => {
    if (meal) {
      setCheckedIngredients({});
      setImgSrc(meal.image_url || "/placeholder-dish.svg");
    }
  }, [meal]);

  // Handle ESC key press
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  if (!meal) return null;

  const toggleIngredient = (idx: number) => {
    setCheckedIngredients((prev) => ({
      ...prev,
      [idx]: !prev[idx],
    }));
  };

  const isFreeMeal = meal.is_free_meal;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-stone-900/40 backdrop-blur-xs transition-opacity"
        onClick={onClose}
      />

      {/* Drawer Container */}
      <div className="fixed inset-y-0 right-0 flex max-w-full pl-10">
        <div className="w-screen max-w-xl bg-white shadow-xl">
          <div className="flex h-full flex-col overflow-y-auto">
            {/* Drawer Header */}
            <div className="border-b border-[#E7E5E4] px-6 py-5">
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold uppercase tracking-wider text-[#4A6B53]">
                      {meal.category}
                    </span>
                    {isFreeMeal && (
                      <span className="flex items-center gap-1 rounded bg-[#C25E3F] px-2 py-0.5 text-[10px] font-semibold text-white">
                        <Sparkles className="h-3 w-3" />
                        Pasto Libero
                      </span>
                    )}
                  </div>
                  <h2 className="mt-1 font-serif text-2xl font-semibold text-[#1A1A1A]">
                    {meal.title}
                  </h2>
                  {meal.subtitle && (
                    <p className="mt-1 text-xs text-stone-500">{meal.subtitle}</p>
                  )}
                </div>
                <button
                  onClick={onClose}
                  className="rounded-md p-1.5 text-stone-400 hover:bg-stone-100 hover:text-stone-700"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              {/* Time & Quick Stats */}
              <div className="mt-4 flex flex-wrap items-center gap-4 text-xs text-stone-600">
                {meal.prep_time_min !== undefined && (
                  <div className="flex items-center gap-1.5">
                    <Clock className="h-3.5 w-3.5 text-stone-400" />
                    <span>Prep: <strong className="font-semibold text-stone-800">{meal.prep_time_min} min</strong></span>
                  </div>
                )}
                {meal.cook_time_min !== undefined && meal.cook_time_min > 0 && (
                  <div className="flex items-center gap-1.5">
                    <ChefHat className="h-3.5 w-3.5 text-stone-400" />
                    <span>Cottura: <strong className="font-semibold text-stone-800">{meal.cook_time_min} min</strong></span>
                  </div>
                )}
                <div className="flex items-center gap-1.5">
                  <Flame className="h-3.5 w-3.5 text-[#C25E3F]" />
                  <span><strong className="font-semibold text-stone-800">{meal.kcal} kcal</strong></span>
                </div>
              </div>
            </div>

            {/* Dish Photo if available */}
            {meal.image_url && (
              <div className="relative aspect-[16/9] w-full border-b border-[#E7E5E4] bg-stone-100">
                <Image
                  src={imgSrc}
                  alt={meal.title}
                  fill
                  className="object-cover"
                  onError={() => setImgSrc("/placeholder-dish.svg")}
                />
              </div>
            )}

            {/* Macros Breakdown Bar */}
            <div className="border-b border-[#E7E5E4] bg-[#FAF9F6] px-6 py-3">
              <div className="grid grid-cols-4 gap-2 text-center text-xs">
                <div>
                  <span className="block text-[11px] text-stone-500">Kcal</span>
                  <strong className="font-serif text-sm text-[#1A1A1A]">{meal.kcal}</strong>
                </div>
                <div>
                  <span className="block text-[11px] text-stone-500">Proteine</span>
                  <strong className="font-serif text-sm text-[#4A6B53]">{meal.macros.proteins_g}g</strong>
                </div>
                <div>
                  <span className="block text-[11px] text-stone-500">Carboidrati</span>
                  <strong className="font-serif text-sm text-[#C25E3F]">{meal.macros.carbs_g}g</strong>
                </div>
                <div>
                  <span className="block text-[11px] text-stone-500">Grassi</span>
                  <strong className="font-serif text-sm text-stone-700">{meal.macros.fats_g}g</strong>
                </div>
              </div>
            </div>

            {/* Drawer Body Content */}
            <div className="flex-1 space-y-6 px-6 py-6">
              {/* Ingredients Checklist */}
              <div>
                <div className="flex items-center justify-between">
                  <h3 className="font-serif text-base font-semibold text-[#1A1A1A]">
                    Ingredienti (a crudo e netti)
                  </h3>
                  <span className="text-[11px] text-stone-400">
                    Spunta per preparare
                  </span>
                </div>

                <ul className="mt-3 divide-y divide-stone-100 rounded-lg border border-[#E7E5E4] bg-[#FAF9F6]">
                  {meal.ingredients.map((ing, idx) => {
                    const isChecked = checkedIngredients[idx];
                    return (
                      <li
                        key={idx}
                        onClick={() => toggleIngredient(idx)}
                        className="flex cursor-pointer items-center justify-between px-3.5 py-2.5 transition-colors hover:bg-stone-100"
                      >
                        <div className="flex items-center gap-3">
                          <div
                            className={`flex h-4 w-4 items-center justify-center rounded border transition-colors ${
                              isChecked
                                ? "border-[#4A6B53] bg-[#4A6B53] text-white"
                                : "border-stone-300 bg-white"
                            }`}
                          >
                            {isChecked && <Check className="h-3 w-3 stroke-[2.5]" />}
                          </div>
                          <span
                            className={`text-xs ${
                              isChecked
                                ? "text-stone-400 line-through"
                                : "text-stone-800"
                            }`}
                          >
                            {ing.name}
                            {ing.notes && (
                              <span className="ml-1 text-[11px] text-stone-500">
                                ({ing.notes})
                              </span>
                            )}
                          </span>
                        </div>
                        <span
                          className={`font-mono text-xs font-semibold ${
                            isChecked ? "text-stone-400" : "text-stone-900"
                          }`}
                        >
                          {ing.qty}
                        </span>
                      </li>
                    );
                  })}
                </ul>
              </div>

              {/* Step-by-Step Cooking Instructions */}
              {meal.recipe_steps && meal.recipe_steps.length > 0 && (
                <div>
                  <h3 className="font-serif text-base font-semibold text-[#1A1A1A]">
                    Preparazione & Cottura
                  </h3>
                  <ol className="mt-3 space-y-3">
                    {meal.recipe_steps.map((step, idx) => (
                      <li key={idx} className="flex gap-3 text-xs leading-relaxed text-stone-700">
                        <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-[#1A1A1A] text-[11px] font-semibold text-white">
                          {idx + 1}
                        </span>
                        <p className="pt-0.5">{step}</p>
                      </li>
                    ))}
                  </ol>
                </div>
              )}

              {/* Nutritionist Clinical Advice Box */}
              <div className="rounded-lg border border-[#4A6B53]/30 bg-[#4A6B53]/5 p-4 text-xs text-stone-700">
                <div className="flex items-center gap-2 text-[#4A6B53]">
                  <Info className="h-4 w-4 shrink-0" />
                  <span className="font-semibold uppercase tracking-wider text-[11px]">
                    Indicazioni Nutrizionista (Dott.ssa Caglioni)
                  </span>
                </div>
                <ul className="mt-2 space-y-1 text-[11px] leading-relaxed text-stone-600">
                  <li>• Tutti i pesi degli alimenti sono intesi <strong>a crudo e al netto degli scarti</strong>.</li>
                  <li>• Condimento massimo autorizzato: <strong>10g olio extravergine d&apos;oliva a crudo</strong> per pasto.</li>
                  <li>• Cuocere la pasta sempre <strong>al dente</strong> e tostare il pane per modulare il carico glicemico.</li>
                  <li>• Idratarsi costantemente: target minimo <strong>2.0 litri d&apos;acqua al giorno</strong>.</li>
                </ul>
              </div>
            </div>

            {/* Footer */}
            <div className="border-t border-[#E7E5E4] bg-[#FAF9F6] px-6 py-4">
              <button
                onClick={onClose}
                className="w-full rounded-md border border-[#E7E5E4] bg-white py-2 text-xs font-semibold text-stone-700 transition-colors hover:bg-stone-50"
              >
                Chiudi Ricetta
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
