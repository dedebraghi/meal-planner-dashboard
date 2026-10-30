export interface MacroTarget {
  kcal: number;
  carbs_g: number;
  proteins_g: number;
  fats_g: number;
  fiber_g: number;
}

export interface Ingredient {
  name: string;
  qty: string;
  category?: "carne" | "pesce" | "latticini" | "frutta_verdura" | "dispensa" | "condimenti" | string;
  notes?: string;
}

export interface MealMacros {
  carbs_g: number;
  proteins_g: number;
  fats_g: number;
}

export interface Meal {
  id: string;
  meal_type: "colazione" | "pranzo" | "spuntino_pomeriggio" | "cena" | "dopocena";
  title: string;
  subtitle?: string;
  category: string;
  kcal: number;
  macros: MealMacros;
  ingredients: Ingredient[];
  recipe_steps?: string[];
  prep_time_min?: number;
  cook_time_min?: number;
  image_url?: string;
  is_free_meal?: boolean;
  notes?: string;
}

export type DayName = "Sabato" | "Domenica" | "Lunedì" | "Martedì" | "Mercoledì" | "Giovedì" | "Venerdì";

export interface DayPlan {
  id: string;
  day_name: DayName;
  date: string;
  daily_macros: {
    kcal: number;
    carbs_g: number;
    proteins_g: number;
    fats_g: number;
  };
  meals: {
    colazione: Meal;
    pranzo: Meal;
    spuntino_pomeriggio: Meal;
    cena: Meal;
    dopocena: Meal;
  };
}

export interface CartItem {
  name: string;
  qty: string;
  estimated_eur?: number;
}

export interface CartGroupedItem {
  category: string;
  items: CartItem[];
}

export interface CartSummary {
  total_estimated_eur: number;
  items_count: number;
  cart_url: string;
  last_updated: string;
  store: "Esselunga";
  grouped_items?: CartGroupedItem[];
}

export interface WeeklyPlanData {
  week_id: string;
  week_start: string;
  week_end: string;
  macro_target: MacroTarget;
  cart_summary: CartSummary;
  days: DayPlan[];
}
