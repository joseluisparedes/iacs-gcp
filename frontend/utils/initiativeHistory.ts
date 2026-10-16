export interface HistoryStateInfo {
  number: string;
  label: string;
  circleClass: string;
  badgeClass: string;
  dotColor: string;
}

export function formatDateDDMMYYYY(val: string | Date | null | undefined): string {
  if (!val) return '—';
  try {
    const d = new Date(val);
    if (isNaN(d.getTime())) return String(val);
    const day = String(d.getDate()).padStart(2, '0');
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const year = d.getFullYear();
    return `${day}/${month}/${year}`;
  } catch {
    return String(val);
  }
}

export function formatDateTimeDDMMYYYY(val: string | Date | null | undefined): string {
  if (!val) return '—';
  try {
    const d = new Date(val);
    if (isNaN(d.getTime())) return String(val);
    const day = String(d.getDate()).padStart(2, '0');
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const year = d.getFullYear();
    const hours = String(d.getHours()).padStart(2, '0');
    const minutes = String(d.getMinutes()).padStart(2, '0');
    return `${day}/${month}/${year}, ${hours}:${minutes}`;
  } catch {
    return String(val);
  }
}

export function getHistoryStateInfo(stateName: string, stepIndex?: number): HistoryStateInfo {
  const s = (stateName || '').toLowerCase().trim();

  if (s.includes('observad')) {
    return {
      number: '!',
      label: 'Observada',
      circleClass: 'bg-amber-500 text-white ring-4 ring-amber-100 shadow-sm animate-pulse',
      badgeClass: 'bg-amber-50 text-amber-800 border-amber-200',
      dotColor: 'bg-amber-500',
    };
  }
  if (s.includes('desestimad') || s.includes('rechaz')) {
    return {
      number: '✕',
      label: 'Desestimada',
      circleClass: 'bg-rose-500 text-white ring-4 ring-rose-100 shadow-sm',
      badgeClass: 'bg-rose-50 text-rose-700 border-rose-200',
      dotColor: 'bg-rose-500',
    };
  }
  if (s.includes('fin') || s.includes('producci') || s.includes('aprobación final') || s.includes('finaliz')) {
    return {
      number: '✓',
      label: 'Planificación / Fin',
      circleClass: 'bg-emerald-600 text-white ring-4 ring-emerald-100 shadow-sm',
      badgeClass: 'bg-emerald-50 text-emerald-800 border-emerald-200',
      dotColor: 'bg-emerald-600',
    };
  }
  if (s.includes('1') || s.includes('borrador') || s.includes('registro')) {
    return {
      number: '1',
      label: '1. Borrador',
      circleClass: 'bg-[#F87171] text-white ring-4 ring-red-100 shadow-sm',
      badgeClass: 'bg-red-50 text-red-700 border-red-200',
      dotColor: 'bg-red-500',
    };
  }
  if (s.includes('2') || s.includes('evaluaci') || s.includes('viabilidad') || s.includes('bp')) {
    return {
      number: '2',
      label: 'Evaluación BP TI',
      circleClass: 'bg-[#3B82F6] text-white ring-4 ring-blue-100 shadow-sm',
      badgeClass: 'bg-blue-50 text-blue-700 border-blue-200',
      dotColor: 'bg-blue-600',
    };
  }
  if (s.includes('3') || s.includes('patrocinio') || s.includes('aprobación bo') || s.includes('bo')) {
    return {
      number: '3',
      label: '3. Aprobación BO',
      circleClass: 'bg-[#A855F7] text-white ring-4 ring-purple-100 shadow-sm',
      badgeClass: 'bg-purple-50 text-purple-700 border-purple-200',
      dotColor: 'bg-purple-600',
    };
  }
  if (s.includes('4') || s.includes('vp') || s.includes('vicepresidencia')) {
    return {
      number: '4',
      label: 'Aprobación VP',
      circleClass: 'bg-[#10B981] text-white ring-4 ring-emerald-100 shadow-sm',
      badgeClass: 'bg-emerald-50 text-emerald-700 border-emerald-200',
      dotColor: 'bg-emerald-600',
    };
  }
  if (s.includes('5') || s.includes('demanda') || s.includes('asignaci') || s.includes('dominio')) {
    return {
      number: '5',
      label: 'Asignación de Dominio',
      circleClass: 'bg-[#06B6D4] text-white ring-4 ring-cyan-100 shadow-sm',
      badgeClass: 'bg-cyan-50 text-cyan-700 border-cyan-200',
      dotColor: 'bg-cyan-600',
    };
  }
  if (s.includes('6') || s.includes('estimaci') || s.includes('presupuesto')) {
    return {
      number: '6',
      label: 'Estimación',
      circleClass: 'bg-amber-600 text-white ring-4 ring-amber-100 shadow-sm',
      badgeClass: 'bg-amber-50 text-amber-700 border-amber-200',
      dotColor: 'bg-amber-600',
    };
  }
  if (s.includes('7') || s.includes('planificaci')) {
    return {
      number: '7',
      label: 'Planificación',
      circleClass: 'bg-emerald-600 text-white ring-4 ring-emerald-100 shadow-sm',
      badgeClass: 'bg-emerald-50 text-emerald-800 border-emerald-200',
      dotColor: 'bg-emerald-600',
    };
  }

  // Fallback con número secuencial si se proporciona
  const stepNum = stepIndex !== undefined ? String(stepIndex + 1) : '•';
  const colors = [
    { circle: 'bg-[#F87171]', badge: 'bg-red-50 text-red-700 border-red-200', dot: 'bg-red-500' },
    { circle: 'bg-[#3B82F6]', badge: 'bg-blue-50 text-blue-700 border-blue-200', dot: 'bg-blue-600' },
    { circle: 'bg-[#A855F7]', badge: 'bg-purple-50 text-purple-700 border-purple-200', dot: 'bg-purple-600' },
    { circle: 'bg-[#10B981]', badge: 'bg-emerald-50 text-emerald-700 border-emerald-200', dot: 'bg-emerald-600' },
    { circle: 'bg-[#06B6D4]', badge: 'bg-cyan-50 text-cyan-700 border-cyan-200', dot: 'bg-cyan-600' },
    { circle: 'bg-[#F59E0B]', badge: 'bg-amber-50 text-amber-700 border-amber-200', dot: 'bg-amber-600' },
  ];
  const c = stepIndex !== undefined ? colors[stepIndex % colors.length] : colors[0];

  return {
    number: stepNum,
    label: stateName || 'Transición',
    circleClass: `${c.circle} text-white ring-4 ring-slate-100 shadow-sm`,
    badgeClass: c.badge,
    dotColor: c.dot,
  };
}

export function getValueCaseInsensitive(obj: Record<string, any> | null | undefined, key: string): any {
  if (!obj) return undefined;
  if (obj[key] !== undefined) return obj[key];

  const cleanKey = key.toLowerCase().replace(/_/g, '').replace(/[\s\W]/g, '');
  for (const k of Object.keys(obj)) {
    const cleanK = k.toLowerCase().replace(/_/g, '').replace(/[\s\W]/g, '');
    if (cleanK === cleanKey) {
      return obj[k];
    }
  }
  return undefined;
}
