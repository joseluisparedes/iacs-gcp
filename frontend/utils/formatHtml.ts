/**
 * Utilidades de formateo HTML y Markdown para Teo y el chat conversacional de IACS.
 * Réplica exacta y adaptada para Vue / Nuxt del archivo formatHtml.ts del proyecto original.
 */

export function parseHtmlToMarkdown(text?: string): string {
  if (!text) return "";
  let md = String(text);

  md = md.replace(/<\s*br\s*\/?>/gi, '\n');
  md = md.replace(/<\s*\/p\s*>/gi, '\n\n');
  md = md.replace(/<\s*p[^>]*>/gi, '');

  md = md.replace(/<\s*h1[^>]*>(.*?)<\s*\/h1\s*>/gi, '\n# $1\n\n');
  md = md.replace(/<\s*h2[^>]*>(.*?)<\s*\/h2\s*>/gi, '\n## $1\n\n');
  md = md.replace(/<\s*h3[^>]*>(.*?)<\s*\/h3\s*>/gi, '\n### $1\n\n');
  md = md.replace(/<\s*h4[^>]*>(.*?)<\s*\/h4\s*>/gi, '\n#### $1\n\n');
  md = md.replace(/<\s*h5[^>]*>(.*?)<\s*\/h5\s*>/gi, '\n##### $1\n\n');
  md = md.replace(/<\s*h6[^>]*>(.*?)<\s*\/h6\s*>/gi, '\n###### $1\n\n');

  md = md.replace(/<\s*b\s*>(.*?)<\s*\/\s*b\s*>/gi, '**$1**');
  md = md.replace(/<\s*strong\s*>(.*?)<\s*\/\s*strong\s*>/gi, '**$1**');
  md = md.replace(/<\s*i\s*>(.*?)<\s*\/\s*i\s*>/gi, '*$1*');
  md = md.replace(/<\s*em\s*>(.*?)<\s*\/\s*em\s*>/gi, '*$1*');

  md = md.replace(/<\s*(?:s|strike|del)\s*>(.*?)<\s*\/(?:s|strike|del)\s*>/gi, '~~$1~~');
  md = md.replace(/<\s*li[^>]*>(.*?)<\s*\/li\s*>/gi, '\n- $1');
  md = md.replace(/<\s*\/?(?:ul|ol)[^>]*>/gi, '\n');
  md = md.replace(/<\s*hr\s*\/?>/gi, '\n\n---\n\n');

  md = md.replace(/<\s*pre\s*>\s*<\s*code[^>]*>([\s\S]*?)<\s*\/code\s*>\s*<\s*\/pre\s*>/gi, '\n```\n$1\n```\n');
  md = md.replace(/<\s*code[^>]*>(.*?)<\s*\/code\s*>/gi, '`$1`');
  md = md.replace(/<\s*blockquote[^>]*>([\s\S]*?)<\s*\/blockquote\s*>/gi, '\n> $1\n');
  md = md.replace(/<\s*a\s+[^>]*href=["']([^"']+)["'][^>]*>(.*?)<\s*\/a\s*>/gi, '[$2]($1)');

  md = md.replace(/<\s*\/?(?:div|span|section|article)[^>]*>/gi, '');

  md = md.replace(/&nbsp;/gi, ' ')
         .replace(/&amp;/gi, '&')
         .replace(/&lt;/gi, '<')
         .replace(/&gt;/gi, '>')
         .replace(/&quot;/gi, '"')
         .replace(/&#39;/gi, "'");

  md = md.replace(/\n{3,}/g, '\n\n');

  return md.trim();
}

/**
 * Sanitiza texto con codificación corrupta heredada (signos de interrogación en lugar de tildes/ñ/¡/¿)
 */
export function sanitizeCorruptedEncoding(str?: string): string {
  if (!str) return '';
  let s = String(str);

  return s
    // Signos de exclamación al inicio de frases / saludos
    .replace(/(^|[.!?\n]\s*)\?Hola!?\s*/gi, '$1¡Hola! ')
    .replace(/(^|[.!?\n]\s*)\?Excelente!?\s*/gi, '$1¡Excelente! ')
    .replace(/(^|[.!?\n]\s*)\?Perfecto!?\s*/gi, '$1¡Perfecto! ')
    .replace(/(^|[.!?\n]\s*)\?Genial!?\s*/gi, '$1¡Genial! ')
    .replace(/¡Hola!\s*!+/g, '¡Hola! ')
    .replace(/¡Excelente!\s*!+/g, '¡Excelente! ')
    .replace(/¡Perfecto!\s*!+/g, '¡Perfecto! ')

    // Interrogación invertida de apertura en preguntas
    .replace(/\?Cu\?l(?=\s|[.,;:!?]|$)/gi, '¿Cuál')
    .replace(/\?Cu[aá]l(?=\s|[.,;:!?]|$)/gi, '¿Cuál')
    .replace(/\?Qu\?(?=\s|[.,;:!?]|$)/gi, '¿Qué')
    .replace(/\?Qu[eé](?=\s|[.,;:!?]|$)/gi, '¿Qué')
    .replace(/\?C\?mo(?=\s|[.,;:!?]|$)/gi, '¿Cómo')
    .replace(/\?C[oó]mo(?=\s|[.,;:!?]|$)/gi, '¿Cómo')
    .replace(/\?D\?nde(?=\s|[.,;:!?]|$)/gi, '¿Dónde')
    .replace(/\?D[oó]nde(?=\s|[.,;:!?]|$)/gi, '¿Dónde')
    .replace(/\?Cu\?ndo(?=\s|[.,;:!?]|$)/gi, '¿Cuándo')
    .replace(/\?Cu[aá]ndo(?=\s|[.,;:!?]|$)/gi, '¿Cuándo')
    .replace(/\?Qui\?n(?=\s|[.,;:!?]|$)/gi, '¿Quién')
    .replace(/\?Qui[eé]n(?=\s|[.,;:!?]|$)/gi, '¿Quién')
    .replace(/\?Por qu\?(?=\s|[.,;:!?]|$)/gi, '¿Por qué')
    .replace(/\?Por qu[eé](?=\s|[.,;:!?]|$)/gi, '¿Por qué')

    // Palabras interrogativas / relativas ("qué", "cuál", etc.)
    .replace(/(^|\s|[.,;:¡¿(])qu\?(?=\s|[.,;:!?)]|$)/g, '$1qué')
    .replace(/(^|\s|[.,;:¡¿(])Qu\?(?=\s|[.,;:!?)]|$)/g, '$1Qué')
    .replace(/(^|\s|[.,;:¡¿(])cu\?l(?=\s|[.,;:!?)]|$)/gi, '$1cuál')
    .replace(/(^|\s|[.,;:¡¿(])c\?mo(?=\s|[.,;:!?)]|$)/gi, '$1cómo')
    .replace(/(^|\s|[.,;:¡¿(])d\?nde(?=\s|[.,;:!?)]|$)/gi, '$1dónde')
    .replace(/(^|\s|[.,;:¡¿(])cu\?ndo(?=\s|[.,;:!?)]|$)/gi, '$1cuándo')
    .replace(/(^|\s|[.,;:¡¿(])qui\?n(?=\s|[.,;:!?)]|$)/gi, '$1quién')
    .replace(/(^|\s|[.,;:¡¿(])cu\?nt([oa]s?)(?=\s|[.,;:!?)]|$)/gi, '$1cuánt$2')
    .replace(/(^|\s|[.,;:¡¿(])Cu\?ntame(?=\s|[.,;:!?)]|$)/gi, '$1Cuéntame')

    // Si quedó un ¿Qu? o ¿Cu?l etc.
    .replace(/¿Qu\?(?=\s|[.,;:!?]|$)/gi, '¿Qué')
    .replace(/¿Cu\?l(?=\s|[.,;:!?]|$)/gi, '¿Cuál')

    // Sufijos muy comunes en español con tildes dañadas: -ción, -sión, -gión
    .replace(/([a-zA-ZáéíóúÁÉÍÓÚñÑ])ci\?n(?=\s|[.,;:!?)]|$)/gi, '$1ción')
    .replace(/([a-zA-ZáéíóúÁÉÍÓÚñÑ])si\?n(?=\s|[.,;:!?)]|$)/gi, '$1sión')
    .replace(/([a-zA-ZáéíóúÁÉÍÓÚñÑ])gi\?n(?=\s|[.,;:!?)]|$)/gi, '$1gión')

    // Verbos en futuro y condicional (3ra persona singular/plural con tilde en á/án)
    .replace(/([a-zA-Záéíóúñ]{3,})ar\?(?=\s|[.,;:!?)]|$)/g, '$1ará')
    .replace(/([a-zA-Záéíóúñ]{3,})er\?(?=\s|[.,;:!?)]|$)/g, '$1erá')
    .replace(/([a-zA-Záéíóúñ]{3,})ir\?(?=\s|[.,;:!?)]|$)/g, '$1irá')
    .replace(/([a-zA-Záéíóúñ]{3,})ar\?n(?=\s|[.,;:!?)]|$)/g, '$1arán')
    .replace(/([a-zA-Záéíóúñ]{3,})er\?n(?=\s|[.,;:!?)]|$)/g, '$1erán')
    .replace(/([a-zA-Záéíóúñ]{3,})ir\?n(?=\s|[.,;:!?)]|$)/g, '$1irán')
    .replace(/ver\?n(?=\s|[.,;:!?)]|$)/gi, 'verán')
    .replace(/(^|\s)est\?(?=\s|[.,;:!?]|$)/gi, '$1está')
    .replace(/(^|\s)est\?n(?=\s|[.,;:!?]|$)/gi, '$1están')

    // Palabras técnicas frecuentes
    .replace(/gesti\?n(?=\s|[.,;:!?)]|$)/gi, 'gestión')
    .replace(/bot\?n(?=\s|[.,;:!?)]|$)/gi, 'botón')
    .replace(/t\?cnic([oa]s?)(?=\s|[.,;:!?)]|$)/gi, 'técnic$1')
    .replace(/l\?gic([oa]s?)(?=\s|[.,;:!?)]|$)/gi, 'lógic$1')
    .replace(/c\?lcul([oa]s?)(?=\s|[.,;:!?)]|$)/gi, 'cálcul$1')
    .replace(/an\?lisis(?=\s|[.,;:!?)]|$)/gi, 'análisis')
    .replace(/anal\?tic([oa]s?)(?=\s|[.,;:!?)]|$)/gi, 'analític$1')
    .replace(/tecnol\?gic([oa]s?)(?=\s|[.,;:!?)]|$)/gi, 'tecnológic$1')
    .replace(/Tambi\?n(?=\s|[.,;:!?)]|$)/g, 'También')
    .replace(/tambi\?n(?=\s|[.,;:!?)]|$)/g, 'también')
    .replace(/Adem\?s(?=\s|[.,;:!?)]|$)/g, 'Además')
    .replace(/adem\?s(?=\s|[.,;:!?)]|$)/g, 'además')
    .replace(/seg\?n(?=\s|[.,;:!?)]|$)/gi, 'según')
    .replace(/clip \?\?/gi, 'clip 📎')
    .replace(/clip \?/gi, 'clip 📎')

    // Cualquier signo de interrogación que quedó como apertura antes de una mayúscula y que termina en ?
    .replace(/\?([A-ZÁÉÍÓÚ][^?!\n]+)\?/g, '¿$1?');
}

