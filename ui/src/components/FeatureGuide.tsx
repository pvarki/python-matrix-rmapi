import { useState } from "react";
import { Drawer, DrawerContent } from "@/components/ui/drawer";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight, ImageOff } from "lucide-react";
import { useIsMobile } from "@/hooks/use-mobile";
import { cn } from "@/lib/utils";
import { useTranslation } from "react-i18next";
import { PRODUCT_SHORTNAME } from "@/App";

export interface FeatureStep {
  id: string;
  title: string; // i18n key
  description: string; // i18n key
  image?: string;
}

interface FeatureGuideProps {
  open: boolean;
  onClose: () => void;
  title: string;
  steps: FeatureStep[];
}

export function FeatureGuide({
  open,
  onClose,
  title,
  steps,
}: FeatureGuideProps) {
  const { t } = useTranslation(PRODUCT_SHORTNAME);
  const isMobile = useIsMobile();

  const [currentStep, setCurrentStep] = useState(0);
  const [imageError, setImageError] = useState(false);
  const [imageLoading, setImageLoading] = useState(true);
  const [imageEnlarged, setImageEnlarged] = useState(false);

  const step = steps[currentStep];
  if (!step) return null;

  const progress = ((currentStep + 1) / steps.length) * 100;

  const handlePrev = () => {
    setImageError(false);
    setImageLoading(true);
    setImageEnlarged(false);
    setCurrentStep((c) => Math.max(0, c - 1));
  };

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setImageError(false);
      setImageLoading(true);
      setImageEnlarged(false);
      setCurrentStep((c) => c + 1);
    } else {
      onClose();
      setCurrentStep(0);
    }
  };

  const handleOpenChange = (newOpen: boolean) => {
    if (!newOpen) {
      onClose();
      setCurrentStep(0);
    }
  };

  const content = (
    <div
      className="flex flex-col h-full max-h-[85vh] w-full overflow-hidden"
      data-testid="feature-guide-content"
    >
      <div className="flex-1 overflow-y-auto min-h-0 p-4 md:p-6 space-y-4">
        <div className="space-y-1">
          <h2 className="text-xl font-bold leading-tight">{title}</h2>
          <p
            className="text-xs text-muted-foreground uppercase tracking-wider font-semibold"
            data-testid="feature-guide-step-indicator"
          >
            {t("onboarding.step")} {currentStep + 1} / {steps.length}
          </p>
        </div>

        {step.image && (
          <div
            className={cn(
              "relative rounded-xl overflow-hidden aspect-video w-full border border-border shadow-sm bg-muted/20 shrink-0",
              !imageError && !imageLoading && "cursor-pointer group",
            )}
            onClick={() =>
              !imageError && !imageLoading && setImageEnlarged(true)
            }
            tabIndex={-1}
          >
            {imageLoading && !imageError && (
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="w-8 h-8 border-2 border-primary-light border-t-transparent rounded-full animate-spin" />
              </div>
            )}
            {imageError ? (
              <div className="absolute inset-0 flex flex-col items-center justify-center text-muted-foreground gap-2">
                <ImageOff className="w-8 h-8" />
                <span className="text-xs">{t("onboarding.imageMissing")}</span>
              </div>
            ) : (
              <img
                src={step.image}
                alt={t(step.title)}
                className={cn(
                  "w-full h-full object-contain transition-opacity duration-300",
                  imageLoading ? "opacity-0" : "opacity-100",
                )}
                onLoad={() => setImageLoading(false)}
                onError={() => {
                  setImageError(true);
                  setImageLoading(false);
                }}
              />
            )}
          </div>
        )}

        <div className="space-y-2">
          <h3 className="font-semibold">{t(step.title)}</h3>
          <p className="text-sm text-muted-foreground leading-relaxed">
            {t(step.description)}
          </p>
        </div>
      </div>

      <div className="p-4 border-t bg-background flex gap-3 shrink-0">
        <Button
          variant="outline"
          onClick={handlePrev}
          disabled={currentStep === 0}
          className="flex-1"
          data-testid="feature-guide-back"
        >
          <ChevronLeft className="w-4 h-4 mr-2" />
          {t("onboarding.back")}
        </Button>
        <Button
          onClick={handleNext}
          className="flex-1 bg-primary-light hover:bg-primary-light/90 text-white"
          data-testid="feature-guide-next"
        >
          {currentStep === steps.length - 1
            ? t("onboarding.finish")
            : t("onboarding.next")}
          <ChevronRight className="w-4 h-4 ml-2" />
        </Button>
      </div>

      <div className="h-1.5 w-full bg-muted shrink-0">
        <div
          className="h-full bg-primary-light transition-all duration-500 ease-out"
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );

  if (isMobile === undefined) return null;

  const enlargedImageModal = (
    <Dialog open={imageEnlarged} onOpenChange={setImageEnlarged}>
      <DialogContent
        className="max-w-none! w-[95vw]! h-[95vh]! p-0 bg-black/95 border-none shadow-none flex items-center justify-center"
        onClick={() => setImageEnlarged(false)}
        onOpenAutoFocus={(e) => e.preventDefault()}
      >
        <DialogTitle className="sr-only">{t(step.title)}</DialogTitle>
        <DialogDescription className="sr-only" />
        <img
          src={step.image}
          alt={t(step.title)}
          className="w-auto h-auto max-w-[90vw] max-h-[90vh] object-contain rounded-lg shadow-2xl"
        />
      </DialogContent>
    </Dialog>
  );

  return isMobile ? (
    <>
      {enlargedImageModal}
      <Drawer open={open} onOpenChange={handleOpenChange}>
        <DrawerContent data-testid="feature-guide-dialog">
          {content}
        </DrawerContent>
      </Drawer>
    </>
  ) : (
    <>
      {enlargedImageModal}
      <Dialog open={open} onOpenChange={handleOpenChange}>
        <DialogContent
          className="max-w-2xl max-h-[90vh] p-0 flex flex-col overflow-hidden outline-none"
          data-testid="feature-guide-dialog"
        >
          <DialogTitle className="sr-only">{title}</DialogTitle>
          {content}
        </DialogContent>
      </Dialog>
    </>
  );
}
