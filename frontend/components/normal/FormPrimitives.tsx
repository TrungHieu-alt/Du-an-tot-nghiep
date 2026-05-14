import React, { useState } from 'react';
import { Check, Plus, Trash2 } from 'lucide-react';

import type { NormalOption } from '../../src/reference/normalEnums';

export interface FormStep {
  title: string;
  subtitle: string;
}

export const cardClass = 'rounded-2xl border border-gray-100 bg-white p-5 shadow-sm';
export const inputClass =
  'w-full rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 outline-none transition focus:border-[#0F6FD6] focus:ring-2 focus:ring-blue-100';

export const Stepper: React.FC<{
  steps: FormStep[];
  currentStep: number;
}> = ({ steps, currentStep }) => (
  <div className="rounded-2xl border border-gray-100 bg-white p-4 shadow-sm">
    <div className="mb-3 flex items-center justify-between text-xs font-semibold uppercase tracking-wide text-gray-500">
      <span>
        Step {currentStep + 1} of {steps.length}
      </span>
      <span>{Math.round(((currentStep + 1) / steps.length) * 100)}%</span>
    </div>
    <div className="mb-4 h-2 overflow-hidden rounded-full bg-gray-100">
      <div
        className="h-full rounded-full bg-[#0F6FD6] transition-all"
        style={{ width: `${((currentStep + 1) / steps.length) * 100}%` }}
      />
    </div>
    <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
      {steps.map((step, index) => {
        const active = index === currentStep;
        const complete = index < currentStep;
        return (
          <div
            key={step.title}
            className={`rounded-xl border px-3 py-2 text-left ${
              active
                ? 'border-blue-200 bg-blue-50 text-[#0F6FD6]'
                : complete
                  ? 'border-green-100 bg-green-50 text-green-700'
                  : 'border-gray-100 bg-gray-50 text-gray-500'
            }`}
          >
            <div className="flex items-center gap-2">
              <span className={`flex h-5 w-5 items-center justify-center rounded-full text-[11px] font-bold ${
                complete ? 'bg-green-600 text-white' : active ? 'bg-[#0F6FD6] text-white' : 'bg-white text-gray-500'
              }`}>
                {complete ? <Check className="h-3 w-3" /> : index + 1}
              </span>
              <span className="truncate text-xs font-bold">{step.title}</span>
            </div>
            <p className="mt-1 line-clamp-2 text-[11px] leading-4 opacity-80">{step.subtitle}</p>
          </div>
        );
      })}
    </div>
  </div>
);

export const Field: React.FC<{
  label: string;
  required?: boolean;
  helper?: string;
  error?: string;
  className?: string;
  children: React.ReactNode;
}> = ({ label, required = false, helper, error, className = '', children }) => (
  <label className={`block ${className}`}>
    <span className="mb-1 block text-sm font-semibold text-gray-800">
      {label}
      {required ? <span className="text-red-500"> *</span> : null}
    </span>
    {children}
    {helper ? <span className="mt-1 block text-xs leading-5 text-gray-500">{helper}</span> : null}
    {error ? <span className="mt-1 block text-xs font-semibold text-red-600">{error}</span> : null}
  </label>
);

