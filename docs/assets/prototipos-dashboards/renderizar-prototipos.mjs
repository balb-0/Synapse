#!/usr/bin/env node
/**
 * renderizar-prototipos.mjs
 *
 * Script Playwright em Node.js ES Module para capturar os protótipos de dashboard
 * em resoluções desktop (1600x1000 @ dsf=2) e mobile para QA (390x844 @ dsf=2).
 *
 * Requisitos:
 * - Executar via npx / Node
 * - Iniciar ou reutilizar servidor HTTP local de forma reprodutível
 * - Capturar 4 visões desktop (d01..d04) e 4 visões mobile para QA (d01..d04)
 * - Checar e falhar em caso de erros no console da página
 * - Salvar em imagens/ com nomes claros
 * - Sem criar package.json / node_modules na pasta do projeto
 */

import { spawn } from 'child_process';
import { existsSync, mkdirSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';
import { createRequire } from 'module';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

let chromium;
try {
  const pw = await import('playwright');
  chromium = pw.chromium;
} catch {
  const modulePath = process.env.PLAYWRIGHT_MODULE;
  if (modulePath) {
    const packagePath = modulePath.endsWith('package.json')
      ? modulePath
      : resolve(modulePath, 'package.json');
    if (existsSync(packagePath)) {
      const require = createRequire(packagePath);
      const packageDirectory = dirname(packagePath);
      chromium = require(packageDirectory).chromium;
    }
  }
}

if (!chromium) {
  console.error("Erro: Playwright não localizado. Instale-o fora do repositório e informe PLAYWRIGHT_MODULE.");
  process.exit(1);
}

const PORT = Number(process.env.PROTOTIPOS_PORT || 8089);
const BASE_URL = `http://localhost:${PORT}/index.html`;
const IMAGES_DIR = resolve(__dirname, 'imagens');

if (!existsSync(IMAGES_DIR)) {
  mkdirSync(IMAGES_DIR, { recursive: true });
}

function startServer() {
  return new Promise((resolveServer, rejectServer) => {
    const serverProc = spawn('python3', ['-m', 'http.server', String(PORT)], {
      cwd: __dirname,
      stdio: 'ignore'
    });

    setTimeout(() => {
      resolveServer(serverProc);
    }, 1200);

    serverProc.on('error', (err) => {
      rejectServer(err);
    });
  });
}

async function run() {
  console.log("Iniciando servidor HTTP local na porta", PORT, "...");
  const serverProc = await startServer();

  let hasConsoleErrors = false;
  const consoleErrorLogs = [];

  try {
    console.log("Iniciando navegador Chromium via Playwright...");
    const browser = await chromium.launch({
      headless: true,
      executablePath: process.env.CHROMIUM_EXECUTABLE || undefined
    });

    const views = [
      { id: 'd01', hash: '#d01', tabId: '#tab-d01', name: 'operacao' },
      { id: 'd02', hash: '#d02', tabId: '#tab-d02', name: 'participacao' },
      { id: 'd03', hash: '#d03', tabId: '#tab-d03', name: 'resultados' },
      { id: 'd04', hash: '#d04', tabId: '#tab-d04', name: 'qualidade' }
    ];

    // Capturar desktop (1600x1000 @ dsf=2)
    console.log("\n--- Capturando visualizações desktop (1600x1000 @ dsf 2) ---");
    const desktopContext = await browser.newContext({
      viewport: { width: 1600, height: 1000 },
      deviceScaleFactor: 2
    });

    for (const v of views) {
      const page = await desktopContext.newPage();
      page.on('console', msg => {
        if (msg.type() === 'error') {
          hasConsoleErrors = true;
          consoleErrorLogs.push(`[Erro de console no desktop] ${msg.text()}`);
        }
      });
      page.on('pageerror', err => {
        hasConsoleErrors = true;
        consoleErrorLogs.push(`[Erro de página no desktop] ${err.message}`);
      });

      const url = `${BASE_URL}${v.hash}`;
      console.log(`Navegando no desktop para: ${url}`);
      await page.goto(url, { waitUntil: 'networkidle' });
      await page.click(v.tabId);
      await page.waitForTimeout(300);

      const imgPath = resolve(IMAGES_DIR, `dashboard-${v.name}.png`);
      await page.screenshot({ path: imgPath, fullPage: false });
      console.log(`  -> Salvo: imagens/dashboard-${v.name}.png`);
      await page.close();
    }
    await desktopContext.close();

    // Capturar mobile para QA (390x844 @ dsf=2)
    console.log("\n--- Capturando visualizações mobile para QA (390x844 @ dsf 2) ---");
    const mobileContext = await browser.newContext({
      viewport: { width: 390, height: 844 },
      deviceScaleFactor: 2,
      isMobile: true,
      hasTouch: true
    });

    for (const v of views) {
      const page = await mobileContext.newPage();
      page.on('console', msg => {
        if (msg.type() === 'error') {
          hasConsoleErrors = true;
          consoleErrorLogs.push(`[Erro de console no mobile] ${msg.text()}`);
        }
      });
      page.on('pageerror', err => {
        hasConsoleErrors = true;
        consoleErrorLogs.push(`[Erro de página no mobile] ${err.message}`);
      });

      const url = `${BASE_URL}${v.hash}`;
      console.log(`Navegando no mobile para QA: ${url}`);
      await page.goto(url, { waitUntil: 'networkidle' });
      await page.click(v.tabId);
      await page.waitForTimeout(300);

      const overflowAudit = await page.evaluate(() => {
        const limite = document.documentElement.clientWidth;
        const elementos = Array.from(document.querySelectorAll('body *'))
          .filter(elemento => {
            const retangulo = elemento.getBoundingClientRect();
            return retangulo.right > limite + 1 || retangulo.left < -1;
          })
          .slice(0, 8)
          .map(elemento => ({
            tag: elemento.tagName.toLowerCase(),
            id: elemento.id,
            classe: elemento.className,
            esquerda: Math.round(elemento.getBoundingClientRect().left),
            direita: Math.round(elemento.getBoundingClientRect().right)
          }));
        return {
          pixels: document.documentElement.scrollWidth - limite,
          elementos
        };
      });
      if (overflowAudit.pixels > 1) {
        throw new Error(
          `Transbordo horizontal de ${overflowAudit.pixels}px na visão mobile ${v.id}: ` +
          JSON.stringify(overflowAudit.elementos)
        );
      }

      const imgPath = resolve(IMAGES_DIR, `dashboard-${v.name}-mobile.png`);
      await page.screenshot({ path: imgPath, fullPage: true });
      console.log(`  -> Salvo: imagens/dashboard-${v.name}-mobile.png`);
      await page.close();
    }
    await mobileContext.close();
    await browser.close();

    if (hasConsoleErrors) {
      console.error("\nFALHA: Erros detectados no console do navegador:");
      consoleErrorLogs.forEach(log => console.error(log));
      process.exitCode = 1;
    } else {
      console.log("\nSUCESSO: Todas as 8 capturas foram geradas com sucesso sem erros de console!");
    }

  } catch (err) {
    console.error("\nERRO na renderização dos protótipos:", err);
    process.exitCode = 1;
  } finally {
    serverProc.kill();
  }
}

run();
