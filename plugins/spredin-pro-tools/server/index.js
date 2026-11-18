// Entry point Claude Desktop runs (manifest.json → server.mcp_config).
// Everything is in connector.js, so the tests can load its parts on their own.
import { main } from './connector.js';

main();
