"use client";

import React, { useState, useEffect } from "react";
import { X, ExternalLink, Check, ShoppingCart, ShieldCheck } from "lucide-react";
import { CartSummary } from "@/types/meal-plan";

interface CartModalProps {
  cartSummary: CartSummary;
  isOpen: boolean;
  onClose: () => void;
}

export function CartModal({ cartSummary, isOpen, onClose }: CartModalProps) {
  const [checkedItems, setCheckedItems] = useState<Record<string, boolean>>({});

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };
    if (isOpen) {
      window.addEventListener("keydown", handleKeyDown);
    }
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const toggleItem = (key: string) => {
    setCheckedItems((prev) => ({
      ...prev,
      [key]: !prev[key],
    }));
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-stone-900/40 backdrop-blur-xs transition-opacity"
        onClick={onClose}
      />

      <div className="fixed inset-y-0 right-0 flex max-w-full pl-6 sm:pl-10">
        <div className="w-screen max-w-2xl bg-white shadow-xl">
          <div className="flex h-full flex-col overflow-y-auto">
            {/* Header */}
            <div className="border-b border-[#E7E5E4] px-6 py-5">
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold uppercase tracking-wider text-[#C25E3F]">
                      Spesa Settimanale
                    </span>
                    <span className="text-xs text-stone-300">•</span>
                    <span className="text-xs text-stone-500">{cartSummary.store} a Casa</span>
                  </div>
                  <h2 className="mt-1 font-serif text-2xl font-semibold text-[#1A1A1A]">
                    Riepilogo Carrello
                  </h2>
                  <p className="mt-1 text-xs text-stone-500">
                    Ingredienti aggregati per il fabbisogno settimanale (31/10 – 06/11/2026)
                  </p>
                </div>
                <button
                  onClick={onClose}
                  className="rounded-md p-1.5 text-stone-400 hover:bg-stone-100 hover:text-stone-700"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              {/* Spend & Count Badge */}
              <div className="mt-4 flex flex-wrap items-center justify-between gap-3 rounded-lg border border-[#E7E5E4] bg-[#FAF9F6] p-4">
                <div>
                  <span className="text-xs text-stone-500">Totale stimato carrello</span>
                  <div className="flex items-baseline gap-2">
                    <span className="font-serif text-2xl font-semibold text-[#1A1A1A]">
                      {cartSummary.total_estimated_eur.toFixed(2)} €
                    </span>
                    <span className="text-xs text-stone-500">
                      ({cartSummary.items_count} prodotti inclusi)
                    </span>
                  </div>
                </div>

                <a
                  href={cartSummary.cart_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 rounded-md bg-[#1A1A1A] px-4 py-2 text-xs font-semibold text-white transition-colors hover:bg-stone-800"
                >
                  <ShoppingCart className="h-4 w-4 text-[#C25E3F]" />
                  <span>Apri su Esselunga</span>
                  <ExternalLink className="h-3.5 w-3.5 opacity-70" />
                </a>
              </div>
            </div>

            {/* Safety Invariant Notice */}
            <div className="border-b border-[#E7E5E4] bg-stone-50 px-6 py-3">
              <div className="flex items-center gap-2 text-stone-700">
                <ShieldCheck className="h-4 w-4 text-[#4A6B53] shrink-0" />
                <span className="text-[11px] leading-relaxed text-stone-600">
                  <strong>Guardrail di sicurezza</strong>: Lo script automatizzato aggiunge esclusivamente i prodotti al carrello sul tuo browser. Nessun ordine o pagamento viene mai confermato senza la tua approvazione manuale.
                </span>
              </div>
            </div>

            {/* Body: Grouped Items */}
            <div className="flex-1 space-y-6 px-6 py-6">
              {cartSummary.grouped_items?.map((group, groupIdx) => (
                <div key={groupIdx}>
                  <h3 className="border-b border-stone-200 pb-1.5 font-serif text-sm font-semibold text-[#1A1A1A]">
                    {group.category} ({group.items.length})
                  </h3>
                  <ul className="mt-2 divide-y divide-stone-100 rounded-lg border border-[#E7E5E4] bg-[#FAF9F6]">
                    {group.items.map((item, itemIdx) => {
                      const itemKey = `${groupIdx}-${itemIdx}`;
                      const isChecked = checkedItems[itemKey];

                      return (
                        <li
                          key={itemIdx}
                          onClick={() => toggleItem(itemKey)}
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
                              {item.name}
                            </span>
                          </div>

                          <div className="flex items-center gap-3">
                            <span className="text-[11px] font-medium text-stone-500">
                              {item.qty}
                            </span>
                            {item.estimated_eur && (
                              <span className="font-mono text-xs font-semibold text-stone-900">
                                {item.estimated_eur.toFixed(2)} €
                              </span>
                            )}
                          </div>
                        </li>
                      );
                    })}
                  </ul>
                </div>
              ))}
            </div>

            {/* Footer */}
            <div className="border-t border-[#E7E5E4] bg-[#FAF9F6] px-6 py-4">
              <div className="flex gap-3">
                <button
                  onClick={onClose}
                  className="flex-1 rounded-md border border-[#E7E5E4] bg-white py-2 text-xs font-semibold text-stone-700 transition-colors hover:bg-stone-50"
                >
                  Chiudi Lista
                </button>
                <a
                  href={cartSummary.cart_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex flex-1 items-center justify-center gap-2 rounded-md bg-[#1A1A1A] py-2 text-xs font-semibold text-white transition-colors hover:bg-stone-800"
                >
                  <span>Vai al Carrello</span>
                  <ExternalLink className="h-3.5 w-3.5" />
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
