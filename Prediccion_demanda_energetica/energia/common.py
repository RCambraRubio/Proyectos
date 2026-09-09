import json
from datetime import datetime, timezone
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[1]

def leer_json(ruta):
    return json.loads(Path(ruta).read_text(encoding='utf-8-sig'))

def escribir_json(ruta, valor):
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    temporal = ruta.with_suffix(ruta.suffix + '.tmp')
    temporal.write_text(json.dumps(valor, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
    temporal.replace(ruta)

def ahora():
    return datetime.now(timezone.utc).isoformat()
