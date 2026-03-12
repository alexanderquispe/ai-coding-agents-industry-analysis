# Bulk Fetch - GitHub Data Collection

Script para descargar commits y PRs de los 5 agentes de IA desde la GitHub Search API.

## Agentes soportados

| Agente | Tipo | Query | API endpoint |
|--------|------|-------|-------------|
| `claude` | commits | `"Co-Authored-By" "noreply@anthropic.com"` | `/search/commits` |
| `copilot` | PRs | `is:pr head:copilot` | `/search/issues` |
| `codex` | PRs | `is:pr head:codex` | `/search/issues` |
| `cursor` | PRs | `is:pr head:cursor` | `/search/issues` |
| `jules` | commits | `author:google-labs-jules[bot]` | `/search/commits` |

## Requisitos

```bash
pip install requests pandas tqdm
```

## Setup

1. Crear archivo `.env` en esta carpeta (no se sube a git):

```bash
# Un solo token
GH_TOKEN=ghp_xxxxxxx

# O multiples tokens separados por coma (recomendado, mas rapido)
GH_TOKENS=ghp_aaa,ghp_bbb,ghp_ccc
```

2. Cargar las variables de entorno:

```bash
# Linux/Mac
export $(cat .env | xargs)

# Windows PowerShell
Get-Content .env | ForEach-Object { $k,$v = $_ -split '=',2; Set-Item "env:$k" $v }
```

## Uso

```bash
# Fetch Claude commits de enero a marzo 2026
python fetch_bulk.py --agent claude --start 2026-01-01 --end 2026-03-11

# Fetch Copilot PRs
python fetch_bulk.py --agent copilot --start 2026-01-01 --end 2026-03-11

# Fetch todos los agentes (uno por uno)
for agent in claude copilot codex cursor jules; do
    python fetch_bulk.py --agent $agent --start 2026-01-01 --end 2026-03-11
done
```

### Opciones

| Flag | Default | Descripcion |
|------|---------|-------------|
| `--agent` | (requerido) | `claude`, `copilot`, `codex`, `cursor`, `jules` |
| `--start` | (requerido) | Fecha inicio `YYYY-MM-DD` |
| `--end` | (requerido) | Fecha fin `YYYY-MM-DD` |
| `--output-dir` | `output/` | Donde se guardan JSONL y Parquet |
| `--checkpoint-dir` | `checkpoints/` | Donde se guardan SHAs y manifest |

## Output

```
output/
  claude_commits.jsonl      # Datos crudos (1 JSON por linea)
  claude_commits.parquet    # Mismo dato en Parquet

checkpoints/
  seen_keys_Claude.txt      # SHAs unicos (para dedup entre runs)
  manifest_Claude.json      # Dias completados (para resume)
  run_log_Claude.jsonl      # Historial de corridas
```

## Checkpoint / Resume

El script guarda progreso automaticamente:

- **Cada 1000 items**: escribe JSONL + SHAs + manifest a disco
- **Cada dia completado**: marca el dia como `"complete"` en el manifest
- **Si se interrumpe**: al re-ejecutar salta los dias completos y retoma los parciales

Los SHAs evitan duplicados entre corridas. Un dia `"complete"` nunca se re-escanea.

## Como funciona

1. Divide el rango de fechas en dias individuales
2. Para cada dia, consulta el total de items en la API
3. Si hay <= 1000: descarga todo directo (hasta 10 paginas x 100 items)
4. Si hay > 1000: divide el dia en intervalos mas pequenos (6h -> binario -> minutos -> 10s)
5. Repite hasta que cada intervalo tenga <= 1000 items
6. Deduplicacion por SHA (commits) o PR ID (pull requests)

## Tokens

- Cada token permite 30 requests/minuto a la Search API
- Con N tokens: N x 30 req/min
- Recomendado: 6-12 tokens para velocidad optima (~86K-160K items/hora)
- Crear tokens en: GitHub > Settings > Developer settings > Personal access tokens
- Permisos necesarios: ninguno (acceso a repos publicos viene por defecto)

## Velocidades de referencia

| Tokens | Req/min | Items/hora aprox |
|--------|---------|-----------------|
| 1 | 30 | ~15K |
| 6 | 180 | ~86K |
| 12 | 360 | ~160K |
| 20 | 600 | ~280K (limite practico por IP) |
