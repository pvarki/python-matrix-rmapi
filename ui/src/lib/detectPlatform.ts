export enum Platform {
  Android = "android",
  iOS = "ios",
  Windows = "windows",
  Linux = "linux",
  macOS = "macos",
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
  if (/Macintosh|Mac OS X/.test(ua)) return Platform.macOS;
  if (/Linux/.test(ua) && !/android/i.test(ua)) return Platform.Linux;

  return Platform.Android;
};
