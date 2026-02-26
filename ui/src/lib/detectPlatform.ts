export enum Platform {
  Android = "android",
  iOS = "ios",
  Windows = "windows",
  Linux = "linux",
}

export const detectPlatform = (): Platform => {
  if (typeof window === "undefined") return Platform.Android;

  const ua =
    window.navigator.userAgent ||
    window.navigator.vendor ||
    (window as any).opera;

  if (/android/i.test(ua)) return Platform.Android;
  if (/iPad|iPhone|iPod/.test(ua)) return Platform.iOS;
  if (/Windows NT/.test(ua)) return Platform.Windows;
  if (/Linux/.test(ua) && !/android/i.test(ua)) return Platform.Linux;

  //Return most likely platform
  return Platform.Android;
};
