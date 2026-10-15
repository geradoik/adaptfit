// Small form pieces shared by the onboarding and check-in screens matches figma.

export function Banner({ kind = "info", children }) {
  return (
    <p className={`banner ${kind}`} role={kind === "error" ? "alert" : undefined}>
      {children}
    </p>
  );
}

export function Field({ label, suffix, children }) {
  return (
    <label className="field">
      <span className="caption">{label}</span>
      <span className="field-row">
        {children}
        {suffix && <span className="suffix">{suffix}</span>}
      </span>
    </label>
  );
}

export function NumberField({ label, suffix, value, onChange, step = "any" }) {
  return (
    <Field label={label} suffix={suffix}>
      <input type="number" inputMode="decimal" step={step} value={value} onChange={(e) => onChange(e.target.value)} />
    </Field>
  );
}

export function TimeField({ label, value, onChange }) {
  return (
    <Field label={label}>
      <input type="time" value={value} onChange={(e) => onChange(e.target.value)} />
    </Field>
  );
}

// Option chips. With multiple, value is an array; otherwise a single string. Tapping a selected single chip clears it.
export function Chips({ options, value, onChange, multiple = false }) {
  const isOn = (v) => (multiple ? value.includes(v) : value === v);
  const tap = (v) => {
    if (multiple) onChange(value.includes(v) ? value.filter((x) => x !== v) : [...value, v]);
    else onChange(value === v ? "" : v);
  };
  return (
    <div className="chips">
      {options.map((o) => (
        <button key={o.value} type="button" className={isOn(o.value) ? "chip selected" : "chip"}
          aria-pressed={isOn(o.value)} onClick={() => tap(o.value)}>
          {o.label}
        </button>
      ))}
    </div>
  );
}

// Full-width rows where exactly one can be selected (the "Main goal" question).
export function OptionRows({ options, value, onChange }) {
  return (
    <div className="option-rows">
      {options.map((o) => (
        <button key={o.value} type="button" className={value === o.value ? "option-row selected" : "option-row"}
          aria-pressed={value === o.value} onClick={() => onChange(o.value)}>
          {o.label}
        </button>
      ))}
    </div>
  );
}
