# Transcriptor de Audio con Whisper

Herramienta de línea de comandos para transcribir archivos de audio largos usando el modelo Whisper-1 de OpenAI. El script divide automáticamente el audio en fragmentos manejables y procesa cada uno de forma secuencial.

## Características

- **División automática**: Fragmenta el audio original en trozos de duración configurable (por defecto 5 minutos)
- **Transcripción con Whisper-1**: Usa el modelo de OpenAI para transcripciones de alta calidad
- **Soporte multi-formato**: Compatible con `.m4a`, `.mp3`, `.wav` y otros formatos de audio
- **Procesamiento sin pérdida**: Utiliza FFmpeg con `copy codec` para dividir sin recodificar
- **Salida consolidada**: Todas las transcripciones se guardan en un único archivo de texto
- **Sistema de caché**: Evita re-transcribir fragmentos ya procesados (ahorro de tiempo y costos)
- **Reintentos automáticos**: Manejo inteligente de errores de red y rate limiting
- **Validación robusta**: Verifica archivos antes de procesar para evitar errores
- **Logging completo**: Sistema de logs para debugging y auditoría
- **Manejo de interrupciones**: Guarda progreso si el proceso se interrumpe
- **Resumen automático con IA**: Genera resúmenes estructurados de las transcripciones usando GPT
- **Modo interactivo**: Interfaz con menús navegables (↑↓ + Enter) sin necesidad de recordar flags CLI

## Requisitos

### Sistema
- macOS, Linux o Windows
- Python 3.8 o superior
- FFmpeg instalado y accesible en PATH

### Dependencias Python
- `openai` - Cliente oficial de OpenAI
- `tenacity` - Reintentos automáticos con backoff exponencial
- `python-dotenv` - Gestión de variables de entorno
- FFmpeg (herramienta de sistema, no paquete Python)

### API
- Clave de API de OpenAI con acceso al modelo Whisper-1

## Instalación

### 1. Clonar el repositorio

```bash
git clone <url-del-repositorio>
cd Transcriptor
```

### 2. Crear entorno virtual

```bash
python3 -m venv venv
source venv/bin/activate        # macOS/Linux
.\venv\Scripts\Activate.ps1     # Windows PowerShell
```

### 3. Instalar dependencias

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Para desarrollo (opcional):
```bash
pip install -r requirements-dev.txt
```

### 4. Instalar FFmpeg

**macOS (Homebrew):**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

