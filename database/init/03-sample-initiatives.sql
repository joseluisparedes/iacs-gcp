-- ==============================================================================
-- IACS GCP — SEED DE 11 INICIATIVAS DE PRUEBA (Paridad 1:1 con Image 1)
-- ==============================================================================

-- 1. Asegurar VPs "Comercial" y "Académica"
INSERT INTO vps (id, name, bp_name) VALUES
  ('11111111-1111-1111-1111-111111111101', 'Comercial', 'Sponsor Comercial'),
  ('11111111-1111-1111-1111-111111111102', 'Académica', 'Sponsor Académico')
ON CONFLICT (name) DO UPDATE SET bp_name = EXCLUDED.bp_name;

-- 2. Asegurar Direcciones asociadas
INSERT INTO direcciones (id, name, vp_id) VALUES
  ('22222222-2222-2222-2222-222222222201', 'Dirección de Admisiones y Ventas', '11111111-1111-1111-1111-111111111101'),
  ('22222222-2222-2222-2222-222222222202', 'Dirección de Marketing Corporativo', '11111111-1111-1111-1111-111111111101'),
  ('22222222-2222-2222-2222-222222222203', 'Dirección de Retención y Fidelización', '11111111-1111-1111-1111-111111111101'),
  ('22222222-2222-2222-2222-222222222204', 'Dirección de Servicios Académicos', '11111111-1111-1111-1111-111111111102')
ON CONFLICT (name, vp_id) DO NOTHING;

-- 3. Limpiar iniciativas previas de prueba si las hubiera
DELETE FROM initiatives WHERE id LIKE 'INIT-SAMPLE-%';

-- 4. Insertar las 10 iniciativas de VP Comercial
-- 3 x Borrador
INSERT INTO initiatives (id, status, current_node_id, form_data, summary, created_at, updated_at) VALUES
(
  'INIT-SAMPLE-01',
  'Borrador',
  'borrador',
  jsonb_build_object(
    'institucion', 'UPC',
    'vicepresidencia', 'Comercial',
    'direccion', 'Dirección de Admisiones y Ventas',
    'registrador', 'Administrador General',
    'bp_ti_asignado', 'Carlos Mendoza',
    'lider_de_dominio_responsable', 'Roberto Gómez',
    'titulo', 'Automatización del proceso de captura de prospectos digitales',
    '_reached_summary', true
  ),
  jsonb_build_object(
    'id_corta', 'COM-001',
    'titulo', 'Automatización del proceso de captura de prospectos digitales',
    'objetivo', 'Optimizar el embudo de admisión e integrar leads de Meta/Google al CRM Salesforce.',
    'descripcionProblema', 'Demoras de hasta 48 horas en la distribución manual de prospectos a los asesores.',
    'complejidad', 'Media',
    'riesgo', 'Bajo'
  ),
  NOW() - INTERVAL '5 days',
  NOW() - INTERVAL '5 days'
),
(
  'INIT-SAMPLE-02',
  'Borrador',
  'borrador',
  jsonb_build_object(
    'institucion', 'UPN',
    'vicepresidencia', 'Comercial',
    'direccion', 'Dirección de Marketing Corporativo',
    'registrador', 'Administrador General',
    'bp_ti_asignado', 'Carlos Mendoza',
    'lider_de_dominio_responsable', 'Roberto Gómez',
    'titulo', 'Portal de eventos y charlas vocacionales online',
    '_reached_summary', true
  ),
  jsonb_build_object(
    'id_corta', 'COM-002',
    'titulo', 'Portal de eventos y charlas vocacionales online',
    'objetivo', 'Centralizar el registro a webinars y talleres vivenciales para postulantes.',
    'complejidad', 'Baja',
    'riesgo', 'Bajo'
  ),
  NOW() - INTERVAL '4 days',
  NOW() - INTERVAL '4 days'
),
(
  'INIT-SAMPLE-03',
  'Borrador',
  'borrador',
  jsonb_build_object(
    'institucion', 'Cibertec',
    'vicepresidencia', 'Comercial',
    'direccion', 'Dirección de Retención y Fidelización',
    'registrador', 'Administrador General',
    'bp_ti_asignado', 'Ana Lucía Ramos',
    'lider_de_dominio_responsable', 'Jorge Velásquez',
    'titulo', 'Sistema de alertas tempranas de deserción de postulantes',
    '_reached_summary', true
  ),
  jsonb_build_object(
    'id_corta', 'COM-003',
    'titulo', 'Sistema de alertas tempranas de deserción de postulantes',
    'objetivo', 'Modelo predictivo para identificar candidatos con riesgo de no completar su matrícula.',
    'complejidad', 'Alta',
    'riesgo', 'Medio'
  ),
  NOW() - INTERVAL '3 days',
  NOW() - INTERVAL '3 days'
),

