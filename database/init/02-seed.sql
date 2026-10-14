-- ==============================================================================
-- IACS GCP — DATOS SEMILLA INICIALES (PostgreSQL 17)
-- ==============================================================================

-- 1. Configuración del Sitio
INSERT INTO site_settings (id, maintenance_mode, system_notice)
VALUES (1, false, 'Bienvenido a IACS Enterprise (GCP Edition).')
ON CONFLICT (id) DO UPDATE SET maintenance_mode = EXCLUDED.maintenance_mode;

-- 2. Catálogo de Roles del Sistema (App Roles)
INSERT INTO app_roles (code, name, description, color, is_system, is_active) VALUES
  ('admin', 'Administrador General', 'Acceso total al sistema y gobernanza de flujos', 'indigo', true, true),
  ('registrador', 'Key user', 'Responsable de levantar iniciativas de negocio con Teo', 'emerald', true, true),
  ('bp_ti', 'Business Partner (BP)', 'Evaluador técnico y funcional de iniciativas', 'blue', true, true),
  ('entrenador_ia', 'Entrenador IA', 'Gestión de la base de conocimiento y prompts de Teo', 'violet', true, true),
  ('invitado', 'Invitado (Solo lectura)', 'Visualización de iniciativas sin permisos de edición', 'slate', true, true)
ON CONFLICT (code) DO NOTHING;

-- 3. Vicepresidencias Iniciales
INSERT INTO vps (id, name, bp_name) VALUES
  ('a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d', 'Vicepresidencia Académica', 'Carlos Mendoza'),
  ('b2c3d4e5-f6a7-4b6c-9d0e-1f2a3b4c5d6e', 'Vicepresidencia de Operaciones', 'Ana Lucía Ramos'),
  ('c3d4e5f6-a7b8-4c7d-0e1f-2a3b4c5d6e7f', 'Vicepresidencia de Finanzas', 'Jorge Velásquez'),
  ('d4e5f6a7-b8c9-4d8e-1f2a-3b4c5d6e7f8a', 'Vicepresidencia de Tecnología e Innovación', 'Elena Paredes')
ON CONFLICT (name) DO NOTHING;

-- 4. Direcciones Iniciales
INSERT INTO direcciones (id, name, vp_id) VALUES
  ('e5f6a7b8-c9d0-4e9f-2a3b-4c5d6e7f8a9b', 'Dirección de Gestión Docente', 'a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d'),
  ('f6a7b8c9-d0e1-4f0a-3b4c-5d6e7f8a9b0c', 'Dirección de Experiencia Estudiantil', 'a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d'),
  ('a7b8c9d0-e1f2-4a1b-4c5d-6e7f8a9b0c1d', 'Dirección de Infraestructura y Mantenimiento', 'b2c3d4e5-f6a7-4b6c-9d0e-1f2a3b4c5d6e'),
  ('b8c9d0e1-f2a3-4b2c-5d6e-7f8a9b0c1d2e', 'Dirección de Contabilidad y Tesorería', 'c3d4e5f6-a7b8-4c7d-0e1f-2a3b4c5d6e7f'),
  ('c9d0e1f2-a3b4-4c3d-6e7f-8a9b0c1d2e3f', 'Dirección de Arquitectura y Soluciones TI', 'd4e5f6a7-b8c9-4d8e-1f2a-3b4c5d6e7f8a')
ON CONFLICT (name, vp_id) DO NOTHING;

-- 5. Usuario Administrador Inicial
INSERT INTO profiles (id, email, name, is_active) VALUES
  ('00000000-0000-0000-0000-000000000001', 'admin@iacs.empresa.com', 'Administrador IACS', true),
  ('00000000-0000-0000-0000-000000000002', 'keyuser@iacs.empresa.com', 'Solicitante Académico', true),
  ('00000000-0000-0000-0000-000000000003', 'bpti@iacs.empresa.com', 'Business Partner TI', true)
ON CONFLICT (email) DO NOTHING;

INSERT INTO profile_roles (profile_id, role, is_transversal) VALUES
  ('00000000-0000-0000-0000-000000000001', 'admin', true),
  ('00000000-0000-0000-0000-000000000002', 'registrador', true),
  ('00000000-0000-0000-0000-000000000003', 'bp_ti', true)
ON CONFLICT DO NOTHING;

