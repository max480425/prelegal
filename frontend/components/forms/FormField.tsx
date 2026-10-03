'use client';

import { FieldValues, Path, UseFormRegisterReturn } from 'react-hook-form';

interface FormFieldProps<T extends FieldValues> {
  label: string;
  name: Path<T>;
  type?: string;
  placeholder?: string;
  description?: string;
  options?: string[];
  error?: string;
  register: UseFormRegisterReturn;
  required?: boolean;
}

export function FormField<T extends FieldValues>({
  label,
  name,
  type = 'text',
  placeholder,
  description,
  options,
  error,
  register,
  required = false,
}: FormFieldProps<T>) {
  return (
    <div className="form-field-wrapper">
      <label htmlFor={name} className="form-label">
        {label}
        {required && <span className="text-red-500">*</span>}
      </label>

      {type === 'select' ? (
        <select
          id={name}
          {...register}
          className="form-select"
        >
          <option value="">-- Select {label} --</option>
          {options?.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      ) : type === 'textarea' ? (
        <textarea
          id={name}
          {...register}
          placeholder={placeholder}
          className="form-textarea"
          rows={4}
        />
      ) : (
        <input
          id={name}
          type={type}
          {...register}
          placeholder={placeholder}
          className="form-input"
        />
      )}

      {description && <p className="form-description">{description}</p>}
      {error && <p className="form-error">{error}</p>}
    </div>
  );
}
