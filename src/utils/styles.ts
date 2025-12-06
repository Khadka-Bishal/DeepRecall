import { ELEMENT_COLORS, STATUS_COLORS } from './constants';

export const getElementColorClasses = (type: string): string => {
  const colors = ELEMENT_COLORS[type as keyof typeof ELEMENT_COLORS] || ELEMENT_COLORS.Default;
  return `${colors.bg} ${colors.text} ${colors.border}`;
};

export const getStatusColorClasses = (status: 'pending' | 'active' | 'complete'): string => {
  const colors = STATUS_COLORS[status];
  const classes = `${colors.bg} ${colors.border} ${colors.text}`;
  const shadow = status === 'active' && 'shadow' in colors ? (colors as any).shadow : '';
  return shadow ? `${classes} ${shadow}` : classes;
};

export const cn = (...classes: (string | boolean | undefined)[]): string => {
  return classes.filter(Boolean).join(' ');
};

export const getChunkTypeColor = (type: 'text' | 'mixed'): string => {
  return type === 'mixed' ? 'bg-purple-500' : 'bg-zinc-500';
};

export const getRoleColor = (role: 'user' | 'assistant'): string => {
  return role === 'assistant' ? 'text-emerald-500' : 'text-zinc-400';
};

export const getRoleTextColor = (role: 'user' | 'assistant'): string => {
  return role === 'assistant' ? 'text-zinc-300' : 'text-zinc-100';
};

export const getButtonClasses = (
  disabled: boolean = false,
  variant: 'primary' | 'secondary' = 'primary'
): string => {
  if (disabled) {
    return 'bg-zinc-800 text-zinc-600 cursor-not-allowed';
  }

  if (variant === 'primary') {
    return 'bg-zinc-100 text-zinc-900 hover:bg-white';
  }

  return 'bg-zinc-900 hover:bg-zinc-800 text-zinc-300';
};

export const buttonPrimary = (disabled = false): string =>
  `p-1.5 rounded-md ${getButtonClasses(disabled, 'primary')}`;

export const buttonSecondary = (disabled = false): string =>
  `p-1.5 rounded-md ${getButtonClasses(disabled, 'secondary')}`;

export const buttonSmall = (extra = ''): string => `px-2 py-1 rounded ${extra}`;
