import { createContext, useContext, ReactNode, useMemo } from "react";

export interface MetaData {
  theme: string;
  callsign: string;
}

const MetaContext = createContext<MetaData | undefined>(undefined);

export const MetaProvider = ({
  children,
  meta,
}: {
  children: ReactNode;
  meta: MetaData;
}) => {
  const value = useMemo(() => meta, [meta]);

  return <MetaContext.Provider value={value}>{children}</MetaContext.Provider>;
};

// eslint-disable-next-line react-refresh/only-export-components
export const useMeta = () => {
  const context = useContext(MetaContext);
  if (context === undefined) {
    throw new Error("useMeta must be used within a MetaProvider");
  }
  return context;
};
