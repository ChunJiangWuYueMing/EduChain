/**
 * EduChain 合约编译脚本
 * 用法: node scripts/compile.js
 * 输出: backend/compiled/ 目录下的 ABI + Bytecode JSON 文件
 */

const solc = require("solc");
const fs = require("fs");
const path = require("path");

const CONTRACTS_DIR = path.join(__dirname, "..", "contracts");
const OUTPUT_DIR = path.join(__dirname, "..", "backend", "compiled");

// 需要编译的合约文件
const CONTRACT_FILES = [
    "EduToken.sol",
    "MaterialRegistry.sol",
    "DownloadLog.sol",
];

// 读取合约源码
function readContract(filename) {
    return fs.readFileSync(path.join(CONTRACTS_DIR, filename), "utf8");
}

// import 回调：解析 @openzeppelin 和本地 import
function findImports(importPath) {
    // OpenZeppelin 从 node_modules 读取
    if (importPath.startsWith("@openzeppelin/")) {
        const fullPath = path.join(__dirname, "..", "node_modules", importPath);
        if (fs.existsSync(fullPath)) {
            return { contents: fs.readFileSync(fullPath, "utf8") };
        }
        return { error: `File not found: ${fullPath}` };
    }
    // 本地合约
    const fullPath = path.join(CONTRACTS_DIR, importPath);
    if (fs.existsSync(fullPath)) {
        return { contents: fs.readFileSync(fullPath, "utf8") };
    }
    return { error: `File not found: ${fullPath}` };
}

// 构建 solc 输入
const sources = {};
for (const file of CONTRACT_FILES) {
    sources[file] = { content: readContract(file) };
}

const input = {
    language: "Solidity",
    sources,
    settings: {
        evmVersion: "shanghai",  // 必须与 Ganache hardfork 一致
        optimizer: { enabled: true, runs: 200 },
        viaIR: true,
        outputSelection: {
            "*": {
                "*": ["abi", "evm.bytecode.object"],
            },
        },
    },
};

console.log("编译合约...");
const output = JSON.parse(solc.compile(JSON.stringify(input), { import: findImports }));

// 检查错误
if (output.errors) {
    let hasError = false;
    for (const err of output.errors) {
        if (err.severity === "error") {
            console.error("编译错误:", err.formattedMessage);
            hasError = true;
        } else {
            console.warn(" 警告:", err.formattedMessage);
        }
    }
    if (hasError) {
        process.exit(1);
    }
}

// 输出 ABI + Bytecode
fs.mkdirSync(OUTPUT_DIR, { recursive: true });

for (const file of CONTRACT_FILES) {
    const contractName = file.replace(".sol", "");
    const compiled = output.contracts[file][contractName];

    if (!compiled) {
        console.error(`未找到合约 ${contractName}，请检查合约名是否与文件名一致`);
        continue;
    }

    const artifact = {
        contractName,
        abi: compiled.abi,
        bytecode: "0x" + compiled.evm.bytecode.object,
    };

    const outPath = path.join(OUTPUT_DIR, `${contractName}.json`);
    fs.writeFileSync(outPath, JSON.stringify(artifact, null, 2));
    console.log(`${contractName} → ${outPath}`);
}

console.log("\n编译完成！ABI 和 Bytecode 已输出到 backend/compiled/");