/**
 * Convierte Markdown a HTML formateado y seguro para renderizado en Nuxt/Vue.
 */
export function formatMarkdownToHtml(rawText?: string, options?: { isDark?: boolean }): string {
  if (!rawText) return "";
  const isDark = Boolean(options?.isDark);
  let text = parseHtmlToMarkdown(sanitizeCorruptedEncoding(rawText));

  // Desempaquetar preguntas en línea
  text = text.replace(/([:.]|\bcríticos\b)\s+(\([1-9]\)|\b[1-9]\.)\s+/gi, '$1\n\n$2 ');
  text = text.replace(/([?;])\s+(?:y\s+)?(\([2-9]\)|\b[2-9]\.)\s+/gi, '$1\n\n$2 ');

  // Separar en bloques por párrafos (doble salto de línea)
  const blocks = text.split(/\n\s*\n/);

  const htmlBlocks = blocks.map(block => {
    const trimmed = block.trim();
    if (!trimmed) return '';

    // Encabezados (# Titulo)
    if (/^###\s+(.+)$/m.test(trimmed)) {
      const headerCls = isDark ? 'font-bold text-white text-sm mt-3 mb-1' : 'font-bold text-slate-800 text-sm mt-3 mb-1';
      return trimmed.replace(/^###\s+(.+)$/gm, `<h4 class="${headerCls}">$1</h4>`);
    }
    if (/^##\s+(.+)$/m.test(trimmed)) {
      const headerCls = isDark ? 'font-bold text-white text-base mt-3 mb-1.5' : 'font-bold text-slate-900 text-base mt-3 mb-1.5';
      return trimmed.replace(/^##\s+(.+)$/gm, `<h3 class="${headerCls}">$1</h3>`);
    }
    if (/^#\s+(.+)$/m.test(trimmed)) {
      const headerCls = isDark ? 'font-bold text-white text-lg mt-4 mb-2' : 'font-bold text-slate-900 text-lg mt-4 mb-2';
      return trimmed.replace(/^#\s+(.+)$/gm, `<h2 class="${headerCls}">$1</h2>`);
    }

    // Listas con viñetas (- item o * item)
    const lines = trimmed.split('\n');
    const isBulletList = lines.every(l => /^\s*[-*•]\s+/.test(l));
    if (isBulletList) {
      const items = lines.map(l => {
        let content = l.replace(/^\s*[-*•]\s+/, '');
        content = parseInlineMarkdown(content, isDark);
        const liCls = isDark ? 'flex items-start gap-2 text-white' : 'flex items-start gap-2 text-slate-800';
        return `<li class="${liCls}"><span class="text-[#EB5F46] font-bold select-none leading-relaxed">•</span><span class="flex-1 leading-relaxed">${content}</span></li>`;
      }).join('');
      return `<ul class="my-2 space-y-1.5 pl-1">${items}</ul>`;
    }

    // Listas numeradas (1. item, (1) item)
    const isNumberedList = lines.every(l => /^\s*(?:\d+\.|\(\d+\))\s+/.test(l));
    if (isNumberedList) {
      const items = lines.map((l, idx) => {
        let content = l.replace(/^\s*(?:\d+\.|\(\d+\))\s+/, '');
        content = parseInlineMarkdown(content, isDark);
        const liCls = isDark ? 'flex items-start gap-2.5 text-white' : 'flex items-start gap-2.5 text-slate-800';
        return `<li class="${liCls}"><span class="w-5 h-5 rounded-md bg-[#FFF0ED] text-[#EB5F46] flex items-center justify-center text-[10px] font-bold shrink-0 border border-[#FCD9D2] mt-0.5">${idx + 1}</span><span class="flex-1 leading-relaxed">${content}</span></li>`;
      }).join('');
      return `<ul class="my-2 space-y-2 pl-1">${items}</ul>`;
    }

    // Párrafo normal con saltos de línea convertidos a <br />
    const parsedLines = lines.map(line => parseInlineMarkdown(line, isDark));
    const pCls = isDark ? 'leading-relaxed text-white my-1.5' : 'leading-relaxed text-slate-800 my-1.5';
    return `<p class="${pCls}">${parsedLines.join('<br />')}</p>`;
  });

  return htmlBlocks.filter(Boolean).join('');
}

function parseInlineMarkdown(str: string, isDark = false): string {
  let s = str;

  // Renderizar etiquetas [Adjunto: nombre_archivo] como pill visual interactivo
  s = s.replace(/\[Adjunto:\s*([^\]]+)\]/gi, (_match, filename) => {
    const chipCls = isDark
      ? 'inline-flex items-center gap-1.5 px-2.5 py-1 my-1 rounded-lg bg-white/10 text-white border border-white/20 font-mono text-[11px] font-semibold'
      : 'inline-flex items-center gap-1.5 px-2.5 py-1 my-1 rounded-lg bg-amber-50 text-amber-900 border border-amber-200 font-mono text-[11px] font-semibold';
    return `<span class="${chipCls}">📎 ${filename}</span>`;
  });

  // Negrita: **texto**
  const boldCls = isDark ? 'font-bold text-white' : 'font-bold text-slate-900';
  s = s.replace(/\*\*(.+?)\*\*/g, `<strong class="${boldCls}">$1</strong>`);

  // Limpiar asteriscos huérfanos o residuales
  s = s.replace(/^\s*\*\*\s*/, '').replace(/\s*\*\*\s*$/, '');

  // Cursiva: *texto*
  const emCls = isDark ? 'italic text-slate-200' : 'italic text-slate-700';
  s = s.replace(/(?<!\*)\*([^*]+)\*(?!\*)/g, `<em class="${emCls}">$1</em>`);

  // Código en línea: `texto`
  const codeCls = isDark
    ? 'bg-white/20 text-white text-xs px-1.5 py-0.5 rounded font-mono'
    : 'bg-slate-100 text-slate-800 text-xs px-1.5 py-0.5 rounded font-mono border border-slate-200';
  s = s.replace(/`([^`]+)`/g, `<code class="${codeCls}">$1</code>`);

  return s;
}

export function formatHtmlText(rawText?: string, fallback = ""): string {
  if (!rawText) return fallback;
  return parseInlineMarkdown(String(rawText).trim());
}
