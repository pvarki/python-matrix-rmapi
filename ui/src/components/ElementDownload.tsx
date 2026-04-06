import { PRODUCT_SHORTNAME } from "@/App";
import { useTranslation } from "react-i18next";
import { Button } from "./ui/button";
import { Platform } from "@/lib/detectPlatform";

interface Props {
  platform: Platform;
}

export function ElementDownload({ platform }: Props) {
  const { t } = useTranslation(PRODUCT_SHORTNAME);

  if (platform === Platform.Android) {
    return (
      <div className="flex flex-wrap gap-3 mt-4">
        <Button asChild>
          <a
            href="https://play.google.com/store/apps/details?id=im.vector.app"
            target="_blank"
            rel="noopener noreferrer"
          >
            {t("onboarding.downloads.google_play")}
          </a>
        </Button>
      </div>
    );
  }

  if (platform === Platform.iOS) {
    return (
      <div className="flex flex-wrap gap-3 mt-4">
        <Button asChild>
          <a
            href="https://apps.apple.com/app/element-messenger/id1083446067"
            target="_blank"
            rel="noopener noreferrer"
          >
            {t("onboarding.downloads.app_store")}
          </a>
        </Button>
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