-- 3 x Iniciativa planificada
(
  'INIT-SAMPLE-04',
  'Iniciativa planificada',
  'planificacion',
  jsonb_build_object(
    'institucion', 'UPC',
    'vicepresidencia', 'Comercial',
    'direccion', 'Dirección de Admisiones y Ventas',
    'registrador', 'Administrador General',
    'bp_ti_asignado', 'Carlos Mendoza',
    'lider_de_dominio_responsable', 'Roberto Gómez',
    'titulo', 'Integración de pasarela de pagos QR para matrículas y reservas',
    '_reached_summary', true
  ),
  jsonb_build_object(
    'id_corta', 'COM-004',
    'titulo', 'Integración de pasarela de pagos QR para matrículas y reservas',
    'objetivo', 'Permitir pagos instantáneos con Yape y Plin en el portal de admisión.',
    'complejidad', 'Media',
    'riesgo', 'Bajo'
  ),
  NOW() - INTERVAL '10 days',
  NOW() - INTERVAL '10 days'
),
(
  'INIT-SAMPLE-05',
  'Iniciativa planificada',
  'planificacion',
  jsonb_build_object(
    'institucion', 'UPN',
    'vicepresidencia', 'Comercial',
    'direccion', 'Dirección de Marketing Corporativo',
    'registrador', 'Administrador General',
    'bp_ti_asignado', 'Ana Lucía Ramos',
    'lider_de_dominio_responsable', 'Roberto Gómez',
    'titulo', 'Módulo de autogestión de convalidaciones en línea',
    '_reached_summary', true
  ),
  jsonb_build_object(
    'id_corta', 'COM-005',
    'titulo', 'Módulo de autogestión de convalidaciones en línea',
    'objetivo', 'Revisión automática de mallas curriculares y sílabos para traslados externos.',
    'complejidad', 'Alta',
    'riesgo', 'Medio'
  ),
  NOW() - INTERVAL '9 days',
  NOW() - INTERVAL '9 days'
),
(
  'INIT-SAMPLE-06',
  'Iniciativa planificada',
  'planificacion',
  jsonb_build_object(
    'institucion', 'Laureate Perú',
    'vicepresidencia', 'Comercial',
    'direccion', 'Dirección de Retención y Fidelización',
    'registrador', 'Administrador General',
    'bp_ti_asignado', 'Carlos Mendoza',
    'lider_de_dominio_responsable', 'Jorge Velásquez',
    'titulo', 'Tablero analítico corporativo de conversión de admisiones',
    '_reached_summary', true
  ),
  jsonb_build_object(
    'id_corta', 'COM-006',
    'titulo', 'Tablero analítico corporativo de conversión de admisiones',
    'objetivo', 'Visualización en tiempo real de metas comerciales por sede y programa académico.',
    'complejidad', 'Media',
    'riesgo', 'Bajo'
  ),
  NOW() - INTERVAL '8 days',
  NOW() - INTERVAL '8 days'
),

