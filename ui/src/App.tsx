import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  createRootRoute,
  createRoute,
  createRouter,
  Outlet,
  RouterProvider,
} from "@tanstack/react-router";

import { HomePage } from "./pages/HomePage";

import enLang from "./locales/en.json";
import fiLang from "./locales/fi.json";
import svLang from "./locales/sv.json";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MetaData, MetaProvider } from "./lib/metadata";

const RootLayoutComponent = () => (
  <div className="max-w-5xl mx-auto p-6">
    <Outlet />
  </div>
);

const rootRoute = createRootRoute({
  component: RootLayoutComponent,
});

const homeRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/",
  component: HomePage,
});

const routeTree = rootRoute.addChildren([homeRoute]);

interface Props {
  data: {};
  meta: MetaData;
}

export const PRODUCT_SHORTNAME = "matrix";

export default ({ data, meta }: Props) => {
  const [ready, setReady] = useState(false);
  const { t, i18n } = useTranslation(PRODUCT_SHORTNAME);

  const router = createRouter({ routeTree, basepath: "/product/matrix" });

  useEffect(() => {
    console.log("Registering");

    async function load() {
      i18n.addResourceBundle("en", PRODUCT_SHORTNAME, enLang);
      i18n.addResourceBundle("fi", PRODUCT_SHORTNAME, fiLang);
      i18n.addResourceBundle("sv", PRODUCT_SHORTNAME, svLang);

      await i18n.loadNamespaces(PRODUCT_SHORTNAME);
      setReady(true);
    }

    load();
  }, [i18n]);

  if (!ready) return null;
  const queryClient = new QueryClient();

  return (
    <MetaProvider meta={meta}>
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
      </QueryClientProvider>
    </MetaProvider>
  );
};
