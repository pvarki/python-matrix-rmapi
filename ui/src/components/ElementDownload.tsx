import { PRODUCT_SHORTNAME } from "@/App";
import { useTranslation } from "react-i18next";
import { Button } from "./ui/button";
import { Platform } from "@/lib/detectPlatform";

interface Props {
  platform: Platform;
}

type BadgeLang = "en" | "fi" | "sv";

const badgeLang = (language: string): BadgeLang => {
  const lang = language.toLowerCase().split("-")[0];
  if (lang === "fi") return "fi";
  if (lang === "sv") return "sv";
  return "en";
};

export function ElementDownload({ platform }: Props) {
  const { t, i18n } = useTranslation(PRODUCT_SHORTNAME);
  const lang = badgeLang(i18n.resolvedLanguage ?? i18n.language);

  if (platform === Platform.Android) {
    return (
      <div className="flex flex-wrap gap-3 mt-4">
        <a
          href="https://play.google.com/store/apps/details?id=io.element.android.x"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-block"
        >
          <img
            src={`/ui/matrix/download-buttons/${lang}-googleplay.svg`}
            alt={t("onboarding.downloads.google_play")}
            className="h-12 w-auto"
          />
        </a>
      </div>
    );
  }

  if (platform === Platform.iOS) {
    return (
      <div className="flex flex-wrap gap-3 mt-4">
        <a
          href="https://apps.apple.com/us/app/element-x-secure-chat-call/id1631335820"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-block p-3"
        >
          <img
            src={`/ui/matrix/download-buttons/${lang}-apple.svg`}
            alt={t("onboarding.downloads.app_store")}
            className="h-12 w-auto"
          />
        </a>
      </div>
    );
  }

  // Windows, Linux, macOS
  return (
    <div className="flex flex-wrap gap-3 mt-4">
      <Button asChild>
        <a
          href="https://element.io/download"
          target="_blank"
          rel="noopener noreferrer"
        >
          {t("onboarding.downloads.open_website")}
        </a>
      </Button>
    </div>
  );
}
