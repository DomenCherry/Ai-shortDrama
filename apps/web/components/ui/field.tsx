import * as React from "react";

import { cn } from "@/lib/utils";

type FieldProps = {
  label: string;
  hint?: React.ReactNode;
  className?: string;
  children: React.ReactElement<{
    id?: string;
    "aria-describedby"?: string;
    "aria-labelledby"?: string;
  }>;
};

function Field({ label, hint, className, children }: FieldProps) {
  const generatedId = React.useId();
  const controlId = children.props.id || `${generatedId}-control`;
  const labelId = `${controlId}-label`;
  const hintId = hint ? `${controlId}-hint` : undefined;

  return (
    <div className={cn("field", className)}>
      <label id={labelId} htmlFor={controlId}>
        {label}
      </label>
      {React.cloneElement(children, {
        id: controlId,
        "aria-describedby": hintId,
        "aria-labelledby": labelId,
      })}
      {hint ? (
        <span className="field-hint" id={hintId}>
          {hint}
        </span>
      ) : null}
    </div>
  );
}

export { Field };
