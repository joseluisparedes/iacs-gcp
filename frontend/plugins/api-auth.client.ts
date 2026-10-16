export default defineNuxtPlugin((_nuxtApp) => {
  if (process.client) {
    const originalFetch = globalThis.$fetch;
    globalThis.$fetch = originalFetch.create({
      onRequest({ options }) {
        try {
          const token = localStorage.getItem('iacs_token');
          if (token) {
            options.headers = options.headers || {};
            if (options.headers instanceof Headers) {
              options.headers.set('Authorization', `Bearer ${token}`);
            } else if (Array.isArray(options.headers)) {
              options.headers.push(['Authorization', `Bearer ${token}`]);
            } else {
              (options.headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
            }
          }
        } catch (e) {
          console.error('[IACS Auth Plugin] Error attaching token to request:', e);
        }
      },
    });
  }
});
