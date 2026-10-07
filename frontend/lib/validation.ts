import { z } from 'zod';

export const NDAFormSchema = z.object({
  purpose: z.string().min(10, 'Purpose must be at least 10 characters').max(2000),
  effectiveDate: z.string().refine(
    (date) => !isNaN(Date.parse(date)),
    'Invalid date format'
  ),
  mndaTerm: z.string().min(1, 'MNDA Term is required').max(200),
  termOfConfidentiality: z.string().min(1, 'Term of Confidentiality is required').max(200),
  governingLaw: z.enum(['California', 'New York', 'Delaware', 'Texas', 'Other']),
  jurisdiction: z.string().min(3, 'Jurisdiction is required').max(200),
  partyAName: z.string().min(2, 'Party A name must be at least 2 characters').max(255),
  partyBName: z.string().min(2, 'Party B name must be at least 2 characters').max(255),
});

export type NDAFormValues = z.infer<typeof NDAFormSchema>;
