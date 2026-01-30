/**
 * Central export for all utilities
 */

export * from './constants';
export * from './formatters';
export * from './transformers';
export * from './validators';
export * from './styles';
export const mapStepStatus = (
  current: string,
  step: string
): 'pending' | 'active' | 'complete' => {
  const ORDER = ['UPLOADING', 'PARTITIONING', 'CHUNKING', 'SUMMARIZING', 'VECTORIZING', 'COMPLETE'];
  // Virtual steps specific to UI, mapped from backend states
  if (step === 'securing' || step === 'orchestrating') {
     const idx = ORDER.indexOf(current.toUpperCase());
     // AWS steps happen between UPLOADING (0) and PARTITIONING (1)
     if (idx > 0) return 'complete'; // Past uploading
     // Crucial: Return 'pending' during upload so we don't have two spinners.
     // The user will see Uploading -> Partitioning (with AWS steps marking complete instantly)
     // This is the only safe way without a fake delay state.
     return 'pending';
  }

  const idx = ORDER.indexOf(current.toUpperCase());
  const stepIdx = ORDER.indexOf(step.toUpperCase());
  if (idx < 0 || stepIdx < 0) return 'pending';
  if (idx < stepIdx) return 'pending';
  if (idx === stepIdx) return 'active';
  return 'complete';
};
export * from './helpers';
