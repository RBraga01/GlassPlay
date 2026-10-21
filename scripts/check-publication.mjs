import { assertPublication } from './publication-policy.mjs';

try {
  console.log(JSON.stringify({ result: 'PASS', ...assertPublication('dist') }, null, 2));
} catch (error) {
  console.error(error.message);
  process.exitCode = 1;
}
