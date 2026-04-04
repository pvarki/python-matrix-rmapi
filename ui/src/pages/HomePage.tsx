import { useState } from "react";
import { useTranslation } from "react-i18next";
import { PRODUCT_SHORTNAME } from "@/App";
import { Toaster } from "@/components/ui/sonner";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Copy, MessageSquare, Users } from "lucide-react";
import { copyToClipboard } from "@/lib/clipboard";
import { OnboardingHandler } from "@/components/OnboardingGuide";
import { FeatureGuide, FeatureStep } from "@/components/FeatureGuide";

const MESSAGING_STEPS: FeatureStep[] = [
  {
    id: "messaging-intro",
    title: "featureguides.messaging.steps.intro.title",
    description: "featureguides.messaging.steps.intro.description",
    image: "/ui/matrix/assets/matrix-intro.webp",
  },
  {
    id: "messaging-space",
    title: "featureguides.messaging.steps.space.title",
    description: "featureguides.messaging.steps.space.description",
    image: "/ui/matrix/assets/features/messaging/messaging-2.png",
  },
  {
    id: "messaging-rooms",
    title: "featureguides.messaging.steps.rooms.title",
    description: "featureguides.messaging.steps.rooms.description",
    image: "/ui/matrix/assets/features/messaging/messaging-3.png",
  },
  {
    id: "messaging-calls",
    title: "featureguides.messaging.steps.calls.title",
    description: "featureguides.messaging.steps.calls.description",
    image: "/ui/matrix/assets/features/messaging/messaging-4.png",
  },
  {
    id: "messaging-meetings",
    title: "featureguides.messaging.steps.meetings.title",
    description: "featureguides.messaging.steps.meetings.description",
    image: "/ui/matrix/assets/features/messaging/messaging-5.png",
  },
];

const UNIT_STEPS: FeatureStep[] = [
  {
    id: "unit-setup",
    title: "featureguides.unit.steps.setup.title",
    description: "featureguides.unit.steps.setup.description",
    image: "/ui/matrix/assets/matrix-intro.webp",
  },
  {
    id: "unit-rooms",
    title: "featureguides.unit.steps.rooms.title",
    description: "featureguides.unit.steps.rooms.description",
    image: "/ui/matrix/assets/features/unit/unit-1.png",
  },
  {
    id: "unit-command",
    title: "featureguides.unit.steps.command.title",
    description: "featureguides.unit.steps.command.description",
    image: "/ui/matrix/assets/features/unit/unit-1.png",
  },
  {
    id: "unit-friendly",
    title: "featureguides.unit.steps.friendly.title",
    description: "featureguides.unit.steps.friendly.description",
    image: "/ui/matrix/assets/features/unit/unit-2.png",
  },
  {
    id: "unit-recon",
    title: "featureguides.unit.steps.recon.title",
    description: "featureguides.unit.steps.recon.description",
    image: "/ui/matrix/assets/features/unit/unit-3.png",
  },
  {
    id: "unit-guard",
    title: "featureguides.unit.steps.guard.title",
    description: "featureguides.unit.steps.guard.description",
    image: "/ui/matrix/assets/features/unit/unit-4.png",
  },
  {
    id: "unit-others",
    title: "featureguides.unit.steps.others.title",
    description: "featureguides.unit.steps.others.description",
    image: "/ui/matrix/assets/features/unit/unit-5.png",
  },
  {
    id: "unit-users",
    title: "featureguides.unit.steps.users.title",
    description: "featureguides.unit.steps.users.description",
    image: "/ui/matrix/assets/features/unit/unit-6.png",
  },
  {
    id: "unit-federation",
    title: "featureguides.unit.steps.federation.title",
    description: "featureguides.unit.steps.federation.description",
    image: "/ui/matrix/assets/matrix-intro.webp",
  },
];

export const HomePage = () => {
  const { t } = useTranslation(PRODUCT_SHORTNAME);
  const [activeGuide, setActiveGuide] = useState<"messaging" | "unit" | null>(
    null,
  );

  const currentHost = window.location.host.replace(/^mtls\./, "");
  const synapseDomain = `https://synapse.${currentHost}`;

  return (
    <div className="flex justify-center">
      <div className="w-full max-w-xl space-y-6">
        {/* Homeserver URL — big action at the top */}
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
              onClick={() => copyToClipboard(synapseDomain, t("common.copied"))}
            >
              <p>{t("homepage.copyButton")}</p>
              <Copy className="ml-2 size-4" />
            </Button>
          </div>
        </div>

        {/* Feature guides */}
        <div className="space-y-3">
          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            {t("featureguides.title")}
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <button
              onClick={() => setActiveGuide("messaging")}
              className="flex items-start gap-3 rounded-lg border border-border bg-card p-4 text-left shadow-sm transition-colors hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <MessageSquare className="mt-0.5 size-5 shrink-0 text-primary" />
              <span className="text-sm font-medium leading-snug">
                {t("featureguides.messaging.button")}
              </span>
            </button>
            <button
              onClick={() => setActiveGuide("unit")}
              className="flex items-start gap-3 rounded-lg border border-border bg-card p-4 text-left shadow-sm transition-colors hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <Users className="mt-0.5 size-5 shrink-0 text-primary" />
              <span className="text-sm font-medium leading-snug">
                {t("featureguides.unit.button")}
              </span>
            </button>
          </div>
        </div>

        <Toaster position="top-center" />

        <FeatureGuide
          open={activeGuide === "messaging"}
          onClose={() => setActiveGuide(null)}
          title={t("featureguides.messaging.title")}
          steps={MESSAGING_STEPS}
        />
        <FeatureGuide
          open={activeGuide === "unit"}
          onClose={() => setActiveGuide(null)}
          title={t("featureguides.unit.title")}
          steps={UNIT_STEPS}
        />

        <OnboardingHandler />
      </div>
    </div>
  );
};
