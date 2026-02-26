import { PRODUCT_SHORTNAME } from "@/App";
import { useTranslation } from "react-i18next";
import { Button } from "./ui/button";

export function ElementDownload() {
  const { t } = useTranslation(PRODUCT_SHORTNAME);

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