-- 3 x En evaluación del BP TI
(
  'INIT-SAMPLE-07',
  'En evaluación del BP TI',
  'eval_bp',
  jsonb_build_object(
    'institucion', 'UPC',
    'vicepresidencia', 'Comercial',
    'direccion', 'Dirección de Admisiones y Ventas',
    'registrador', 'Administrador General',
    'bp_ti_asignado', 'Carlos Mendoza',
    'lider_de_dominio_responsable', 'Roberto Gómez',
    'titulo', 'Chatbot omnicanal de WhatsApp para atención 24/7 de postulantes',
    '_reached_summary', true
  ),
  jsonb_build_object(
    'id_corta', 'COM-007',
    'titulo', 'Chatbot omnicanal de WhatsApp para atención 24/7 de postulantes',
    'objetivo', 'Desplegar asistente conversacional integrado con IA generativa de Vertex AI.',
    'complejidad', 'Alta',
    'riesgo', 'Medio'
  ),
  NOW() - INTERVAL '2 days',
  NOW() - INTERVAL '2 days'
),
(
  'INIT-SAMPLE-08',
  'En evaluación del BP TI',
  'eval_bp',
  jsonb_build_object(
    'institucion', 'Cibertec',
    'vicepresidencia', 'Comercial',
    'direccion', 'Dirección de Marketing Corporativo',
    'registrador', 'Administrador General',
    'bp_ti_asignado', 'Ana Lucía Ramos',
    'lider_de_dominio_responsable', 'Jorge Velásquez',
    'titulo', 'Plataforma B2B para convenios educativos corporativos',
    '_reached_summary', true
  ),
  jsonb_build_object(
    'id_corta', 'COM-008',
    'titulo', 'Plataforma B2B para convenios educativos corporativos',
    'objetivo', 'Portal para que empresas asociadas gestionen becas y capacitaciones para colaboradores.',
    'complejidad', 'Media',
    'riesgo', 'Bajo'
  ),
  NOW() - INTERVAL '2 days',
  NOW() - INTERVAL '2 days'
),
(
  'INIT-SAMPLE-09',
  'En evaluación del BP TI',
  'eval_bp',
  jsonb_build_object(
    'institucion', 'UPN',
    'vicepresidencia', 'Comercial',
    'direccion', 'Dirección de Retención y Fidelización',
    'registrador', 'Administrador General',
    'bp_ti_asignado', 'Carlos Mendoza',
    'lider_de_dominio_responsable', 'Roberto Gómez',
    'titulo', 'App móvil para seguimiento de postulaciones y citas de admisión',
    '_reached_summary', true
  ),
  jsonb_build_object(
    'id_corta', 'COM-009',
    'titulo', 'App móvil para seguimiento de postulaciones y citas de admisión',
    'objetivo', 'Notificaciones push y tracking en tiempo real del estado de admisión del estudiante.',
    'complejidad', 'Alta',
    'riesgo', 'Alto'
  ),
  NOW() - INTERVAL '1 day',
  NOW() - INTERVAL '1 day'
),

-- 1 x Pendiente de aprobación BO
(
  'INIT-SAMPLE-10',
  'Pendiente de aprobación BO',
  'aprob_bo',
  jsonb_build_object(
    'institucion', 'UPC',
    'vicepresidencia', 'Comercial',
    'direccion', 'Dirección de Admisiones y Ventas',
    'registrador', 'Administrador General',
    'bp_ti_asignado', 'Carlos Mendoza',
    'lider_de_dominio_responsable', 'Roberto Gómez',
    'titulo', 'Digitalización biométrica de validación de identidad en evaluaciones',
    '_reached_summary', true
  ),
  jsonb_build_object(
    'id_corta', 'COM-010',
    'titulo', 'Digitalización biométrica de validación de identidad en evaluaciones',
    'objetivo', 'Validación facial y cotejo automático con RENIEC para exámenes de admisión virtuales.',
    'complejidad', 'Alta',
    'riesgo', 'Alto'
  ),
  NOW() - INTERVAL '6 hours',
  NOW() - INTERVAL '6 hours'
),

-- 5. Insertar 1 iniciativa de VP Académica
-- 1 x Pendiente de estimación sin Presupuesto
(
  'INIT-SAMPLE-11',
  'Pendiente de estimación sin Presupuesto',
  'est_sin_presupuesto',
  jsonb_build_object(
    'institucion', 'UPC',
    'vicepresidencia', 'Académica',
    'direccion', 'Dirección de Servicios Académicos',
    'registrador', 'Administrador General',
    'bp_ti_asignado', 'Ana Lucía Ramos',
    'lider_de_dominio_responsable', 'Jorge Velásquez',
    'titulo', 'Sistema de asignación automática de horarios y carga docente',
    '_reached_summary', true
  ),
  jsonb_build_object(
    'id_corta', 'ACA-001',
    'titulo', 'Sistema de asignación automática de horarios y carga docente',
    'objetivo', 'Algoritmo de optimización de aulas y cruce de disponibilidad de profesores a tiempo parcial.',
    'complejidad', 'Alta',
    'riesgo', 'Medio'
  ),
  NOW() - INTERVAL '12 hours',
  NOW() - INTERVAL '12 hours'
);
