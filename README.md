Transcriptor de Audio con Whisper y Pydub

Este proyecto permite dividir un archivo de audio en fragmentos de 5 minutos y transcribir cada uno usando el modelo whisper-1 de OpenAI. Está diseñado para ejecutarse en macOS dentro de un entorno virtual de Python.

📋 Características

División automática: parte el audio original en trozos de duración configurable.

Transcripción en bucle: procesa cada fragmento secuencialmente y concatena los resultados.

Soporte para M4A y otros formatos (.m4a, .mp3, .wav, etc.) gracias a FFmpeg.

Salida única: toda la transcripción se guarda en un solo fichero de texto.

🛠️ Requisitos

macOS, Linux o Windows.

Python 3.9+.

Entorno virtual de Python (venv).

FFmpeg instalado y accesible en el PATH.

Clave de API de OpenAI con permisos para Whisper.

⚙️ Instalación

Clona o descarga este repositorio.

En la raíz del proyecto, crea y activa un entorno virtual:

python3 -m venv venv
source venv/bin/activate        # macOS/Linux
.\venv\Scripts\Activate.ps1   # Windows PowerShell

Actualiza pip (opcional):

pip install --upgrade pip

Instala las dependencias:

pip install pydub openai

Instala FFmpeg si no lo tienes:

macOS (Homebrew):

brew install ffmpeg

Ubuntu/Debian:

sudo apt-get update
sudo apt-get install ffmpeg

Windows: descarga desde ffmpeg.org y añade al PATH.

🔑 Configuración

Exporta tu clave de API de OpenAI en el entorno:

export OPENAI_API_KEY="tu_clave_aquí"       # macOS/Linux
$Env:OPENAI_API_KEY="tu_clave_aquí"         # Windows PowerShell

🚀 Uso

Ejecuta el script principal con los parámetros deseados:

python split_and_transcribe.py <archivo_audio> \
  --minutes 5    \
  --outdir chunks \
  --output transcripcion.txt

<archivo_audio>: ruta al archivo de audio (ej. consultoria.m4a).

--minutes: duración en minutos de cada fragmento (por defecto 5).

--outdir: carpeta donde se guardan los fragmentos generados.

--output: archivo de salida con la transcripción completa.

Ejemplo completo:

python split_and_transcribe.py consultoria.m4a --minutes 5 --outdir trozos --output mi_transcripcion.txt

Al finalizar, tendrás:

Carpeta trozos/ con los fragmentos de audio (consultoria_00.mp3, consultoria_01.mp3, ...).

Archivo mi_transcripcion.txt con las transcripciones de cada fragmento.

🔧 Personalización

Formato de salida: puedes generar subtítulos añadiendo response_format="srt" o "vtt" al método de transcripción.

Duración de fragmentos: ajusta --minutes al valor que necesites.

Procesamiento masivo: integra el script en un pipeline o añade paralelización para grandes volúmenes de audio.

🤝 Contribuciones

¡Las contribuciones son bienvenidas! Abre un issue o un pull request para sugerir mejoras o reportar errores.

📄 Licencia

Este proyecto está bajo la Licencia MIT. Consulta LICENSE para más detalles.

