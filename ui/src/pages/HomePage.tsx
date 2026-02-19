import { useTranslation } from "react-i18next";
import { PRODUCT_SHORTNAME } from "@/App";
import { OnboardingGuide } from "@/components/OnboardingGuide";
import { Toaster } from "sonner";

export const HomePage = () => {
  const { t } = useTranslation(PRODUCT_SHORTNAME);
  return (
    <div className="space-y-6">
      <p>Matrix insisode</p>
      <Toaster position="top-center" />
      <OnboardingGuide />
    </div>
  );
};
