// A non-local API origin the guard must watch. playwright.config.ts lists it in
// APP_ORIGINS; guard.spec.ts answers it with page routing.
export const SELFTEST_API_ORIGIN = 'http://api.guard-selftest.test';
