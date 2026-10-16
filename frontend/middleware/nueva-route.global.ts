export default defineNuxtRouteMiddleware((to) => {
  if (to.path.startsWith('/nueva/') && to.path !== '/nueva/') {
    const id = to.path.replace(/^\/nueva\//, '');
    if (id) {
      return navigateTo(`/nueva?id=${id}`);
    }
  }
});
