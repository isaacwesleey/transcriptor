#!/usr/bin/env python3

import os
import sys
import shutil
import subprocess
import argparse
import logging
import hashlib
import json
from pathlib import Path
from typing import Optional
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from dotenv import load_dotenv

# Cargar variables de entorno desde .env si existe
load_dotenv()

# Configurar logging
def setup_logger() -> logging.Logger:
    """Configura el sistema de logging."""
    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_file = os.getenv("LOG_FILE", "transcriptor.log")

    logger = logging.getLogger("transcriptor")
    logger.setLevel(getattr(logging, log_level))

    # Formato del log
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Handler para consola
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Handler para archivo
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

logger = setup_logger()

# Sistema de caché
class TranscriptionCache:
    """Maneja el caché de transcripciones para evitar re-procesar fragmentos."""

    def __init__(self, cache_dir: str = ".cache/transcriptions"):
        self.cache_dir = Path(cache_dir)
        self.enabled = os.getenv("CACHE_ENABLED", "true").lower() == "true"

        if self.enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Caché habilitado en: {self.cache_dir}")

    def _get_file_hash(self, file_path: str) -> str:
        """Calcula el hash SHA256 de un archivo."""
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hasher.update(chunk)
        return hasher.hexdigest()

    def get(self, chunk_path: str) -> Optional[str]:
        """Recupera una transcripción del caché si existe."""
        if not self.enabled:
            return None

        try:
            file_hash = self._get_file_hash(chunk_path)
            cache_file = self.cache_dir / f"{file_hash}.json"

            if cache_file.exists():
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"Transcripción recuperada del caché: {chunk_path}")
                    return data['transcription']
        except Exception as e:
            logger.warning(f"Error al leer caché para {chunk_path}: {e}")

        return None

    def set(self, chunk_path: str, transcription: str):
        """Guarda una transcripción en el caché."""
        if not self.enabled:
            return

        try:
            file_hash = self._get_file_hash(chunk_path)
            cache_file = self.cache_dir / f"{file_hash}.json"

            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'file_hash': file_hash,
                    'chunk_path': chunk_path,
                    'transcription': transcription
                }, f, indent=2, ensure_ascii=False)

            logger.debug(f"Transcripción guardada en caché: {chunk_path}")
        except Exception as e:
            logger.warning(f"Error al guardar en caché {chunk_path}: {e}")

# Validación de archivos
def validate_audio_file(file_path: str) -> tuple[bool, str]:
    """
    Valida que el archivo de audio sea válido.
    Retorna (es_válido, mensaje_error)
    """
    SUPPORTED_FORMATS = {'.mp3', '.m4a', '.wav', '.flac', '.ogg', '.aac', '.wma'}
    MAX_FILE_SIZE_GB = 2

    path = Path(file_path)

    # Verificar que existe
    if not path.exists():
        return False, f"El archivo no existe: {file_path}"

    # Verificar que es un archivo
    if not path.is_file():
        return False, f"La ruta no es un archivo: {file_path}"

    # Verificar formato
    if path.suffix.lower() not in SUPPORTED_FORMATS:
        return False, f"Formato no soportado: {path.suffix}. Formatos válidos: {', '.join(SUPPORTED_FORMATS)}"

    # Verificar tamaño
    size_gb = path.stat().st_size / (1024 ** 3)
    if size_gb > MAX_FILE_SIZE_GB:
        return False, f"Archivo muy grande: {size_gb:.2f} GB (máximo: {MAX_FILE_SIZE_GB} GB)"

    # Verificar que ffmpeg puede leerlo
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', str(path)],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0 or not result.stdout.strip():
            return False, "El archivo de audio está corrupto o no es válido"

        duration = float(result.stdout.strip())
        logger.info(f"Audio validado: {file_path} (duración: {duration/60:.2f} minutos)")

    except subprocess.TimeoutExpired:
        return False, "Timeout al validar el archivo con ffprobe"
    except Exception as e:
        return False, f"Error al validar el audio: {e}"

    return True, "OK"


