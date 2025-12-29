const { execSync } = require("child_process");
const path = require("path");

function generate() {
  const schemaPath = path.join(__dirname, "..", "schema", "health.json");
  const outputPath = path.join(__dirname, "..", "generated", "py", "health.py");

  execSync(
    `python -m datamodel_code_generator --input "${schemaPath}" --output "${outputPath}" --input-file-type jsonschema`,
    { stdio: "inherit" }
  );
}

try {
  generate();
} catch (error) {
  console.error(error);
  process.exit(1);
}
