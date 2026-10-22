export interface MacroStageDef {
  id: string;
  name: string;
  role: string;
  nodeIds?: string[];
  subRoles?: Record<string, string>;
  statusKeywords?: string[];
}

export const DEFAULT_MACRO_STAGES: MacroStageDef[] = [
  {
    id: 'borrador',
    name: 'Registro',
    role: 'Key User',
    nodeIds: ['borrador', 'start', 'ai_chat'],
    subRoles: {
      'start': 'Key User',
      'ai_chat': 'Asistente IA (Chat)',
    },
    statusKeywords: ['borrador', 'draft', 'chat', '1. borrador', 'registro'],
  },
  {
    id: 'eval_bp',
    name: 'Viabilidad BP TI',
    role: 'Business Partner',
    nodeIds: ['eval_bp'],
    subRoles: {},
    statusKeywords: ['evalua', 'viabilidad', 'eval_bp', '2. evaluaci'],
  },
  {
    id: 'aprob_bo',
    name: 'Patrocinio BO',
    role: 'Business Owner',
    nodeIds: ['aprob_bo'],
    subRoles: {},
    statusKeywords: ['patrocinio', 'aprob.*bo', '3. aprobaci'],
  },
  {
    id: 'aprob_vp',
    name: 'Aprobación VP',
    role: 'Vicepresidencia',
    nodeIds: ['aprob_vp'],
    subRoles: {},
    statusKeywords: ['aprob.*vp', 'vicepresid', '4. aprobaci'],
  },
  {
    id: 'asig_demanda',
    name: 'Demanda TI',
    role: 'Gestor Demanda',
    nodeIds: ['asig_demanda'],
    subRoles: {},
    statusKeywords: ['demanda', 'asignación de dominio', '5. asignaci'],
  },
  {
    id: 'ventana_est',
    name: 'Estimación',
    role: 'Líder Dominio',
    nodeIds: ['ventana_est', 'est_con_presupuesto', 'est_sin_presupuesto', 'val_est_bp', 'vobo_est_bo'],
    subRoles: {
      'est_con_presupuesto': 'Líder Dominio',
      'est_sin_presupuesto': 'Líder Dominio',
      'val_est_bp': 'Business Partner',
      'vobo_est_bo': 'Business Owner',
    },
    statusKeywords: ['estimaci', 'ventana', 'presupuesto', 'vobo_est'],
  },
  {
    id: 'planificacion',
    name: 'Planificación',
    role: 'Producción',
    nodeIds: ['plan_fechas', 'val_plan_bp', 'aprob_plan_bo', 'planificacion', 'end'],
    subRoles: {
      'plan_fechas': 'Líder Dominio',
      'val_plan_bp': 'Business Partner',
      'aprob_plan_bo': 'Business Owner',
      'planificacion': 'Gestor Demanda',
      'end': 'Producción',
    },
    statusKeywords: ['planifica', 'cartera', 'finalizada', 'aprobada'],
  },
];
