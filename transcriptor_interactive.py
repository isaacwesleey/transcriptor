#!/usr/bin/env python3
"""
Versión interactiva del Transcriptor con menús navegables.
Proporciona una interfaz guiada para transcribir audio sin necesidad de recordar flags CLI.

Uso:
    python transcriptor_interactive.py

Requisitos:
    - questionary: pip install questionary
    - Todas las dependencias de split_and_transcribe.py
"""

import sys
import os
import shutil
from pathlib import Path
from typing import Optional

# Importar el módulo de menús
from menu_interface import TranscriptorMenu

# Importar funciones del transcriptor principal
from split_and_transcribe import (
    validate_audio_file,
    split_audio,
    transcribe_audio,
    generate_summary,
    TranscriptionCache,
    setup_logger,
)
from openai import OpenAI
from dotenv import load_dotenv


def check_api_key() -> bool:
    """Verifica si la API key de OpenAI está configurada."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return False
    return True


def run_transcription(menu: TranscriptorMenu, audio_path: str, options: dict, logger) -> bool:
    """
    Ejecuta el proceso de transcripción con las opciones seleccionadas.

    Args:
        menu: Instancia de TranscriptorMenu
        audio_path: Ruta al archivo de audio
        options: Diccionario con opciones de configuración
        logger: Logger configurado

    Returns:
        True si la transcripción fue exitosa, False en caso contrario
    """
    try:
        # Inicializar cliente OpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        client = OpenAI(api_key=api_key)
        logger.info("Cliente OpenAI inicializado correctamente")

        # Limpiar directorios previos
        outdir = options.get('outdir', 'chunks')
        output_file = options.get('output', 'transcripcion.txt')

        if os.path.isdir(outdir):
            logger.info(f"Limpiando directorio existente: {outdir}")
            shutil.rmtree(outdir)
        os.makedirs(outdir, exist_ok=True)

        if os.path.isfile(output_file):
            logger.warning(f"Sobrescribiendo archivo de salida existente: {output_file}")
            os.remove(output_file)

        # Inicializar caché
        cache = TranscriptionCache(os.getenv("CACHE_DIR", ".cache/transcriptions"))
        if options.get('cache_disabled', False):
            cache.enabled = False
            logger.info("Caché desactivado por opción del usuario")

        # Dividir audio
        menu.print_header("Dividiendo Audio")
        chunk_minutes = options.get('chunk_minutes', 5)
        print(f"Dividiendo audio en fragmentos de {chunk_minutes} minutos...\n")
        logger.info(f"Dividiendo audio en fragmentos de {chunk_minutes} minutos")

        chunk_ms = chunk_minutes * 60 * 1000
        chunks = split_audio(audio_path, chunk_ms, outdir)
        logger.info(f"Audio dividido en {len(chunks)} fragmentos")
        menu.print_success(f"Audio dividido en {len(chunks)} fragmentos")

        # Transcripción
        menu.print_header(f"Transcribiendo {len(chunks)} Fragmentos")
        logger.info("Iniciando proceso de transcripción")

        successful = 0
        failed = 0
        cached = 0

        with open(output_file, "w", encoding="utf-8") as out_f:
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
                    out_f.flush()

                except KeyboardInterrupt:
                    logger.warning("Proceso interrumpido por el usuario")
                    print("\n\n⚠️  Proceso interrumpido por el usuario")
                    print(f"   Fragmentos procesados: {successful}")
                    print(f"   Transcripción parcial guardada en: {output_file}")
                    return False

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

        # Generar resumen si está activado
        summary_file = None
        if options.get('summarize', False) and (successful > 0 or cached > 0):
            menu.print_header("Generando Resumen")

            try:
                logger.info("Leyendo transcripción para generar resumen")
                with open(output_file, "r", encoding="utf-8") as f:
                    transcription_text = f.read()

                # Generar resumen
                summary_model = options.get('summary_model', 'gpt-4o-mini')
                summary_result = generate_summary(client, transcription_text, summary_model)

                # Guardar resumen en archivo separado
                summary_file = output_file.replace(".txt", "_resumen.txt")
                with open(summary_file, "w", encoding="utf-8") as f:
                    f.write("=" * 70 + "\n")
                    f.write("📝 RESUMEN DE LA TRANSCRIPCIÓN\n")
                    f.write("=" * 70 + "\n\n")
                    f.write(f"Generado con modelo: {summary_result['model']}\n")
                    f.write(f"Tokens utilizados: {summary_result['tokens_used']}\n")
                    f.write("\n" + "=" * 70 + "\n\n")
                    f.write(summary_result['summary'])
                    f.write("\n\n" + "=" * 70 + "\n")

                menu.print_success("Resumen generado exitosamente")
                print(f"  Modelo usado: {summary_result['model']}")
                print(f"  Tokens usados: {summary_result['tokens_used']}")
                logger.info(f"Resumen guardado en: {summary_file}")

            except Exception as e:
                logger.error(f"Error al generar resumen: {e}")
                menu.print_error(f"Error al generar resumen: {e}")
                print("  La transcripción se completó correctamente, pero el resumen falló.")

        # Limpieza de fragmentos
        if not options.get('keep_chunks', False):
            logger.info(f"Eliminando fragmentos temporales: {outdir}")
            try:
                shutil.rmtree(outdir)
            except Exception as e:
                logger.warning(f"No se pudieron eliminar los fragmentos: {e}")

        # Resumen final
        menu.print_header("Resumen de la Transcripción")
        print(f"✓ Transcripciones exitosas: {successful}")
        if cached > 0:
            print(f"💾 Recuperadas del caché:    {cached}")
        if failed > 0:
            print(f"✗ Transcripciones fallidas:  {failed}")

        print(f"\n📄 Transcripción guardada en: {output_file}")

        if summary_file:
            print(f"📝 Resumen guardado en:       {summary_file}")

        if options.get('keep_chunks', False):
            print(f"📂 Fragmentos conservados en: {outdir}")

        logger.info(f"Proceso completado - Exitosas: {successful}, Caché: {cached}, Fallidas: {failed}")
        print("=" * 70)

        return failed == 0

    except Exception as e:
        logger.error(f"Error fatal durante la transcripción: {e}")
        menu.print_error(f"Error fatal: {e}")
        return False


def interactive_mode():
    """Modo interactivo con menús de navegación."""
    load_dotenv()

    menu = TranscriptorMenu()
    logger = setup_logger()

    # Banner de bienvenida
    menu.print_header("🎙️  Transcriptor de Audio con Whisper-1")

    # Verificar API key
    if not check_api_key():
        menu.print_error("No se encontró OPENAI_API_KEY en el entorno.")
        print("\n   Configúrala con: export OPENAI_API_KEY='tu-clave-aquí'")
        print("   O crea un archivo .env con OPENAI_API_KEY=tu-clave-aquí\n")
        sys.exit(1)

    # Bucle principal del menú
    while True:
        action = menu.show_main_menu()

        if action == "🎙️  Transcribir nuevo audio":
            # Seleccionar archivo de audio
            audio_path = menu.select_audio_file()

            if not audio_path:
                menu.print_warning("No hay archivos de audio disponibles.")
                continue

            if audio_path == "📁 Especificar ruta manualmente":
                audio_path = input("\nIngresa la ruta del archivo de audio: ").strip()
                if not audio_path:
                    menu.print_warning("Ruta no especificada.")
                    continue

            # Validar archivo
            menu.print_info(f"Validando archivo: {audio_path}")
            is_valid, error_msg = validate_audio_file(audio_path)

            if not is_valid:
                menu.print_error(f"Validación fallida: {error_msg}")
                continue

            menu.print_success(f"Archivo de audio validado: {audio_path}")

            # Obtener opciones interactivamente
            print()
            options = menu.get_transcription_options()

            # Mostrar resumen de configuración
            menu.show_configuration_summary(audio_path, options)

            # Confirmación final
            if not menu.confirm_action("¿Proceder con la transcripción?"):
                menu.print_warning("Operación cancelada.")
                continue

            # Ejecutar transcripción
            success = run_transcription(menu, audio_path, options, logger)

            if success:
                print("\n✓ ¡Transcripción completada exitosamente!")
            else:
                print("\n⚠️  La transcripción se completó con errores o fue interrumpida.")

            print()

        elif action == "📋 Ver archivos en directorio":
            menu.show_audio_files_list()

        elif action == "🧹 Limpiar archivos anteriores":
            from split_and_transcribe import get_cleanable_items, clean_outputs

            items = get_cleanable_items()
            menu.show_cleanable_items(items)

            if items and menu.confirm_clean(items):
                stats = clean_outputs(verbose=True)
                if stats['deleted_files'] > 0 or stats['deleted_dirs'] > 0:
                    menu.print_success("Limpieza completada")
                if stats['errors']:
                    for error in stats['errors']:
                        menu.print_warning(error)
            elif items:
                menu.print_info("Limpieza cancelada")

            print()

        elif action == "ℹ️  Información de uso":
            menu.show_info()

        elif action == "🚪 Salir":
            menu.print_info("¡Hasta pronto!")
            sys.exit(0)

        else:
            # Si el usuario presiona Ctrl+C en el menú
            menu.print_info("¡Hasta pronto!")
            sys.exit(0)


if __name__ == "__main__":
    try:
        interactive_mode()
    except KeyboardInterrupt:
        print("\n\n⚠️  Programa interrumpido por el usuario. ¡Hasta pronto!")
        sys.exit(130)
