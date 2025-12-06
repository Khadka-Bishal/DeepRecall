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
  step: 'uploading' | 'partitioning' | 'chunking' | 'summarizing' | 'vectorizing'
): 'pending' | 'active' | 'complete' => {
  const ORDER = ['UPLOADING', 'PARTITIONING', 'CHUNKING', 'SUMMARIZING', 'VECTORIZING', 'COMPLETE'];
  const idx = ORDER.indexOf(current.toUpperCase());
  const stepIdx = ORDER.indexOf(step.toUpperCase());
  if (idx < 0 || stepIdx < 0) return 'pending';
  if (idx < stepIdx) return 'pending';
  if (idx === stepIdx) return 'active';
  return 'complete';
};
export * from './helpers';
