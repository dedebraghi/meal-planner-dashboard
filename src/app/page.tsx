import currentWeekJson from "@/data/current-week.json";
import { WeeklyPlanData } from "@/types/meal-plan";
import { DashboardShell } from "@/components/DashboardShell";

export default function Home() {
  const planData = currentWeekJson as unknown as WeeklyPlanData;

  return (
    <main className="min-h-screen bg-[#FAF9F6] pb-16">
      <DashboardShell initialData={planData} />
    </main>
  );
}
