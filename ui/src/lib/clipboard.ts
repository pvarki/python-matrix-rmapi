import { toast } from "sonner";

export const copyToClipboard = (value: string, success_string: string) => {
  void navigator.clipboard.writeText(value);
  toast.success(success_string);
};