def clean_outputs(
    output_file: str = "transcripcion.txt",
    chunks_dir: str = "chunks",
    cache_dir: str = ".cache/transcriptions",
    log_file: str = "transcriptor.log",
    verbose: bool = True
) -> dict:
    """
    Limpia los archivos generados por ejecuciones anteriores.

    Args:
        output_file: Archivo de transcripción principal
        chunks_dir: Directorio de fragmentos de audio
        cache_dir: Directorio de caché
        log_file: Archivo de logs
        verbose: Si True, imprime mensajes de progreso

    Returns:
        dict con estadísticas de limpieza
    """
    stats = {"deleted_files": 0, "deleted_dirs": 0, "errors": []}

    # Archivos a eliminar
    files_to_delete = [
        output_file,
        output_file.replace(".txt", "_resumen.txt"),
        log_file,
    ]

    # Directorios a eliminar
    dirs_to_delete = [chunks_dir, cache_dir]

    # Eliminar archivos
    for file_path in files_to_delete:
        if os.path.isfile(file_path):
            try:
                os.remove(file_path)
                stats["deleted_files"] += 1
                if verbose:
                    print(f"  ✓ Eliminado: {file_path}")
                logger.info(f"Archivo eliminado: {file_path}")
            except Exception as e:
                stats["errors"].append(f"{file_path}: {e}")
                if verbose:
                    print(f"  ✗ Error al eliminar {file_path}: {e}")
                logger.warning(f"Error al eliminar {file_path}: {e}")

    # Eliminar directorios
    for dir_path in dirs_to_delete:
        if os.path.isdir(dir_path):
            try:
                shutil.rmtree(dir_path)
                stats["deleted_dirs"] += 1
                if verbose:
                    print(f"  ✓ Eliminado: {dir_path}/")
                logger.info(f"Directorio eliminado: {dir_path}")
            except Exception as e:
                stats["errors"].append(f"{dir_path}: {e}")
                if verbose:
                    print(f"  ✗ Error al eliminar {dir_path}: {e}")
                logger.warning(f"Error al eliminar {dir_path}: {e}")

    return stats


def get_cleanable_items(
    output_file: str = "transcripcion.txt",
    chunks_dir: str = "chunks",
    cache_dir: str = ".cache/transcriptions",
    log_file: str = "transcriptor.log"
) -> list[dict]:
    """
    Lista los archivos y directorios que se pueden limpiar.

    Returns:
        Lista de dicts con información de cada item
    """
    items = []

    # Archivos
    files_to_check = [
        (output_file, "Transcripción"),
        (output_file.replace(".txt", "_resumen.txt"), "Resumen"),
        (log_file, "Archivo de logs"),
    ]

    for file_path, description in files_to_check:
        if os.path.isfile(file_path):
            size = os.path.getsize(file_path)
            items.append({
                "path": file_path,
                "type": "file",
                "description": description,
                "size": size,
                "size_str": f"{size / 1024:.1f} KB" if size < 1024 * 1024 else f"{size / (1024*1024):.1f} MB"
            })

    # Directorios
    dirs_to_check = [
        (chunks_dir, "Fragmentos de audio"),
        (cache_dir, "Caché de transcripciones"),
    ]

    for dir_path, description in dirs_to_check:
        if os.path.isdir(dir_path):
            # Contar archivos y tamaño total
            total_size = 0
            file_count = 0
            for root, _, files in os.walk(dir_path):
                for f in files:
                    file_count += 1
                    total_size += os.path.getsize(os.path.join(root, f))

            items.append({
                "path": dir_path,
                "type": "directory",
                "description": description,
                "file_count": file_count,
                "size": total_size,
                "size_str": f"{total_size / 1024:.1f} KB" if total_size < 1024 * 1024 else f"{total_size / (1024*1024):.1f} MB"
            })

    return items


def split_audio(file_path: str, chunk_length_ms: int, output_dir: str) -> list[str]:
    """
    Divide un archivo de audio en fragmentos de chunk_length_ms milisegundos.
    - file_path: ruta al audio original (.m4a, .mp3, .wav, etc.)
    - chunk_length_ms: longitud de cada fragmento en ms
    - output_dir: carpeta donde se guardarán los fragmentos
    Devuelve la lista de rutas de los fragmentos generados.
    """
    os.makedirs(output_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(file_path))[0]
    pattern = os.path.join(output_dir, f"{base}_%03d.m4a")

    # Usa ffmpeg segment para cortar sin recodificar
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error",
        "-i", file_path,
        "-f", "segment",
        "-segment_time", str(chunk_length_ms // 1000),
        "-c", "copy",
        pattern
    ]
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al dividir el audio con ffmpeg: {e}")
        sys.exit(1)

    # Recopila los archivos resultantes
    files = sorted([
        os.path.join(output_dir, fn)
        for fn in os.listdir(output_dir)
        if fn.startswith(base) and fn.endswith(".m4a")
    ])
    return files

