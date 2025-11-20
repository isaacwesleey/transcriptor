# Changelog

Todos los cambios notables de este proyecto serán documentados en este archivo.

## [2.0.0] - 2025-11-20

### Añadido
- **Sistema de caché**: Las transcripciones se guardan en caché para evitar re-procesar fragmentos
  - Configurable vía `.env` con `CACHE_ENABLED` y `CACHE_DIR`
  - Opción `--no-cache` para desactivar temporalmente
- **Logging estructurado**: Sistema completo de logs para debugging y auditoría
  - Logs en consola y archivo
  - Configurable vía `.env` con `LOG_LEVEL` y `LOG_FILE`
- **Validación de entrada**: Verificación completa de archivos antes de procesar
  - Comprueba existencia, formato, tamaño y validez del archivo
  - Usa `ffprobe` para validar la integridad del audio
- **Retry logic**: Reintentos automáticos con backoff exponencial
  - Maneja rate limiting y errores temporales de red
  - Configurable vía `.env` con `MAX_RETRY_ATTEMPTS`
- **Gestión de dependencias**:
  - `requirements.txt` para dependencias de producción
  - `requirements-dev.txt` para herramientas de desarrollo
  - `.env.example` con todas las variables de configuración
  - `.gitignore` apropiado para el proyecto
- **Nuevas opciones CLI**:
  - `--no-cache`: Desactivar el uso de caché
  - `--keep-chunks`: Conservar fragmentos de audio después de transcribir
- **Mejor UX**:
  - Indicadores de progreso mejorados
  - Resumen final con estadísticas
  - Manejo de interrupciones con Ctrl+C
  - Mensajes de error más informativos

### Mejorado
- **Manejo de errores robusto**:
  - Captura específica de errores con contexto
  - Los errores en fragmentos individuales no detienen el proceso completo
  - Errores se registran tanto en logs como en el archivo de salida
- **Formato de salida**:
  - Mejor formateo con separadores claros
  - Indicación del número de fragmento
  - Marcado de errores en el archivo de transcripción
- **Seguridad**:
  - Soporte para archivo `.env` para credenciales
  - Variables de entorno documentadas

### Técnico
- Refactorización completa del código
- Clase `TranscriptionCache` para gestión de caché
- Función `validate_audio_file()` para validación
- Función `setup_logger()` para configuración de logs
- Decorador `@retry` en función de transcripción
- Flush inmediato de resultados para evitar pérdida de datos

## [1.0.0] - 2024-07-09

### Añadido
- Versión inicial del transcriptor
- División de audio con FFmpeg
- Transcripción con Whisper-1 de OpenAI
- Procesamiento secuencial de fragmentos
- Salida en archivo de texto