-- 6. Campos Dinámicos de Iniciativas (Initiative Fields)
INSERT INTO initiative_fields (label, key, field_type, options, is_visible, is_required, sort_order, ask_in_initial_form, help_text) VALUES
  ('Institución', 'institucion', 'select', '["UPC", "UPN", "Cibertec", "Laureate Perú", "Corporativo"]'::jsonb, true, true, 1, true, 'Selecciona la institución donde se ejecutará el proyecto'),
  ('Vicepresidencia', 'vicepresidencia', 'select', '["Vicepresidencia Académica", "Vicepresidencia de Operaciones", "Vicepresidencia de Finanzas", "Vicepresidencia de Tecnología e Innovación"]'::jsonb, true, true, 2, true, 'Área ejecutiva patrocinadora'),
  ('Dirección', 'direccion', 'text', '[]'::jsonb, true, true, 3, true, 'Dirección o departamento solicitante'),
  ('Título de la Iniciativa', 'titulo', 'text', '[]'::jsonb, true, true, 4, false, 'Nombre concreto y descriptivo de la iniciativa (generado con Teo)'),
  ('Objetivo Principal', 'objetivo', 'text', '[]'::jsonb, true, true, 5, false, 'Propósito medible y alcance de la solución'),
  ('Descripción de la Necesidad', 'descripcion_de_la_necesidad', 'text', '[]'::jsonb, true, true, 6, false, 'Situación actual, dolor operativo y desafío a resolver'),
  ('Proceso y Áreas Impactadas', 'proceso_y_areas_impactadas', 'text', '[]'::jsonb, true, true, 7, false, 'Procesos de negocio y áreas involucradas'),
  ('Usuarios Beneficiados', 'usuarios_beneficiados', 'text', '[]'::jsonb, true, false, 8, false, 'Segmentos de usuarios y estimación de personas beneficiadas'),
  ('Pilar Estratégico', 'pilar_estrategico', 'select', '["Crecimiento y Retención", "Excelencia Académica", "Eficiencia Operativa", "Transformación Digital e Innovación", "Cumplimiento Regulatorio"]'::jsonb, true, false, 9, false, 'Alineamiento con los objetivos estratégicos corporativos'),
  ('Beneficio Cuantitativo Anual', 'beneficio_cuantitativo_anual', 'text', '[]'::jsonb, true, false, 10, false, 'Ahorro estimado en horas-hombre, costos o incremento de ingresos'),
  ('Beneficio Cualitativo', 'beneficio_cualitativo', 'text', '[]'::jsonb, true, false, 11, false, 'Impacto en satisfacción, reputación y clima'),
  ('¿Es Proyecto SPO?', 'es_necesidad_spo', 'select', '["No", "Sí - SPO Global", "Sí - SPO Local"]'::jsonb, true, false, 12, false, 'Indicar si se rige bajo el marco SPO'),
  ('Fecha Requerida de Implementación', 'fecha_requerida', 'date', '[]'::jsonb, true, true, 13, false, 'Fecha estimada límite de salida a producción (DD/MM/AAAA)'),
  ('Escenarios de Pruebas', 'escenarios_pruebas', 'text', '[]'::jsonb, true, false, 14, false, 'Criterios de aceptación y pruebas críticas de usuario')
ON CONFLICT (key) DO NOTHING;

-- 7. Consentimientos de Etapa Predeterminados (Cadena de Custodia)
INSERT INTO stage_consents (code, title, statement, version, is_active) VALUES
  ('DICTAMEN_TECNICO_BP', 'Dictamen Técnico de Factibilidad y Arquitectura', 'Declaro que he revisado exhaustivamente los requerimientos técnicos, dependencias con sistemas core (Banner, Blackboard, SAP, Salesforce) y certifico la viabilidad de la presente iniciativa para su pase al portafolio de demanda.', 1, true),
  ('CONFORMIDAD_SOLICITANTE', 'Conformidad y Cierre de Levantamiento', 'Doy fe de que el levantamiento asistido por Teo representa fielmente la necesidad operativa de mi área y acepto los términos de alcance y fecha propuesta.', 1, true)
ON CONFLICT (code) DO NOTHING;

