const fs = require("fs");
const path = require("path");
const ts = require("typescript");
const { execSync } = require("child_process");

const tsPath = path.join(__dirname, "..", "generated", "ts", "health.ts");
const pyPath = path.join(__dirname, "..", "generated", "py", "health.py");

function assertFileExists(filePath) {
  if (!fs.existsSync(filePath)) {
    throw new Error(`Missing generated file: ${filePath}`);
  }
}

function validateTypeScript(filePath) {
  const source = fs.readFileSync(filePath, "utf8");
  const result = ts.transpileModule(source, {
    compilerOptions: { module: ts.ModuleKind.ESNext }
  });

  if (result.diagnostics && result.diagnostics.length > 0) {
    throw new Error("TypeScript diagnostics found during validation");
  }
}

function validatePython(filePath) {
  execSync(`python -m py_compile "${filePath}"`, { stdio: "inherit" });
}

try {
  assertFileExists(tsPath);
  assertFileExists(pyPath);
  validateTypeScript(tsPath);
  validatePython(pyPath);
  console.log("Generated files validated successfully.");
} catch (error) {
  console.error(error);
  process.exit(1);
}
