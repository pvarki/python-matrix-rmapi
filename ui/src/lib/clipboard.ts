import { toast } from "sonner";

export const copyToClipboard = (value: string, success_string: string) => {
  navigator.clipboard.writeText(value);
  toast.success(success_string);
};