@retry(
    stop=stop_after_attempt(int(os.getenv("MAX_RETRY_ATTEMPTS", "5"))),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    retry=retry_if_exception_type((Exception,)),
    reraise=True
)
def transcribe_audio(client: OpenAI, file_path: str) -> str:
    """
    Transcribe un fragmento de audio usando Whisper-1 con reintentos automáticos.
    - client: instancia de OpenAI
    - file_path: ruta al fragmento de audio
    Devuelve el texto transcrito.

    Reintentos automáticos en caso de errores de red o rate limiting.
    """
    try:
        with open(file_path, "rb") as audio_file:
            logger.debug(f"Enviando solicitud de transcripción para: {file_path}")
            resp = client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-1"
            )
        logger.debug(f"Transcripción exitosa: {file_path}")
        return resp.text
    except Exception as e:
        logger.error(f"Error al transcribir {file_path}: {type(e).__name__} - {e}")
        raise

def generate_summary(client: OpenAI, transcription: str, model: str = "gpt-4o-mini") -> dict:
    """
    Genera un resumen estructurado de la transcripción usando un modelo de lenguaje.

    Args:
        client: Cliente de OpenAI
        transcription: Texto completo de la transcripción
        model: Modelo a usar (gpt-4o-mini, gpt-4, gpt-4o, etc.)

    Returns:
        dict con secciones del resumen
    """
    logger.info(f"Generando resumen con modelo {model}...")

    prompt = f"""Eres un asistente experto en análisis de contenido. Analiza la siguiente transcripción y genera un resumen estructurado y completo.

TRANSCRIPCIÓN:
{transcription}

Por favor, genera un resumen estructurado con las siguientes secciones:

1. RESUMEN EJECUTIVO (2-3 párrafos que capturen la esencia completa)
2. PUNTOS CLAVE (5-10 bullet points con los aspectos más importantes)
3. TEMAS PRINCIPALES (lista de temas discutidos con breve descripción)
4. ACCIONES Y DECISIONES (si hay acciones a tomar, decisiones tomadas, o próximos pasos)
5. CONCLUSIONES (síntesis final y reflexiones importantes)

Formatea tu respuesta de manera clara y estructurada, usando markdown."""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "Eres un experto analista que crea resúmenes estructurados, claros y completos de transcripciones de audio."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,  # Más determinístico para resúmenes
            max_tokens=2000   # Suficiente para un resumen extenso
        )

        summary_text = response.choices[0].message.content

        # Información de uso
        usage = response.usage
        logger.info(f"Resumen generado - Tokens usados: {usage.total_tokens} "
                   f"(prompt: {usage.prompt_tokens}, respuesta: {usage.completion_tokens})")

        return {
            "summary": summary_text,
            "model": model,
            "tokens_used": usage.total_tokens
        }

    except Exception as e:
        logger.error(f"Error al generar resumen: {type(e).__name__} - {e}")
        raise

