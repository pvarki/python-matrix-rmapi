import { useTranslation } from "react-i18next";
import { PRODUCT_SHORTNAME } from "@/App";
import { OnboardingGuide } from "@/components/OnboardingGuide";
import { Toaster } from "@/components/ui/sonner";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Copy } from "lucide-react";
import { copyToClipboard } from "@/lib/clipboard";

export const HomePage = () => {
  const { t } = useTranslation(PRODUCT_SHORTNAME);

  const currentHost = window.location.host.replace(/^mtls\./, "");
  const synapseDomain = `https://synapse.${currentHost}`;

  return (
    <div className="flex justify-center">
      <div className="w-full max-w-xl space-y-6">
        <div className="text-left space-y-4">
          <div className="space-y-2">
            <Label className="font-bold text-xl">{t("homepage.label")}</Label>
            <p className="text-sm text-muted-foreground">
              {t("homepage.description")}
            </p>

            <div className="flex flex-col md:flex-row gap-2 mt-2">
              <Input
                readOnly
                value={synapseDomain}
                className="font-mono bg-secondary/30"
              />
              <Button
                className="cursor-pointer shrink-0"
                onClick={() =>
                  copyToClipboard(synapseDomain, t("common.copied"))
                }
              >
                <p>{t("homepage.copyButton")}</p>
                <Copy className="ml-2 size-4" />
              </Button>
            </div>
          </div>
        </div>

        <Toaster position="top-center" />
        <OnboardingGuide />
      </div>
    </div>
  );
};
