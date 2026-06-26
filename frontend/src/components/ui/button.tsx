import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 rounded text-sm font-medium transition-colors duration-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default:
          "bg-brand-600 text-white hover:bg-brand-700 active:bg-brand-800 focus-visible:outline-brand-600",
        secondary:
          "border border-surface-300 bg-white text-surface-700 hover:bg-surface-50 active:bg-surface-100",
        destructive:
          "bg-red-600 text-white hover:bg-red-700 active:bg-red-800 focus-visible:outline-red-600",
        ghost:
          "text-surface-600 hover:bg-surface-100 active:bg-surface-200",
        outline:
          "border border-surface-300 bg-transparent text-surface-700 hover:bg-surface-50",
        link: "text-brand-600 underline-offset-4 hover:underline p-0 h-auto",
      },
      size: {
        default: "px-4 py-2",
        sm: "px-3 py-1.5 text-xs",
        lg: "px-6 py-3 text-base",
        icon: "h-9 w-9",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";

export { Button, buttonVariants };