def main():
    print("=" * 70)
    print("🎙️  Transcriptor de Audio con Whisper-1")
    print("=" * 70)

    # -----------------------------
    # 1. Parseo de argumentos
    # -----------------------------
    parser = argparse.ArgumentParser(
        description="Divide un audio en fragmentos y transcribe con Whisper-1",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "audio_path",
        help="Ruta al archivo de audio de entrada (.m4a, .mp3, .wav, etc.)"
    )
    parser.add_argument(
        "--minutes", "-m",
        type=int,
        default=int(os.getenv("DEFAULT_CHUNK_MINUTES", "5")),
        help="Duración de cada fragmento en minutos (por defecto: 5)"
    )
    parser.add_argument(
        "--outdir", "-d",
        default="chunks",
        help="Directorio donde se guardan los fragmentos"
    )
    parser.add_argument(
        "--output", "-o",
        default="transcripcion.txt",
        help="Fichero de salida con la transcripción completa"
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Desactivar el uso de caché"
    )
    parser.add_argument(
        "--keep-chunks",
        action="store_true",
        help="No eliminar los fragmentos de audio después de transcribir"
    )
    parser.add_argument(
        "--summary", "-s",
        action="store_true",
        help="Generar resumen automático de la transcripción"
    )
    parser.add_argument(
        "--summary-model",
        default=os.getenv("SUMMARY_MODEL", "gpt-4o-mini"),
        help="Modelo a usar para el resumen (gpt-4o-mini, gpt-4, gpt-4o, etc.)"
    )
    parser.add_argument(
        "--clean", "-c",
        action="store_true",
        help="Limpiar archivos de ejecuciones anteriores (transcripciones, caché, logs)"
    )
    args = parser.parse_args()

    # -----------------------------
    # Modo limpieza (si se usa --clean sin archivo)
    # -----------------------------
    if args.clean and args.audio_path == "clean":
        print("\n🧹 Limpiando archivos anteriores...")
        items = get_cleanable_items(args.output, args.outdir)
        if not items:
            print("  No hay archivos para limpiar.")
            sys.exit(0)

        print("\nArchivos a eliminar:")
        for item in items:
            if item["type"] == "file":
                print(f"  📄 {item['path']} ({item['size_str']}) - {item['description']}")
            else:
                print(f"  📁 {item['path']}/ ({item['file_count']} archivos, {item['size_str']}) - {item['description']}")

        print()
        stats = clean_outputs(args.output, args.outdir, verbose=True)
        print(f"\n✓ Limpieza completada: {stats['deleted_files']} archivos, {stats['deleted_dirs']} directorios eliminados")
        sys.exit(0)

    logger.info("Iniciando Transcriptor")
    logger.info(f"Archivo de entrada: {args.audio_path}")

    # Si se usa --clean con archivo, limpiar primero
    if args.clean:
        print("\n🧹 Limpiando archivos anteriores...")
        stats = clean_outputs(args.output, args.outdir, verbose=True)
        if stats['deleted_files'] > 0 or stats['deleted_dirs'] > 0:
            print("✓ Limpieza completada\n")
        else:
            print("  No había archivos para limpiar.\n")

    # -----------------------------
    # 2. Validación del archivo de entrada
    # -----------------------------
    logger.info("Validando archivo de audio...")
    is_valid, error_msg = validate_audio_file(args.audio_path)
    if not is_valid:
        logger.error(f"Validación fallida: {error_msg}")
        print(f"\n❌ ERROR: {error_msg}")
        sys.exit(1)

    print(f"✓ Archivo de audio validado: {args.audio_path}")

    # -----------------------------
    # 3. Limpieza previa
    # -----------------------------
    if os.path.isdir(args.outdir):
        logger.info(f"Limpiando directorio existente: {args.outdir}")
        shutil.rmtree(args.outdir)
    os.makedirs(args.outdir, exist_ok=True)

    if os.path.isfile(args.output):
        logger.warning(f"Sobrescribiendo archivo de salida existente: {args.output}")
        os.remove(args.output)

    # -----------------------------
    # 4. Cliente OpenAI
    # -----------------------------
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("No se encontró OPENAI_API_KEY en el entorno")
        print("\n❌ ERROR: No se encontró OPENAI_API_KEY en el entorno.")
        print("   Configúrala con: export OPENAI_API_KEY='tu-clave-aquí'")
        print("   O crea un archivo .env con OPENAI_API_KEY=tu-clave-aquí")
        sys.exit(1)

    try:
        client = OpenAI(api_key=api_key)
        logger.info("Cliente OpenAI inicializado correctamente")
    except Exception as e:
        logger.error(f"Error al inicializar cliente OpenAI: {e}")
        print(f"\n❌ ERROR: No se pudo inicializar el cliente OpenAI: {e}")
        sys.exit(1)

    # -----------------------------
    # 5. Inicializar caché
    # -----------------------------
    cache = TranscriptionCache(os.getenv("CACHE_DIR", ".cache/transcriptions"))
    if args.no_cache:
        cache.enabled = False
        logger.info("Caché desactivado por argumento --no-cache")

    # -----------------------------
    # 6. División del audio
    # -----------------------------
    print(f"\n📂 Dividiendo audio en fragmentos de {args.minutes} minutos...")
    logger.info(f"Dividiendo audio en fragmentos de {args.minutes} minutos")

    chunk_ms = args.minutes * 60 * 1000
    try:
        chunks = split_audio(args.audio_path, chunk_ms, args.outdir)
        logger.info(f"Audio dividido en {len(chunks)} fragmentos")
        print(f"✓ Audio dividido en {len(chunks)} fragmentos")
    except Exception as e:
        logger.error(f"Error al dividir el audio: {e}")
        print(f"\n❌ ERROR: No se pudo dividir el audio: {e}")
        sys.exit(1)

    # -----------------------------
    # 7. Transcripción en bucle
    # -----------------------------
    print(f"\n🎯 Transcribiendo {len(chunks)} fragmentos...\n")
    logger.info("Iniciando proceso de transcripción")

    successful = 0
    failed = 0
    cached = 0

    try:
        with open(args.output, "w", encoding="utf-8") as out_f:
            for idx, chunk_file in enumerate(chunks, 1):
                print(f"[{idx}/{len(chunks)}] 🔊 Transcribiendo {os.path.basename(chunk_file)}...")

                try:
                    # Intentar recuperar del caché
                    text = cache.get(chunk_file)

                    if text:
                        cached += 1
                        print("          ✓ Recuperado del caché")
                    else:
                        # Transcribir con retry automático
                        text = transcribe_audio(client, chunk_file)
                        cache.set(chunk_file, text)
                        successful += 1
                        print("          ✓ Transcripción exitosa")

                    # Escribir resultado
                    out_f.write(f"\n{'=' * 70}\n")
                    out_f.write(f"Fragmento {idx}/{len(chunks)}: {os.path.basename(chunk_file)}\n")
                    out_f.write(f"{'=' * 70}\n\n")
                    out_f.write(text + "\n")
                    out_f.flush()  # Asegurar que se escribe inmediatamente

                except KeyboardInterrupt:
                    logger.warning("Proceso interrumpido por el usuario")
                    print("\n\n⚠️  Proceso interrumpido por el usuario")
                    print(f"   Fragmentos procesados: {successful}")
                    print(f"   Transcripción parcial guardada en: {args.output}")
                    sys.exit(130)

                except Exception as e:
                    failed += 1
                    error_msg = f"Error al transcribir {chunk_file}: {type(e).__name__} - {e}"
                    logger.error(error_msg)
                    print(f"          ✗ ERROR: {e}")

                    # Escribir error en el archivo de salida
                    out_f.write(f"\n{'=' * 70}\n")
                    out_f.write(f"Fragmento {idx}/{len(chunks)}: {os.path.basename(chunk_file)}\n")
                    out_f.write(f"{'=' * 70}\n\n")
                    out_f.write("[ERROR: No se pudo transcribir este fragmento]\n")
                    out_f.write(f"Motivo: {e}\n\n")
                    out_f.flush()

    except Exception as e:
        logger.error(f"Error fatal durante la transcripción: {e}")
        print(f"\n❌ ERROR FATAL: {e}")
        sys.exit(1)

    # -----------------------------
    # 8. Limpieza de fragmentos (opcional)
    # -----------------------------
    if not args.keep_chunks:
        logger.info(f"Eliminando fragmentos temporales: {args.outdir}")
        try:
            shutil.rmtree(args.outdir)
        except Exception as e:
            logger.warning(f"No se pudieron eliminar los fragmentos: {e}")

    # -----------------------------
    # 9. Generación de resumen (opcional)
    # -----------------------------
    summary_file = None
    if args.summary and (successful > 0 or cached > 0):
        print("\n" + "=" * 70)
        print("📝 Generando resumen de la transcripción...")
        print("=" * 70)

        try:
            # Leer la transcripción completa
            logger.info("Leyendo transcripción para generar resumen")
            with open(args.output, "r", encoding="utf-8") as f:
                transcription_text = f.read()

            # Generar resumen
            summary_result = generate_summary(client, transcription_text, args.summary_model)

            # Guardar resumen en archivo separado
            summary_file = args.output.replace(".txt", "_resumen.txt")
            with open(summary_file, "w", encoding="utf-8") as f:
                f.write("=" * 70 + "\n")
                f.write("📝 RESUMEN DE LA TRANSCRIPCIÓN\n")
                f.write("=" * 70 + "\n\n")
                f.write(f"Generado con modelo: {summary_result['model']}\n")
                f.write(f"Tokens utilizados: {summary_result['tokens_used']}\n")
                f.write("\n" + "=" * 70 + "\n\n")
                f.write(summary_result['summary'])
                f.write("\n\n" + "=" * 70 + "\n")

            print("✓ Resumen generado exitosamente")
            print(f"  Modelo usado: {summary_result['model']}")
            print(f"  Tokens usados: {summary_result['tokens_used']}")
            logger.info(f"Resumen guardado en: {summary_file}")

        except Exception as e:
            logger.error(f"Error al generar resumen: {e}")
            print(f"✗ Error al generar resumen: {e}")
            print("  La transcripción se completó correctamente, pero el resumen falló.")

    # -----------------------------
    # 10. Resumen final
    # -----------------------------
    print("\n" + "=" * 70)
    print("📊 Resumen de la transcripción")
    print("=" * 70)
    print(f"✓ Transcripciones exitosas: {successful}")
    if cached > 0:
        print(f"💾 Recuperadas del caché:    {cached}")
    if failed > 0:
        print(f"✗ Transcripciones fallidas:  {failed}")
    print(f"\n📄 Transcripción guardada en: {args.output}")

    if summary_file:
        print(f"📝 Resumen guardado en:       {summary_file}")

    if args.keep_chunks:
        print(f"📂 Fragmentos conservados en: {args.outdir}")

    logger.info(f"Proceso completado - Exitosas: {successful}, Caché: {cached}, Fallidas: {failed}")
    print("=" * 70)

    if failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
