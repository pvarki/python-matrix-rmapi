import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./i18n";

import {
  Outlet,
  RouterProvider,
  createRouter,
  createRootRoute,
  createRoute,
  redirect,
} from "@tanstack/react-router";

const rootRoute = createRootRoute({
  component: () => (
    <>
      <Outlet />
    </>
  ),
});

const mtxRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "product/matrix/$",
  component: () => (
    <App data={{}} meta={{ theme: "default", callsign: "DEV" }} />
  ),
});

const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/",
  beforeLoad: () => {
    // eslint-disable-next-line @typescript-eslint/only-throw-error
    throw redirect({
      // @ts-expect-error -- route not registered in this local router
      to: "/product/matrix",
    });
  },
  component: () => <h1>Redirecting...</h1>,
});

const routeTree = rootRoute.addChildren([mtxRoute, indexRoute]);

const router = createRouter({ routeTree });

declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}

if (__USE_GLOBAL_CSS__ == true) {
  void import("./index.css");
}

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <RouterProvider router={router} />
  </React.StrictMode>,
);
