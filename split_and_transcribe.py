#!/usr/bin/env python3

import os
import sys
import shutil
import subprocess
import argparse
from openai import OpenAI

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

def transcribe_audio(client: OpenAI, file_path: str) -> str:
    """
    Transcribe un fragmento de audio usando Whisper-1.
    - client: instancia de OpenAI
    - file_path: ruta al fragmento de audio
    Devuelve el texto transcrito.
    """
    with open(file_path, "rb") as audio_file:
        resp = client.audio.transcriptions.create(
            file=audio_file,
            model="whisper-1"
        )
    return resp.text

def main():
    # -----------------------------
    # 1. Parseo de argumentos
    # -----------------------------
    parser = argparse.ArgumentParser(
        description="Divide un audio en fragmentos y transcribe con Whisper-1"
    )
    parser.add_argument(
        "audio_path",
        help="Ruta al archivo de audio de entrada (.m4a, .mp3, .wav)"
    )
    parser.add_argument(
        "--minutes", "-m",
        type=int,
        default=5,
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
    args = parser.parse_args()

    # -----------------------------
    # 2. Limpieza previa
    # -----------------------------
    if os.path.isdir(args.outdir):
        shutil.rmtree(args.outdir)
    os.makedirs(args.outdir, exist_ok=True)

    if os.path.isfile(args.output):
        os.remove(args.output)

    # -----------------------------
    # 3. Cliente OpenAI
    # -----------------------------
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ ERROR: No se encontró OPENAI_API_KEY en el entorno.")
        sys.exit(1)
    client = OpenAI(api_key=api_key)

    # -----------------------------
    # 4. División del audio
    # -----------------------------
    chunk_ms = args.minutes * 60 * 1000
    chunks = split_audio(args.audio_path, chunk_ms, args.outdir)

    # -----------------------------
    # 5. Transcripción en bucle
    # -----------------------------
    with open(args.output, "w", encoding="utf-8") as out_f:
        for chunk_file in chunks:
            print(f"🔊 Transcribiendo {chunk_file} …")
            try:
                text = transcribe_audio(client, chunk_file)
                out_f.write(f"\n=== Transcripción de {chunk_file} ===\n")
                out_f.write(text + "\n")
            except Exception as e:
                print(f"⚠️ Error al transcribir {chunk_file}: {e}")

    print(f"\n✅ Transcripción completa guardada en: {args.output}")

if __name__ == "__main__":
    main()
