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

**Ayuda del comando:**
```bash
python split_and_transcribe.py --help
```

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
📊 Resumen de la transcripción
======================================================================
✓ Transcripciones exitosas: 4
💾 Recuperadas del caché:    2

📄 Transcripción guardada en: transcripcion.txt
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
7. **Limpieza**: Elimina fragmentos temporales (opcional con `--keep-chunks`)

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

La API de Whisper-1 tiene un costo de **$0.006 por minuto de audio** (aproximado, verificar precios actuales en [OpenAI Pricing](https://openai.com/pricing)).

**Ejemplo de cálculo:**
- Audio de 60 minutos = $0.36 USD
- Audio de 120 minutos = $0.72 USD

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

