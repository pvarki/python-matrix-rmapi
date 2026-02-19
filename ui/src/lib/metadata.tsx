import { createContext, useContext, ReactNode, useMemo } from "react";

export interface MetaData {
  theme: string;
  callsign: string;
}

const MetaContext = createContext<MetaData | undefined>(
  undefined,
) as React.Context<MetaData | undefined>;

export const MetaProvider = ({
  children,
  meta,
}: {
  children: ReactNode;
  meta: MetaData;
}) => {
  const value = useMemo(() => meta, [meta.theme, meta.callsign]);

  return (
    <MetaContext.Provider value={value as MetaData}>
      {children}
    </MetaContext.Provider>
  );
};

export const useMeta = () => {
  const context = useContext(MetaContext);
  if (context === undefined) {
    throw new Error("useMeta must be used within a MetaProvider");
  }
  return context;
};
