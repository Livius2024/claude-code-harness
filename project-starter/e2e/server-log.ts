import path from 'node:path';

// Where playwright.config.ts sends the app's stdout and stderr, so fixtures.ts can read it.
export const SERVER_LOG = path.join(__dirname, 'server.log');