export const SelectField: React.FC<{
  label: string;
  value: string;
  options: NormalOption[];
  onChange: (value: string) => void;
  helper?: string;
  required?: boolean;
  error?: string;
}> = ({ label, value, options, onChange, helper, required, error }) => (
  <Field label={label} required={required} helper={helper} error={error}>
    <select value={value} onChange={(event) => onChange(event.target.value)} className={inputClass}>
      {options.map((option) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
  </Field>
);

export const MultiOptionField: React.FC<{
  label: string;
  values: string[];
  options: NormalOption[];
  onChange: (values: string[]) => void;
  helper?: string;
}> = ({ label, values, options, onChange, helper }) => {
  const toggle = (value: string) => {
    const withoutUnknown = values.filter((item) => item !== 'unknown');
    if (value === 'unknown') {
      onChange(['unknown']);
      return;
    }
    if (withoutUnknown.includes(value)) {
      const next = withoutUnknown.filter((item) => item !== value);
      onChange(next.length > 0 ? next : ['unknown']);
      return;
    }
    onChange([...withoutUnknown, value]);
  };

  return (
    <Field label={label} helper={helper}>
      <div className="flex flex-wrap gap-2">
        {options.map((option) => {
          const active = values.includes(option.value);
          return (
            <button
              key={option.value}
              type="button"
              onClick={() => toggle(option.value)}
              className={`rounded-full border px-3 py-1.5 text-xs font-semibold transition ${
                active
                  ? 'border-[#0F6FD6] bg-blue-50 text-[#0F6FD6]'
                  : 'border-gray-200 bg-white text-gray-600 hover:border-blue-200'
              }`}
            >
              {option.label}
            </button>
          );
        })}
      </div>
    </Field>
  );
};

export const StringListEditor: React.FC<{
  label: string;
  values: string[];
  onChange: (values: string[]) => void;
  placeholder?: string;
  helper?: string;
  emptyText?: string;
}> = ({ label, values, onChange, placeholder = 'Add item', helper, emptyText = 'No items added yet.' }) => {
  const [draft, setDraft] = useState('');
  const add = () => {
    const value = draft.trim();
    if (!value) return;
    onChange([...values, value]);
    setDraft('');
  };

  return (
    <Field label={label} helper={helper}>
      <div className="flex gap-2">
        <input
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter') {
              event.preventDefault();
              add();
            }
          }}
          placeholder={placeholder}
          className={inputClass}
        />
        <button
          type="button"
          onClick={add}
          className="inline-flex items-center gap-1 rounded-xl border border-blue-200 bg-blue-50 px-3 py-2 text-sm font-semibold text-[#0F6FD6]"
        >
          <Plus className="h-4 w-4" />
          Add
        </button>
      </div>
      {values.length === 0 ? (
        <p className="mt-2 rounded-xl border border-dashed border-gray-200 bg-gray-50 px-3 py-2 text-xs text-gray-500">
          {emptyText}
        </p>
      ) : (
        <div className="mt-2 flex flex-wrap gap-2">
          {values.map((value, index) => (
            <span key={`${value}-${index}`} className="inline-flex items-center gap-2 rounded-full bg-gray-100 px-3 py-1 text-xs font-semibold text-gray-700">
              {value}
              <button
                type="button"
                aria-label={`Remove ${value}`}
                onClick={() => onChange(values.filter((_, itemIndex) => itemIndex !== index))}
                className="rounded-full text-gray-400 hover:text-red-600"
              >
                <Trash2 className="h-3 w-3" />
              </button>
            </span>
          ))}
        </div>
      )}
    </Field>
  );
};

export const EmptyState: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div className="rounded-xl border border-dashed border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-500">
    {children}
  </div>
);

export const WizardActions: React.FC<{
  currentStep: number;
  totalSteps: number;
  saving: boolean;
  nextDisabled?: boolean;
  onBack: () => void;
  onNext: () => void;
  onSaveDraft: () => void;
  onPublish: () => void;
}> = ({ currentStep, totalSteps, saving, nextDisabled = false, onBack, onNext, onSaveDraft, onPublish }) => (
  <div className="sticky bottom-3 z-10 mt-6 rounded-2xl border border-gray-100 bg-white/95 p-3 shadow-lg backdrop-blur">
    <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
      <button
        type="button"
        onClick={onBack}
        disabled={currentStep === 0 || saving}
        className="rounded-xl border border-gray-200 bg-white px-4 py-2 text-sm font-semibold text-gray-700 disabled:cursor-not-allowed disabled:opacity-50"
      >
        Back
      </button>
      <div className="flex flex-col gap-2 sm:flex-row">
        <button
          type="button"
          onClick={onSaveDraft}
          disabled={saving}
          className="rounded-xl border border-blue-200 bg-blue-50 px-4 py-2 text-sm font-semibold text-[#0F6FD6] disabled:opacity-60"
        >
          Save draft
        </button>
        {currentStep < totalSteps - 1 ? (
          <button
            type="button"
            onClick={onNext}
            disabled={saving || nextDisabled}
            className="rounded-xl bg-[#0F6FD6] px-5 py-2 text-sm font-semibold text-white disabled:opacity-60"
          >
            Next
          </button>
        ) : (
          <button
            type="button"
            onClick={onPublish}
            disabled={saving}
            className="rounded-xl bg-[#0F6FD6] px-5 py-2 text-sm font-semibold text-white disabled:opacity-60"
          >
            Publish / Save
          </button>
        )}
      </div>
    </div>
  </div>
);
