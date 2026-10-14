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
 * Convierte Markdown a HTML formateado y seguro para renderizado en Nuxt/Vue.
 */
export function formatMarkdownToHtml(rawText?: string): string {
  if (!rawText) return "";
  let text = parseHtmlToMarkdown(String(rawText));

  // Desempaquetar preguntas en línea
  text = text.replace(/([:.]|\bcríticos\b)\s+(\([1-9]\)|\b[1-9]\.)\s+/gi, '$1\n\n$2 ');
  text = text.replace(/([?;])\s+(?:y\s+)?(\([2-9]\)|\b[2-9]\.)\s+/gi, '$1\n\n$2 ');

  // Escapar HTML no deseado antes de parsear formato
  const escapeHtml = (str: string) =>
    str.replace(/&/g, '&amp;')
       .replace(/</g, '&lt;')
       .replace(/>/g, '&gt;');

  // Separar en bloques por párrafos (doble salto de línea)
  const blocks = text.split(/\n\s*\n/);

  const htmlBlocks = blocks.map(block => {
    const trimmed = block.trim();
    if (!trimmed) return '';

    // Encabezados (# Titulo)
    if (/^###\s+(.+)$/m.test(trimmed)) {
      return trimmed.replace(/^###\s+(.+)$/gm, '<h4 class="font-bold text-slate-800 text-sm mt-3 mb-1">$1</h4>');
    }
    if (/^##\s+(.+)$/m.test(trimmed)) {
      return trimmed.replace(/^##\s+(.+)$/gm, '<h3 class="font-bold text-slate-900 text-base mt-3 mb-1.5">$1</h3>');
    }
    if (/^#\s+(.+)$/m.test(trimmed)) {
      return trimmed.replace(/^#\s+(.+)$/gm, '<h2 class="font-bold text-slate-900 text-lg mt-4 mb-2">$1</h2>');
    }

    // Listas con viñetas (- item o * item)
    const lines = trimmed.split('\n');
    const isBulletList = lines.every(l => /^\s*[-*•]\s+/.test(l));
    if (isBulletList) {
      const items = lines.map(l => {
        let content = l.replace(/^\s*[-*•]\s+/, '');
        content = parseInlineMarkdown(content);
        return `<li class="flex items-start gap-2 text-slate-800"><span class="text-[#EB5F46] font-bold select-none leading-relaxed">•</span><span class="flex-1 leading-relaxed">${content}</span></li>`;
      }).join('');
      return `<ul class="my-2 space-y-1.5 pl-1">${items}</ul>`;
    }

    // Listas numeradas (1. item, (1) item)
    const isNumberedList = lines.every(l => /^\s*(?:\d+\.|\(\d+\))\s+/.test(l));
    if (isNumberedList) {
      const items = lines.map((l, idx) => {
        let content = l.replace(/^\s*(?:\d+\.|\(\d+\))\s+/, '');
        content = parseInlineMarkdown(content);
        return `<li class="flex items-start gap-2.5 text-slate-800"><span class="w-5 h-5 rounded-md bg-[#FFF0ED] text-[#EB5F46] flex items-center justify-center text-[10px] font-bold shrink-0 border border-[#FCD9D2] mt-0.5">${idx + 1}</span><span class="flex-1 leading-relaxed">${content}</span></li>`;
      }).join('');
      return `<ul class="my-2 space-y-2 pl-1">${items}</ul>`;
    }

    // Párrafo normal con saltos de línea convertidos a <br />
    const parsedLines = lines.map(line => parseInlineMarkdown(line));
    return `<p class="leading-relaxed text-slate-800 my-1.5">${parsedLines.join('<br />')}</p>`;
  });

  return htmlBlocks.filter(Boolean).join('');
}

function parseInlineMarkdown(str: string): string {
  let s = str;

  // Negrita: **texto** -> <strong class="font-bold text-slate-900">texto</strong>
  s = s.replace(/\*\*(.+?)\*\*/g, '<strong class="font-semibold text-slate-900">$1</strong>');

  // Limpiar asteriscos huérfanos o residuales
  s = s.replace(/^\s*\*\*\s*/, '').replace(/\s*\*\*\s*$/, '');

  // Cursiva: *texto* -> <em class="italic text-slate-700">texto</em>
  s = s.replace(/(?<!\*)\*([^*]+)\*(?!\*)/g, '<em class="italic text-slate-700">$1</em>');

  // Código en línea: `texto`
  s = s.replace(/`([^`]+)`/g, '<code class="bg-slate-100 text-slate-800 text-xs px-1.5 py-0.5 rounded font-mono border border-slate-200">$1</code>');

  return s;
}

export function formatHtmlText(rawText?: string, fallback = ""): string {
  if (!rawText) return fallback;
  return parseInlineMarkdown(String(rawText).trim());
}