**Windows:**
- Descarga desde [ffmpeg.org](https://ffmpeg.org/download.html)
- Añade el directorio `bin` al PATH del sistema

### 5. Verificar instalación de FFmpeg

```bash
ffmpeg -version
```

## Configuración

### Método 1: Archivo .env (Recomendado)

Crea un archivo `.env` en la raíz del proyecto basándote en `.env.example`:

```bash
cp .env.example .env
```

Edita el archivo `.env` y configura tu API key:

```bash
# .env
OPENAI_API_KEY=sk-proj-tu-clave-aquí

# Configuración opcional
CACHE_ENABLED=true
CACHE_DIR=.cache/transcriptions
LOG_LEVEL=INFO
LOG_FILE=transcriptor.log
DEFAULT_CHUNK_MINUTES=5
MAX_RETRY_ATTEMPTS=5
SUMMARY_MODEL=gpt-4o-mini
```

### Método 2: Variables de entorno

**macOS/Linux:**
```bash
export OPENAI_API_KEY="tu_clave_aquí"
```

**Windows PowerShell:**
```powershell
$Env:OPENAI_API_KEY="tu_clave_aquí"
```

**Forma permanente:**

```bash
# ~/.bashrc o ~/.zshrc
echo 'export OPENAI_API_KEY="tu_clave_aquí"' >> ~/.bashrc
source ~/.bashrc
```

## Uso

### Sintaxis básica

```bash
python split_and_transcribe.py <archivo_audio> [opciones]
```

### Parámetros

| Parámetro | Descripción | Por defecto |
|-----------|-------------|-------------|
| `audio_path` | Ruta al archivo de audio (obligatorio) | - |
| `--minutes, -m` | Duración de cada fragmento en minutos | `5` |
| `--outdir, -d` | Directorio para guardar fragmentos | `chunks` |
| `--output, -o` | Archivo de salida de transcripción | `transcripcion.txt` |
| `--no-cache` | Desactivar el uso de caché | Caché activado |
| `--keep-chunks` | Conservar fragmentos después de transcribir | Eliminar fragmentos |
| `--summary, -s` | Generar resumen automático de la transcripción | No generar resumen |
| `--summary-model` | Modelo GPT para generar resumen | `gpt-4o-mini` |

### Ejemplos

**Uso básico:**
```bash
python split_and_transcribe.py mi_audio.m4a
```

**Con fragmentos de 10 minutos:**
```bash
python split_and_transcribe.py mi_audio.m4a --minutes 10
```

**Especificando todos los parámetros:**
```bash
python split_and_transcribe.py consultoria.m4a \
  --minutes 5 \
  --outdir fragmentos \
  --output transcripcion_completa.txt
```

**Con caché desactivado:**
```bash
python split_and_transcribe.py mi_audio.m4a --no-cache
```

**Conservar fragmentos:**
```bash
python split_and_transcribe.py mi_audio.m4a --keep-chunks
```

**Con resumen automático:**
```bash
python split_and_transcribe.py mi_audio.m4a --summary
```

**Resumen con modelo específico:**
```bash
python split_and_transcribe.py mi_audio.m4a --summary --summary-model gpt-4o
```

**Combinando opciones (resumen + fragmentos conservados):**
```bash
python split_and_transcribe.py consultoria.m4a \
  --summary \
  --keep-chunks \
  --minutes 10
```

**Ayuda del comando:**
```bash
python split_and_transcribe.py --help
```

## Modo Interactivo

Si prefieres una experiencia guiada sin necesidad de recordar opciones CLI, puedes usar el modo interactivo con menús navegables:

### Iniciar modo interactivo

```bash
python transcriptor_interactive.py
```

### Características del modo interactivo

- **Navegación con flechas**: Usa ↑↓ para navegar entre opciones
- **Selección con Enter**: Confirma tu elección presionando Enter
- **Menús guiados**: Paso a paso para todas las configuraciones
- **Visualización de archivos**: Lista automática de archivos de audio disponibles
- **Confirmación visual**: Resumen de configuración antes de ejecutar
- **Sin flags que recordar**: Todo se configura mediante menús

### Flujo del modo interactivo

1. **Menú Principal**
   - Transcribir nuevo audio
   - Ver archivos en directorio
   - Información de uso
   - Salir

2. **Selección de archivo**
   - Lista de archivos .m4a, .mp3, .wav, etc. en el directorio actual
   - Opción para especificar ruta manualmente

3. **Configuración de opciones**
   - Duración de fragmentos (1, 3, 5, 10, 15, 30 min o personalizado)
   - ¿Generar resumen? (Sí/No)
   - Si resumen: Seleccionar modelo GPT
   - Opciones avanzadas (mantener fragmentos, desactivar caché, etc.)

4. **Confirmación**
   - Resumen visual de toda la configuración
   - Confirmación antes de procesar

5. **Procesamiento**
   - Indicadores de progreso en tiempo real
   - Resumen final con estadísticas

### Ejemplo de uso interactivo

```text
======================================================================
  🎙️  Transcriptor de Audio con Whisper-1
======================================================================

? Transcriptor de Audio - Menú Principal
  ▶ 🎙️  Transcribir nuevo audio
    📋 Ver archivos en directorio
    ℹ️  Información de uso
    🚪 Salir

? Selecciona un archivo de audio:
  ▶ producto-15-09-2025.m4a
    entrevista.mp3
    📁 Especificar ruta manualmente

? ¿Cuántos minutos por fragmento?
  ▶ 5
    10
    15

? ¿Deseas generar un resumen automático? (y/N) y

? ¿Qué modelo usar para el resumen?
  ▶ gpt-4o-mini (más económico)
    gpt-4o (balanceado)
    gpt-4 (legacy)

======================================================================
  Resumen de Configuración
======================================================================

📄 Archivo de entrada:     producto-15-09-2025.m4a
⏱️  Duración de fragmentos: 5 minutos
📝 Generar resumen:        Sí
🤖 Modelo de resumen:      gpt-4o-mini
📂 Directorio fragmentos:  chunks
💾 Archivo de salida:      transcripcion.txt
🗂️  Mantener fragmentos:    No
💿 Usar caché:             Sí

? ¿Proceder con la transcripción? (y/N) y
```

### Ventajas del modo interactivo

✅ **Fácil de usar**: No necesitas conocer opciones CLI
✅ **Sin errores de sintaxis**: Los menús evitan errores de tipeo
✅ **Validación en tiempo real**: Opciones inválidas no se pueden seleccionar
✅ **Descubrimiento de funciones**: Ves todas las opciones disponibles
✅ **Experiencia visual**: Interfaz limpia con colores y símbolos

### ¿Cuándo usar cada modo?

| Modo CLI (`split_and_transcribe.py`) | Modo Interactivo (`transcriptor_interactive.py`) |
|---------------------------------------|--------------------------------------------------|
| Scripts automatizados | Uso manual e interactivo |
| Integración con otros programas | Exploración de opciones |
| Comandos repetitivos guardados | Primera vez usando la herramienta |
| Pipelines de CI/CD | Configuración personalizada por sesión |

## Estructura de salida

Después de ejecutar el script, obtendrás:

```text
Transcriptor/
├── .cache/                    # Caché de transcripciones (opcional)
│   └── transcriptions/
│       ├── abc123...json
│       └── def456...json
├── chunks/                    # Fragmentos (si usas --keep-chunks)
│   ├── mi_audio_000.m4a
│   ├── mi_audio_001.m4a
│   └── mi_audio_002.m4a
├── transcripcion.txt          # Transcripción completa
├── transcripcion_resumen.txt  # Resumen (si usas --summary)
├── transcriptor.log           # Archivo de logs
└── split_and_transcribe.py
```

### Formato del archivo de transcripción

```text
======================================================================
Fragmento 1/3: mi_audio_000.m4a
======================================================================

[Texto transcrito del primer fragmento...]

======================================================================
Fragmento 2/3: mi_audio_001.m4a
======================================================================

[Texto transcrito del segundo fragmento...]
```

### Formato del archivo de resumen

El resumen generado con `--summary` incluye:

```text
======================================================================
📝 RESUMEN DE LA TRANSCRIPCIÓN
======================================================================

Generado con modelo: gpt-4o-mini
Tokens utilizados: 1234

======================================================================

## 1. RESUMEN EJECUTIVO

[2-3 párrafos que capturan la esencia completa de la transcripción]

## 2. PUNTOS CLAVE

- Punto importante 1
- Punto importante 2
- Punto importante 3
[...]

## 3. TEMAS PRINCIPALES

**Tema 1: [Nombre del tema]**
[Breve descripción]

**Tema 2: [Nombre del tema]**
[Breve descripción]

## 4. ACCIONES Y DECISIONES

- Acción o decisión 1
- Acción o decisión 2
[...]

## 5. CONCLUSIONES

[Síntesis final y reflexiones importantes]

======================================================================
```

### Ejemplo de salida en consola

```text
======================================================================
🎙️  Transcriptor de Audio con Whisper-1
======================================================================
✓ Archivo de audio validado: producto.m4a

📂 Dividiendo audio en fragmentos de 5 minutos...
✓ Audio dividido en 6 fragmentos

🎯 Transcribiendo 6 fragmentos...

[1/6] 🔊 Transcribiendo producto_000.m4a...
          ✓ Transcripción exitosa
[2/6] 🔊 Transcribiendo producto_001.m4a...
          ✓ Recuperado del caché
[3/6] 🔊 Transcribiendo producto_002.m4a...
          ✓ Transcripción exitosa

======================================================================
📝 Generando resumen de la transcripción...
======================================================================
✓ Resumen generado exitosamente
  Modelo usado: gpt-4o-mini
  Tokens usados: 1542

======================================================================
📊 Resumen de la transcripción
======================================================================
✓ Transcripciones exitosas: 4
💾 Recuperadas del caché:    2

📄 Transcripción guardada en: transcripcion.txt
📝 Resumen guardado en:       transcripcion_resumen.txt
======================================================================
```

## Cómo funciona

1. **Validación de entrada**: Verifica existencia, formato, tamaño y validez del archivo con `ffprobe`
2. **Limpieza previa**: Elimina directorios y archivos de salida anteriores
3. **Inicialización**: Configura cliente OpenAI y sistema de caché
4. **División**: Usa FFmpeg para dividir el audio en fragmentos sin recodificar
5. **Transcripción con caché**:
   - Verifica si el fragmento ya está en caché
   - Si está en caché, recupera la transcripción (instantáneo)
   - Si no, transcribe con Whisper-1 y guarda en caché
   - Reintentos automáticos en caso de errores de red
6. **Consolidación**: Guarda todas las transcripciones en un archivo único
7. **Generación de resumen (opcional)**: Si se usa `--summary`, genera un resumen estructurado con GPT
8. **Limpieza**: Elimina fragmentos temporales (opcional con `--keep-chunks`)

## Personalización

### Cambiar el modelo de Whisper

Edita la función `transcribe_audio()` en [split_and_transcribe.py](split_and_transcribe.py):

```python
resp = client.audio.transcriptions.create(
    file=audio_file,
    model="whisper-1",  # Cambiar si hay otros modelos disponibles
    language="es"       # Especificar idioma (opcional)
)
```

### Generar subtítulos en lugar de texto

```python
resp = client.audio.transcriptions.create(
    file=audio_file,
    model="whisper-1",
    response_format="srt"  # o "vtt" para WebVTT
)
```

### Procesar múltiples archivos

```bash
for file in *.m4a; do
  python split_and_transcribe.py "$file" --output "${file%.m4a}.txt"
done
```

## Solución de problemas

### Error: "No se encontró OPENAI_API_KEY en el entorno"

Verifica que la variable de entorno esté configurada:
```bash
echo $OPENAI_API_KEY  # macOS/Linux
echo $Env:OPENAI_API_KEY  # Windows PowerShell
```

### Error: "ffmpeg: command not found"

FFmpeg no está instalado o no está en el PATH. Sigue las instrucciones de instalación de FFmpeg.

### Error: "Rate limit exceeded"

Has excedido los límites de la API de OpenAI. Considera:
- Aumentar el tiempo entre peticiones
- Reducir la duración de los fragmentos
- Verificar tu plan de OpenAI

### Transcripciones con errores

Si la calidad de transcripción es baja:
- Verifica la calidad del audio original
- Especifica el idioma en el parámetro `language`
- Prueba con fragmentos más pequeños (2-3 minutos)

## Costos

### Transcripción (Whisper-1)

La API de Whisper-1 tiene un costo de **$0.006 por minuto de audio** (aproximado, verificar precios actuales en [OpenAI Pricing](https://openai.com/pricing)).

**Ejemplo de cálculo:**
- Audio de 60 minutos = $0.36 USD
- Audio de 120 minutos = $0.72 USD

### Resumen (GPT)

Si usas la opción `--summary`, se añade el costo del modelo GPT utilizado:

**gpt-4o-mini** (recomendado para resúmenes):
- Entrada: $0.150 por 1M tokens
- Salida: $0.600 por 1M tokens
- Costo típico por resumen: **$0.001 - $0.005 USD**

**gpt-4o**:
- Entrada: $2.50 por 1M tokens
- Salida: $10.00 por 1M tokens
- Costo típico por resumen: **$0.02 - $0.10 USD**

**Costo total estimado** (60 min de audio + resumen):
- Con gpt-4o-mini: ~$0.36 - $0.37 USD
- Con gpt-4o: ~$0.38 - $0.46 USD

## Contribuciones

Las contribuciones son bienvenidas. Para contribuir:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -m 'Añade nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT. Consulta el archivo `LICENSE` para más detalles.

## Recursos adicionales

- [Documentación de OpenAI Whisper](https://platform.openai.com/docs/guides/speech-to-text)
- [Documentación de FFmpeg](https://ffmpeg.org/documentation.html)
- [API Reference de OpenAI](https://platform.openai.com/docs/api-reference)

