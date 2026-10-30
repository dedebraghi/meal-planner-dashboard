# SPEC: Meal Planner Dashboard & Automazione Spesa Esselunga

## 1. Obiettivo & Confini
- **Goal:** Realizzare un sistema integrato composto da:
  1. Una web dashboard Next.js (App Router, Tailwind CSS, Vercel) dal design editoriale di alto livello (anti-slop, ispirato a NYT Cooking / Linear-clean) che visualizza il menù settimanale personalizzato per Davide, le ricette passo-passo con relative immagini ad alta risoluzione, la lista ingredienti e i macronutrienti per pasto.
  2. Uno script locale in Python/Playwright schedulato ogni venerdì (Windows Task Scheduler) che si collega a Esselunga con il profilo Chrome già attivo, compila il carrello solo per il fabbisogno settimanale di Davide (dieta Caglioni, variando ingredienti e rispettando la stagionalità), invia una notifica Telegram con il riepilogo del carrello tramite il bot Jarvis esistente (`telegram-antigravity-bridge/send_alert.py`), genera il menù settimanale con ricette e foto tramite Gemini API, e aggiorna la dashboard via Git commit/push su Vercel.
- **Non-Goals (Categoricamente Fuori Scopo):**
  - **MAI effettuare il checkout o confermare ordini su Esselunga**: il carrello deve essere esclusivamente riempito e lasciato pronto per la revisione manuale dell'utente.
  - Nessun database cloud a pagamento o complesso (no Supabase/Postgres da gestire): i dati risiedono nel repository in formato JSON versionato (`Git-as-CMS`).
  - Nessuna gestione o allucinazione di acquisti per Ceci nell'automazione del venerdì: la spesa automatizzata calcola solo il fabbisogno settimanale per Davide; Ceci integrerà manualmente o Davide aggiungerà il resto prima del checkout.

---

## 2. File & Moduli Coinvolti
- `C:\Users\david\Desktop\Progetti\meal-planner-dashboard\` (Repository radice)
  - `src/app/page.tsx`: Vista principale della dashboard settimanale (griglia 7 giorni, 5 pasti/die, filtri, ricetta attiva in drawer/sheet).
  - `src/components/MealCard.tsx`: Card pasto con foto ad alta risoluzione, badge nutrizionali e stato di preparazione.
  - `src/components/RecipeModal.tsx`: Visualizzazione passo-passo della ricetta con ingredienti, tempi di cottura e passaggi numerati.
  - `src/data/current-week.json`: Fonte di verità della settimana corrente (lista pasti, ingredienti, porzioni, ricette e path immagini).
  - `scripts/esselunga_cart_filler.py`: Script Playwright locale per navigazione su Esselunga, ricerca prodotti e riempimento carrello.
  - `scripts/weekly_orchestrator.py`: Orchestratore del venerdì (chiama `esselunga_cart_filler.py`, interroga Gemini per ricette e Imagen 3 per foto, aggiorna `current-week.json`, invia alert Telegram ed esegue `git push`).
  - `public/recipes/`: Cartella delle immagini WebP dei piatti generate.

---

## 3. Invarianti & Vincoli Tecnici
- **Stack Dashboard:** Next.js 15+ (App Router), React 19, Tailwind CSS, Lucide Icons, deploy su Vercel.
- **Design Tokens & Aesthetic (Taste Skill):** 
  - Palette editoriale culinaria: sfondo caldo (`#FAF9F6` o `#F7F5F0`), testo ad alto contrasto (`#1A1A1A`), accenti salvia/terracotta discreti.
  - Niente gradienti viola generici, niente glassmorphism finto, niente UI "AI-slop".
  - Tipografia pulita, contrasto AA/AAA conforme a `web-design-guidelines`.
- **Esecuzione Esselunga:** Esclusivamente in locale su Windows, lanciando Chromium con il flag `--user-data-dir` puntato al profilo Chrome esistente, azzerando rischi di WAF/bot blocking.
- **Notifiche Telegram:** Integrazione con lo script `C:\Users\david\Desktop\Progetti\telegram-antigravity-bridge\send_alert.py`.

---

## 4. Contratti di Interfaccia (I/O)

### Schema `current-week.json`
```json
{
  "week_start": "2026-10-31",
  "week_end": "2026-11-06",
  "macro_target": { "kcal": 2063, "proteins_g": 112, "carbs_g": 251, "fats_g": 68 },
  "cart_summary": {
    "total_estimated_eur": 45.20,
    "items_count": 18,
    "cart_url": "https://spesaonline.esselunga.it/commerce/nav/supermercato/carrello"
  },
  "days": [
    {
      "day_name": "Sabato",
      "date": "2026-10-31",
      "meals": {
        "colazione": { "title": "...", "ingredients": [], "kcal": 350 },
        "pranzo": {
          "title": "Involtini primavera con verza e uovo",
          "ingredients": [{ "name": "Fogli di riso", "qty": "50g" }],
          "recipe_steps": ["Passo 1", "Passo 2"],
          "image_url": "/recipes/sabato_pranzo.webp"
        },
        "spuntino_pomeriggio": { "title": "...", "ingredients": [] },
        "cena": { "title": "Pizza margherita", "is_free_meal": true },
        "dopocena": { "title": "...", "ingredients": [] }
      }
    }
  ]
}
```

---

## 5. Casi Limite & Fallimenti (Edge Cases)
- **Sessione Esselunga scaduta:** Lo script rileva la schermata di login; non tenta brute force né memorizza password, ma invia subito alert Telegram *"Sessione Esselunga scaduta: accedi una volta su Chrome e rilancia lo script"*.
- **Prodotto non disponibile o fuori stock:** Lo script effettua fallback automatico su un prodotto equivalente della stessa categoria nutrizionale (es. petto di pollo di altra grammatura o marca, oppure fesa di tacchino).
- **Rete / Fallimento API Immagini:** Se la generazione Imagen fallisce per timeout, viene utilizzato un placeholder fotografico culinario pulito o l'immagine viene rigenerata al run successivo, senza bloccare la build della dashboard.

---

## 6. Il Verificatore (Definition of Done)
1. [ ] **Build pulita**: `npm run build` eseguito nella cartella Next.js con exit code 0 e nessun errore TypeScript o ESLint.
2. [ ] **Verifica Playwright locale**: Lo script `scripts/esselunga_cart_filler.py` apre il carrello con profilo utente, aggiunge almeno 1 articolo di test e non viene bloccato dal WAF.
3. [ ] **Notifica Telegram funzionante**: Ricezione confermata del messaggio di notifica su Telegram con link alla dashboard e riepilogo carrello.
4. [ ] **Deploy Vercel attivo**: Dashboard accessibile pubblicamente su Vercel, responsive sia su desktop che su mobile, conforme ai criteri estetici di `design-taste-frontend`.

---

## 7. Istruzione di Esecuzione per l'Agente
> Scaffolding del progetto Next.js in `C:\Users\david\Desktop\Progetti\meal-planner-dashboard`, implementazione dei componenti UI per il piano pasti 7 giorni con ricette passo-passo e drawer, scrittura degli script di orchestrazione carrello + Telegram in Python, configurazione del task schedulato del venerdì mattina.