-- 8. Flujo Canónico de Trabajo Activo (Workflow Definition v1)
INSERT INTO workflow_definitions (id, name, version, status, description, graph_json, published_at) VALUES
  ('11111111-1111-1111-1111-111111111111', 'Flujo Canónico IACS Enterprise', 1, 'published', 'Flujo canónico estándar para evaluación y aprobación de iniciativas de TI.',
  '{
    "nodes": [
      {"id": "node_borrador", "type": "state", "position": {"x": 100, "y": 200}, "data": {"label": "Borrador", "nodeType": "state", "stateSubtype": "standard"}},
      {"id": "node_pendiente", "type": "state", "position": {"x": 400, "y": 200}, "data": {"label": "Pendiente de aprobación", "nodeType": "state", "stateSubtype": "standard"}},
      {"id": "node_observada", "type": "state", "position": {"x": 400, "y": 400}, "data": {"label": "Observada", "nodeType": "state", "stateSubtype": "observada"}},
      {"id": "node_demanda", "type": "state", "position": {"x": 750, "y": 200}, "data": {"label": "En demanda", "nodeType": "state", "stateSubtype": "demanda"}},
      {"id": "node_desestimada", "type": "state", "position": {"x": 750, "y": 400}, "data": {"label": "Desestimada", "nodeType": "state", "stateSubtype": "desestimada"}}
    ],
    "edges": [
      {"id": "edge_1", "source": "node_borrador", "target": "node_pendiente", "label": "Enviar a Revisión"},
      {"id": "edge_2", "source": "node_pendiente", "target": "node_demanda", "label": "Aprobar (VoBo)"},
      {"id": "edge_3", "source": "node_pendiente", "target": "node_observada", "label": "Observar"},
      {"id": "edge_4", "source": "node_observada", "target": "node_pendiente", "label": "Subsanar Observación"},
      {"id": "edge_5", "source": "node_pendiente", "target": "node_desestimada", "label": "Desestimar"}
    ]
  }'::jsonb, now())
ON CONFLICT (id) DO NOTHING;

-- 9. Roles en Nodos del Flujo Canónico
INSERT INTO workflow_node_roles (workflow_id, node_id, role_name, can_edit, can_approve, can_reject) VALUES
  ('11111111-1111-1111-1111-111111111111', 'node_borrador', 'registrador', true, true, false),
  ('11111111-1111-1111-1111-111111111111', 'node_borrador', 'admin', true, true, false),
  ('11111111-1111-1111-1111-111111111111', 'node_pendiente', 'bp_ti', true, true, true),
  ('11111111-1111-1111-1111-111111111111', 'node_pendiente', 'admin', true, true, true),
  ('11111111-1111-1111-1111-111111111111', 'node_observada', 'registrador', true, true, false),
  ('11111111-1111-1111-1111-111111111111', 'node_observada', 'admin', true, true, false)
ON CONFLICT DO NOTHING;

-- 10. Base de Conocimientos Inicial para Teo (ai_knowledge_folders y ai_training_config)
INSERT INTO ai_knowledge_folders (id, name, level, sort_order) VALUES
  ('22222222-2222-2222-2222-222222222222', 'Políticas Institucionales de TI', 1, 1),
  ('33333333-3333-3333-3333-333333333333', 'Lineamientos de Arquitectura', 1, 2)
ON CONFLICT (id) DO NOTHING;

INSERT INTO ai_training_config (layer, title, content, is_active, sort_order, folder_id) VALUES
  ('identity', 'Personalidad y Rol de Teo', 'Eres Teo, el asesor de arquitectura e iniciativas de TI para Laureate Perú (UPC, UPN, Cibertec). Tu misión es guiar de forma empática, ejecutiva y analítica a los solicitantes para estructurar iniciativas claras, cuantificables y viables.', true, 1, '22222222-2222-2222-2222-222222222222'),
  ('guardrails', 'Regla de No Títulos Genéricos', 'Está estrictamente prohibido emitir o aceptar títulos genéricos como "Iniciativa de mejora" o "Nuevo sistema". Debes sintetizar un título concreto con verbo en infinitivo.', true, 1, '33333333-3333-3333-3333-333333333333'),
  ('guardrails', 'Metodología Grill-Me', 'Aplica cuestionamiento constructivo si el usuario brinda respuestas ambiguas. Indaga sobre integraciones con Banner, Salesforce, SAP, Blackboard y cronograma.', true, 2, '33333333-3333-3333-3333-333333333333')
ON CONFLICT DO NOTHING;
