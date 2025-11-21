#!/usr/bin/env python3
"""
Módulo de interfaz interactiva para Transcriptor usando questionary.
Proporciona menús navegables con flechas arriba/abajo y selección con Enter.
"""

import questionary
from pathlib import Path
from typing import Optional, Dict, Any


class TranscriptorMenu:
    """Gestiona la interfaz interactiva del Transcriptor."""

    def __init__(self):
        # Configurar el estilo de questionary
        self.style = questionary.Style([
            ('pointer', 'fg:#2ecc71 bold'),           # Puntero verde
            ('highlighted', 'fg:#3498db bg:#1c2833'), # Fondo azul
            ('selected', 'fg:#2ecc71'),               # Seleccionado en verde
            ('instruction', 'fg:#95a5a6'),            # Gris claro
            ('answer', 'fg:#2ecc71 bold'),            # Respuesta en verde
        ])

    def select_audio_file(self) -> Optional[str]:
        """Permite seleccionar un archivo de audio con navegación."""
        audio_extensions = {'.mp3', '.m4a', '.wav', '.flac', '.ogg', '.aac', '.wma'}
        audio_files = sorted([
            str(f) for f in Path.cwd().iterdir()
            if f.is_file() and f.suffix.lower() in audio_extensions
        ])

        if not audio_files:
            questionary.print(
                "⚠️  No se encontraron archivos de audio en el directorio actual.",
                style="fg:#e74c3c"
            )
            return None

        choices = audio_files + ["📁 Especificar ruta manualmente"]

        return questionary.select(
            "Selecciona un archivo de audio:",
            choices=choices,
            pointer='▶',
            style=self.style,
            use_indicator=True
        ).ask()

    def get_chunk_duration(self) -> int:
        """Seleccionar duración de fragmentos en minutos."""
        duration = questionary.select(
            "¿Cuántos minutos por fragmento?",
            choices=['1', '3', '5', '10', '15', '30', 'Personalizado'],
            default='5',
            pointer='▶',
            style=self.style
        ).ask()

        if duration == 'Personalizado':
            custom = questionary.text(
                "Ingresa la duración en minutos:",
                validate=lambda x: x.isdigit() and int(x) > 0,
                invalid_message="❌ Ingresa un número positivo"
            ).ask()
            return int(custom) if custom else 5

        return int(duration)

    def get_transcription_options(self) -> Dict[str, Any]:
        """Obtener opciones de transcripción de forma interactiva."""
        options = {}

        # Duración de fragmentos
        options['chunk_minutes'] = self.get_chunk_duration()

        # Generar resumen
        should_summarize = questionary.confirm(
            "¿Deseas generar un resumen automático?",
            default=False,
            style=self.style,
            auto_enter=False
        ).ask()
        options['summarize'] = should_summarize

        if should_summarize:
            model = questionary.select(
                "¿Qué modelo usar para el resumen?",
                choices=[
                    'gpt-4o-mini (más económico)',
                    'gpt-4o (balanceado)',
                    'gpt-4 (legacy)'
                ],
                default='gpt-4o-mini (más económico)',
                pointer='▶',
                style=self.style
            ).ask()
            # Extraer solo el nombre del modelo
            options['summary_model'] = model.split(' ')[0] if model else 'gpt-4o-mini'

        # Opciones avanzadas
        show_advanced = questionary.confirm(
            "¿Deseas ver opciones avanzadas?",
            default=False,
            style=self.style,
            auto_enter=False
        ).ask()

        if show_advanced:
            options['keep_chunks'] = questionary.confirm(
                "¿Mantener fragmentos de audio después de transcribir?",
                default=False,
                style=self.style,
                auto_enter=False
            ).ask()

            options['cache_disabled'] = questionary.confirm(
                "¿Desactivar caché de transcripciones?",
                default=False,
                style=self.style,
                auto_enter=False
            ).ask()

            # Opción de directorio personalizado
            custom_outdir = questionary.confirm(
                "¿Usar directorio personalizado para fragmentos?",
                default=False,
                style=self.style,
                auto_enter=False
            ).ask()

            if custom_outdir:
                outdir = questionary.text(
                    "Ingresa el nombre del directorio:",
                    default="chunks"
                ).ask()
                options['outdir'] = outdir if outdir else "chunks"
            else:
                options['outdir'] = "chunks"

            # Opción de archivo de salida personalizado
            custom_output = questionary.confirm(
                "¿Usar nombre personalizado para archivo de salida?",
                default=False,
                style=self.style,
                auto_enter=False
            ).ask()

            if custom_output:
                output = questionary.text(
                    "Ingresa el nombre del archivo de salida:",
                    default="transcripcion.txt"
                ).ask()
                options['output'] = output if output else "transcripcion.txt"
            else:
                options['output'] = "transcripcion.txt"
        else:
            options['keep_chunks'] = False
            options['cache_disabled'] = False
            options['outdir'] = "chunks"
            options['output'] = "transcripcion.txt"

        return options

    def confirm_action(self, message: str, default: bool = False) -> bool:
        """Confirmación simple de acción."""
        return questionary.confirm(
            message,
            default=default,
            style=self.style,
            auto_enter=False
        ).ask()

    def show_main_menu(self) -> Optional[str]:
        """Menú principal interactivo."""
        return questionary.select(
            "Transcriptor de Audio - Menú Principal",
            choices=[
                "🎙️  Transcribir nuevo audio",
                "📋 Ver archivos en directorio",
                "🧹 Limpiar archivos anteriores",
                "ℹ️  Información de uso",
                "🚪 Salir"
            ],
            pointer='▶',
            style=self.style,
            use_indicator=True
        ).ask()

    def print_header(self, title: str) -> None:
        """Imprime un encabezado formateado."""
        print("\n" + "=" * 70)
        print(f"  {title}")
        print("=" * 70 + "\n")

    def print_info(self, message: str) -> None:
        """Imprime un mensaje informativo."""
        print(f"ℹ️  {message}")

    def print_success(self, message: str) -> None:
        """Imprime un mensaje de éxito."""
        print(f"✓ {message}")

    def print_error(self, message: str) -> None:
        """Imprime un mensaje de error."""
        print(f"✗ {message}")

    def print_warning(self, message: str) -> None:
        """Imprime un mensaje de advertencia."""
        print(f"⚠️  {message}")

    def show_configuration_summary(self, audio_path: str, options: Dict[str, Any]) -> None:
        """Muestra un resumen de la configuración seleccionada."""
        self.print_header("Resumen de Configuración")

        print(f"📄 Archivo de entrada:     {audio_path}")
        print(f"⏱️  Duración de fragmentos: {options['chunk_minutes']} minutos")
        print(f"📝 Generar resumen:        {'Sí' if options.get('summarize', False) else 'No'}")

        if options.get('summarize'):
            print(f"🤖 Modelo de resumen:      {options.get('summary_model', 'gpt-4o-mini')}")

        print(f"📂 Directorio fragmentos:  {options.get('outdir', 'chunks')}")
        print(f"💾 Archivo de salida:      {options.get('output', 'transcripcion.txt')}")
        print(f"🗂️  Mantener fragmentos:    {'Sí' if options.get('keep_chunks', False) else 'No'}")
        print(f"💿 Usar caché:             {'No' if options.get('cache_disabled', False) else 'Sí'}")

        print()

    def show_info(self) -> None:
        """Muestra información de uso de la aplicación."""
        self.print_header("Información de Uso")

        info_text = """
El Transcriptor de Audio utiliza el modelo Whisper-1 de OpenAI para
convertir archivos de audio en texto.

Formatos soportados:
  • MP3, M4A, WAV, FLAC, OGG, AAC, WMA

Características:
  ✓ División automática en fragmentos
  ✓ Transcripción de alta calidad con Whisper-1
  ✓ Sistema de caché (evita re-procesar)
  ✓ Reintentos automáticos en caso de errores
  ✓ Resumen automático con GPT (opcional)

Costos aproximados (verificar precios actuales):
  • Whisper-1: $0.006 por minuto de audio
  • GPT-4o-mini resumen: ~$0.001-$0.005 por resumen
  • GPT-4o resumen: ~$0.02-$0.10 por resumen

Ejemplo: Audio de 60 minutos = ~$0.36 USD
         + Resumen con gpt-4o-mini = ~$0.37 USD total

Requisitos:
  • API Key de OpenAI configurada en .env
  • FFmpeg instalado en el sistema
        """
        print(info_text)

        questionary.press_any_key_to_continue(
            "Presiona cualquier tecla para volver al menú...",
            style=self.style
        ).ask()

    def show_audio_files_list(self) -> None:
        """Muestra la lista de archivos de audio en el directorio actual."""
        self.print_header("Archivos de Audio Disponibles")

        audio_extensions = {'.mp3', '.m4a', '.wav', '.flac', '.ogg', '.aac', '.wma'}
        audio_files = sorted([
            f for f in Path.cwd().iterdir()
            if f.is_file() and f.suffix.lower() in audio_extensions
        ])

        if not audio_files:
            self.print_warning("No se encontraron archivos de audio en el directorio actual.")
        else:
            print(f"Se encontraron {len(audio_files)} archivo(s) de audio:\n")
            for idx, file in enumerate(audio_files, 1):
                size_mb = file.stat().st_size / (1024 * 1024)
                print(f"  {idx}. {file.name} ({size_mb:.2f} MB)")

        print()
        questionary.press_any_key_to_continue(
            "Presiona cualquier tecla para volver al menú...",
            style=self.style
        ).ask()

    def show_cleanable_items(self, items: list) -> None:
        """Muestra los archivos que se pueden limpiar."""
        self.print_header("Archivos Limpiables")

        if not items:
            self.print_info("No hay archivos para limpiar.")
            return

        print("Se encontraron los siguientes archivos/directorios:\n")
        total_size = 0
        for item in items:
            size_str = f"({item['size_str']})" if item['size'] > 0 else ""
            icon = "📁" if item['type'] == 'directory' else "📄"
            print(f"  {icon} {item['path']} {size_str}")
            print(f"      └─ {item['description']}")
            total_size += item['size']

        if total_size > 0:
            total_str = f"{total_size / 1024:.1f} KB" if total_size < 1024 * 1024 else f"{total_size / (1024*1024):.1f} MB"
            print(f"\n  Total: {total_str}")
        print()

    def confirm_clean(self, items: list) -> bool:
        """Confirma la limpieza de archivos."""
        if not items:
            return False

        return questionary.confirm(
            f"¿Eliminar {len(items)} archivo(s)/directorio(s)?",
            default=False,
            style=self.style,
            auto_enter=False
        ).ask()
