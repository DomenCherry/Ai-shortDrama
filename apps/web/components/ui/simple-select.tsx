"use client";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from "@/components/ui/select";
import { cn } from "@/lib/utils";

const EMPTY_SELECT_VALUE = "__empty__";

export type SimpleSelectOption = {
  label: string;
  value: string;
};

type SimpleSelectProps = {
  value: string;
  options: SimpleSelectOption[];
  onValueChange: (value: string) => void;
  disabled?: boolean;
  placeholder?: string;
  className?: string;
};

export function SimpleSelect({
  value,
  options,
  onValueChange,
  disabled = false,
  placeholder = "请选择",
  className
}: SimpleSelectProps) {
  return (
    <Select disabled={disabled} value={toSelectValue(value)} onValueChange={(nextValue) => onValueChange(fromSelectValue(nextValue))}>
      <SelectTrigger className={cn("w-full", className)}>
        <SelectValue placeholder={placeholder} />
      </SelectTrigger>
      <SelectContent>
        {options.map((option) => (
          <SelectItem key={`${option.value}-${option.label}`} value={toSelectValue(option.value)}>
            {option.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

function toSelectValue(value: string) {
  return value === "" ? EMPTY_SELECT_VALUE : value;
}

function fromSelectValue(value: string) {
  return value === EMPTY_SELECT_VALUE ? "" : value;
}
