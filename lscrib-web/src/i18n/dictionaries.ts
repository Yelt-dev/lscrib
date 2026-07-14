/** Diccionarios ES/EN. Microcopy de tono claro y humano, tranquilizador en
 *  privacidad y errores. */

export type Lang = 'es' | 'en'

// Claves con {placeholders} interpolables desde params.
export const dictionaries = {
  es: {
    'dropzone.title': 'Arrastra un audio o video',
    'dropzone.hint': 'mp3, wav, m4a, mp4, mov…  ·  o haz clic para elegir',
    'dropzone.drop': 'Suéltalo para empezar',

    'upload.uploading': 'Subiendo… {percent}%',
    'upload.processing': 'Subida completa. Preparando el archivo en el servidor…',

    'model.label': 'Modelo',
    'model.help': 'Más grande = más preciso pero más lento.',
    'model.downloaded': 'descargado',
    'model.download': 'descarga {size} la 1ª vez',

    'lang.label': 'Idioma del audio',
    'lang.auto': 'Detectar automáticamente',

    'vocab.label': 'Vocabulario (opcional)',
    'vocab.placeholder': 'Nombres propios, jerga… ej: Julián Quiñones, México',
    'vocab.help': 'Ayuda al modelo a acertar nombres y términos poco comunes.',

    'job.transcribe': 'Transcribir',
    'job.cancel': 'Cancelar',
    'job.retry': 'Reintentar',
    'job.requeue': 'Reencolar',
    'job.delete': 'Eliminar',
    'job.remove': 'Quitar',
    'job.duration': 'duración',
    'job.detected': 'detectado',

    'status.uploaded': 'Listo para transcribir',
    'status.queued': 'En cola',
    'status.normalizing': 'Preparando audio…',
    'status.transcribing': 'Transcribiendo',
    'status.completed': 'Listo',
    'status.failed': 'Error',
    'status.canceled': 'Cancelado',

    'progress.queued': 'En cola…',
    'progress.preparing': 'Preparando audio…',
    'progress.transcribing': 'Transcribiendo… {percent}%',
    'progress.eta': 'faltan {eta}',

    'terminal.completed': 'Listo. {n} segmentos.',
    'terminal.failed': 'Algo salió mal al transcribir. {reason}',
    'terminal.canceled': 'Cancelado.',

    'error.generic': 'Ocurrió un problema. Inténtalo de nuevo.',
    'error.tooBig': 'Ese archivo supera el límite de {size} MB.',
    'error.exists': 'Ya transcribiste este archivo. Lo abrimos.',
    'error.ffmpeg':
      'Falta ffmpeg. Instálalo: `brew install ffmpeg` (macOS) o `apt install ffmpeg` (Linux).',
    'error.upload': 'Se cortó la conexión al subir el archivo. ¿Sigue lscrib en marcha?',

    'cpu.title': 'Este equipo no puede ejecutar lscrib',
    'cpu.body':
      'El procesador de esta máquina ({model}) no tiene las instrucciones {missing}, que necesitan el motor de transcripción (faster-whisper) y NumPy. No es culpa de tu archivo: ningún audio se podrá transcribir aquí.',
    'cpu.hint':
      'Es una limitación del hardware, no hay ajuste que lo arregle. Instala lscrib en un equipo con un procesador de 2012 en adelante.',
    'cpu.unknownModel': 'desconocido',
    'cpu.banner': 'Transcripción deshabilitada: el procesador de este equipo no es compatible.',
    'cpu.details': 'Ver detalles',

    'common.cancel': 'Cancelar',
    'common.gotIt': 'Entendido',
    'dialog.download.title': 'Descargar el modelo «{model}»',
    'dialog.download.body':
      'Este modelo descarga {size} la primera vez. Se guarda en tu máquina y no se vuelve a bajar.',
    'dialog.download.confirm': 'Descargar y transcribir',
    'dialog.delete.title': '¿Eliminar este trabajo?',
    'dialog.delete.body':
      'El audio y el transcript se borrarán de tu disco. No se puede deshacer.',
    'queue.moveUp': 'Subir en la cola',
    'queue.moveDown': 'Bajar en la cola',

    'editor.title': 'Transcript',
    'editor.empty': 'El texto aparecerá aquí conforme se transcribe.',
    'editor.hint': 'Doble clic en una línea para editarla · clic en una palabra salta el audio ahí.',
    'search.placeholder': 'Buscar en el transcript…',
    'search.count': '{current}/{total}',
    'search.none': 'sin resultados',
    'follow.label': 'Seguir reproducción',
    'review.label': 'Dudosas',
    'review.title': 'Resalta las palabras de baja confianza del modelo, para revisarlas',

    'export.as': 'Exportar como',
    'export.saved': 'Guardado {filename}',

    'sidebar.title': 'Trabajos',
    'sidebar.empty': 'Aún no hay trabajos. Arrastra un archivo para empezar.',
    'sidebar.showing': '{shown} de {total}',
    'sidebar.loadMore': 'Cargar más',

    'server.offline': 'No se pudo conectar con el servidor. Revisa que lscrib esté en marcha.',

    'theme.toggle': 'Cambiar tema',
    'uilang.toggle': 'Idioma de la interfaz',
    'new.title': 'Nuevo trabajo',
  },
  en: {
    'dropzone.title': 'Drop an audio or video file',
    'dropzone.hint': 'mp3, wav, m4a, mp4, mov…  ·  or click to choose',
    'dropzone.drop': 'Drop it to start',

    'upload.uploading': 'Uploading… {percent}%',
    'upload.processing': 'Upload complete. Preparing the file on the server…',

    'model.label': 'Model',
    'model.help': 'Bigger is more accurate but slower.',
    'model.downloaded': 'downloaded',
    'model.download': '{size} download the first time',

    'lang.label': 'Audio language',
    'lang.auto': 'Detect automatically',

    'vocab.label': 'Vocabulary (optional)',
    'vocab.placeholder': 'Proper nouns, jargon… e.g. Julián Quiñones, México',
    'vocab.help': 'Helps the model get uncommon names and terms right.',

    'job.transcribe': 'Transcribe',
    'job.cancel': 'Cancel',
    'job.retry': 'Try again',
    'job.requeue': 'Re-queue',
    'job.delete': 'Delete',
    'job.remove': 'Remove',
    'job.duration': 'duration',
    'job.detected': 'detected',

    'status.uploaded': 'Ready to transcribe',
    'status.queued': 'Queued',
    'status.normalizing': 'Preparing audio…',
    'status.transcribing': 'Transcribing',
    'status.completed': 'Done',
    'status.failed': 'Error',
    'status.canceled': 'Canceled',

    'progress.queued': 'Queued…',
    'progress.preparing': 'Preparing audio…',
    'progress.transcribing': 'Transcribing… {percent}%',
    'progress.eta': '{eta} left',

    'terminal.completed': 'Done. {n} segments.',
    'terminal.failed': 'Something went wrong while transcribing. {reason}',
    'terminal.canceled': 'Canceled.',

    'error.generic': 'Something went wrong. Please try again.',
    'error.tooBig': 'That file is over the {size} MB limit.',
    'error.exists': 'You already transcribed this file. Opening it.',
    'error.ffmpeg':
      "ffmpeg isn't installed. Add it: `brew install ffmpeg` (macOS) or `apt install ffmpeg` (Linux).",
    'error.upload': 'The connection dropped while uploading. Is lscrib still running?',

    'cpu.title': 'This machine cannot run lscrib',
    'cpu.body':
      "This machine's processor ({model}) lacks the {missing} instructions that the transcription engine (faster-whisper) and NumPy require. It is not your file: no audio can be transcribed here.",
    'cpu.hint':
      'This is a hardware limit — no setting can work around it. Install lscrib on a machine with a 2012-or-newer processor.',
    'cpu.unknownModel': 'unknown',
    'cpu.banner': "Transcription disabled: this machine's processor isn't supported.",
    'cpu.details': 'See details',

    'common.cancel': 'Cancel',
    'common.gotIt': 'Got it',
    'dialog.download.title': 'Download the “{model}” model',
    'dialog.download.body':
      'This model needs a {size} download the first time. It is saved on your machine and never downloaded again.',
    'dialog.download.confirm': 'Download and transcribe',
    'dialog.delete.title': 'Delete this job?',
    'dialog.delete.body':
      'The audio and transcript will be removed from your disk. This cannot be undone.',
    'queue.moveUp': 'Move up in queue',
    'queue.moveDown': 'Move down in queue',

    'editor.title': 'Transcript',
    'editor.empty': 'Text will appear here as it is transcribed.',
    'editor.hint': 'Double-click a line to edit it · click a word to jump the audio there.',
    'search.placeholder': 'Search the transcript…',
    'search.count': '{current}/{total}',
    'search.none': 'no results',
    'follow.label': 'Follow playback',
    'review.label': 'Uncertain',
    'review.title': 'Highlight low-confidence words from the model, to review them',

    'export.as': 'Export as',
    'export.saved': 'Saved {filename}',

    'sidebar.title': 'Jobs',
    'sidebar.empty': 'No jobs yet. Drop a file to start.',
    'sidebar.showing': '{shown} of {total}',
    'sidebar.loadMore': 'Load more',

    'server.offline': 'Couldn’t reach the server. Make sure lscrib is running.',

    'theme.toggle': 'Toggle theme',
    'uilang.toggle': 'Interface language',
    'new.title': 'New job',
  },
} as const

export type TKey = keyof (typeof dictionaries)['es']
