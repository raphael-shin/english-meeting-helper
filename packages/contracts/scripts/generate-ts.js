const fs = require("fs");
const path = require("path");
const { compileFromFile } = require("json-schema-to-typescript");

async function generate() {
  const schemaPath = path.join(__dirname, "..", "schema", "health.json");
  const outputPath = path.join(__dirname, "..", "generated", "ts", "health.ts");

  const ts = await compileFromFile(schemaPath, {
    bannerComment: "/* eslint-disable */"
  });

  fs.writeFileSync(outputPath, ts);
  console.log(`Generated ${outputPath}`);
}

generate().catch((error) => {
  console.error(error);
  process.exit(1);
});
