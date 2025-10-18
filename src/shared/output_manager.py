"""
Output Manager - Gestión centralizada de estructura de directorios de salida.

Este módulo proporciona una gestión consistente y organizada de todos los 
archivos de salida generados por las herramientas MCP-ALAIIA.

Principios SOLID aplicados:
- SRP: Solo maneja organización de output y metadatos
- OCP: Extensible para nuevos tipos sin modificar código existente
- DIP: No depende de implementaciones concretas de herramientas
- ISP: Interfaz clara y específica para gestión de outputs
"""

from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import json
import re
import hashlib


class OutputManager:
    """
    Gestión centralizada de estructura de directorios de salida.
    
    Características:
    - Organización jerárquica por tipo de output
    - Timestamps automáticos para trazabilidad
    - Metadatos JSON con información de ejecución
    - Sanitización automática de nombres
    - Prevención de sobrescritura
    - Historial completo preservado
    """
    
    BASE_OUTPUT_DIR = Path("./output")
    
    # Tipos de output soportados con sus carpetas
    OUTPUT_TYPES = {
        'swagger_analysis': 'swagger-analysis',
        'features': 'features',
        'jmeter': 'jmeter',
        'curl': 'curl',
        'curl_parser': 'curl-parser',
        'karate_project': 'karate-projects',
        'complete_workflow': 'complete-workflows'
    }
    
    @classmethod
    def create_output_directory(
        cls,
        output_type: str,
        identifier: str,
        timestamp: Optional[datetime] = None,
        custom_base_dir: Optional[str] = None
    ) -> Path:
        """
        Crea estructura de directorio organizada para tipo de output.
        
        Args:
            output_type: Tipo de output (swagger_analysis, features, jmeter, etc.)
            identifier: Identificador único (nombre API, hash cURL, nombre proyecto)
            timestamp: Timestamp opcional (default: datetime.now())
            custom_base_dir: Directorio base personalizado (default: ./output)
            
        Returns:
            Path del directorio creado
            
        Raises:
            ValueError: Si output_type no es válido
            
        Example:
            >>> manager = OutputManager()
            >>> output_dir = manager.create_output_directory(
            ...     'features',
            ...     'Petstore API'
            ... )
            >>> print(output_dir)
            output/features/20250117_103045-petstore-api/
        """
        if output_type not in cls.OUTPUT_TYPES:
            raise ValueError(
                f"Unknown output type: {output_type}. "
                f"Valid types: {', '.join(cls.OUTPUT_TYPES.keys())}"
            )
        
        # Usar timestamp actual si no se proporciona
        if timestamp is None:
            timestamp = datetime.now()
        
        # Formato: YYYYMMDD_HHMMSS
        timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
        
        # Sanitizar identificador para nombre de carpeta
        sanitized_id = cls._sanitize_identifier(identifier)
        
        # Determinar directorio base
        base_dir = Path(custom_base_dir) if custom_base_dir else cls.BASE_OUTPUT_DIR
        
        # Construir path completo
        dir_name = f"{timestamp_str}-{sanitized_id}"
        output_dir = base_dir / cls.OUTPUT_TYPES[output_type] / dir_name
        
        # Crear directorio (con padres si no existen)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        return output_dir
    
    @classmethod
    def save_metadata(
        cls,
        output_dir: Path,
        metadata: Dict[str, Any]
    ) -> Path:
        """
        Guarda archivo metadata.json con información de ejecución.
        
        Args:
            output_dir: Directorio donde guardar metadata
            metadata: Diccionario con metadatos de la ejecución
            
        Returns:
            Path del archivo metadata.json creado
            
        Example:
            >>> metadata = {
            ...     'source': {'type': 'swagger', 'url': 'https://api.example.com'},
            ...     'summary': {'files_generated': 5}
            ... }
            >>> manager.save_metadata(output_dir, metadata)
        """
        # Asegurar que el directorio existe
        if isinstance(output_dir, str):
            output_dir = Path(output_dir)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Agregar timestamp automático si no existe
        if 'timestamp' not in metadata:
            metadata['timestamp'] = datetime.now().isoformat()
        
        # Agregar execution_id único si no existe
        if 'execution_id' not in metadata:
            metadata['execution_id'] = cls._generate_execution_id()
        
        # Path del archivo metadata
        metadata_file = output_dir / "metadata.json"
        
        # Guardar con formato legible
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        return metadata_file
    
    @classmethod
    def save_summary(
        cls,
        output_dir: Path,
        summary_data: Dict[str, Any],
        filename: str = "summary.json"
    ) -> Path:
        """
        Guarda archivo de resumen con estadísticas de la ejecución.
        
        Args:
            output_dir: Directorio donde guardar resumen
            summary_data: Datos del resumen
            filename: Nombre del archivo (default: summary.json)
            
        Returns:
            Path del archivo de resumen creado
        """
        if isinstance(output_dir, str):
            output_dir = Path(output_dir)
        
        summary_file = output_dir / filename
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)
        
        return summary_file
    
    @classmethod
    def get_latest_output(cls, output_type: str) -> Optional[Path]:
        """
        Obtiene el directorio de output más reciente para un tipo.
        
        Args:
            output_type: Tipo de output a buscar
            
        Returns:
            Path del directorio más reciente o None si no existe
            
        Example:
            >>> latest = OutputManager.get_latest_output('features')
            >>> print(latest)
            output/features/20250117_160815-api-name/
        """
        if output_type not in cls.OUTPUT_TYPES:
            return None
        
        type_dir = cls.BASE_OUTPUT_DIR / cls.OUTPUT_TYPES[output_type]
        
        if not type_dir.exists():
            return None
        
        # Obtener subdirectorios y ordenar por nombre (timestamp)
        subdirs = sorted(
            [d for d in type_dir.iterdir() if d.is_dir()],
            key=lambda x: x.name,
            reverse=True  # Más reciente primero
        )
        
        return subdirs[0] if subdirs else None
    
    @classmethod
    def list_outputs(
        cls,
        output_type: Optional[str] = None,
        limit: Optional[int] = None
    ) -> list[Path]:
        """
        Lista todos los outputs de un tipo (o todos).
        
        Args:
            output_type: Tipo de output (None = todos)
            limit: Límite de resultados (None = todos)
            
        Returns:
            Lista de Paths ordenados por más reciente
        """
        outputs = []
        
        # Determinar qué tipos buscar
        types_to_search = [output_type] if output_type else cls.OUTPUT_TYPES.keys()
        
        for otype in types_to_search:
            if otype not in cls.OUTPUT_TYPES:
                continue
            
            type_dir = cls.BASE_OUTPUT_DIR / cls.OUTPUT_TYPES[otype]
            
            if type_dir.exists():
                subdirs = [d for d in type_dir.iterdir() if d.is_dir()]
                outputs.extend(subdirs)
        
        # Ordenar por timestamp (nombre de carpeta) descendente
        outputs.sort(key=lambda x: x.name, reverse=True)
        
        # Aplicar límite si se especifica
        if limit:
            outputs = outputs[:limit]
        
        return outputs
    
    @classmethod
    def _sanitize_identifier(cls, identifier: str) -> str:
        """
        Sanitiza identificador para usar como nombre de carpeta.
        
        Reglas:
        - Convierte a lowercase
        - Reemplaza espacios con guiones
        - Elimina caracteres especiales
        - Limita longitud a 50 caracteres
        - Elimina guiones al inicio/final
        
        Args:
            identifier: Identificador original
            
        Returns:
            Identificador sanitizado y seguro para filesystem
            
        Example:
            >>> OutputManager._sanitize_identifier("My API v2.0 (Beta)")
            'my-api-v20-beta'
        """
        # Convertir a lowercase
        sanitized = identifier.lower()
        
        # Reemplazar espacios y caracteres no alfanuméricos con guiones
        sanitized = re.sub(r'[^\w\s-]', '', sanitized)
        sanitized = re.sub(r'[\s_]+', '-', sanitized)
        
        # Eliminar múltiples guiones consecutivos
        sanitized = re.sub(r'-+', '-', sanitized)
        
        # Limitar longitud máxima
        max_length = 50
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        # Remover guiones al inicio/final
        sanitized = sanitized.strip('-')
        
        # Fallback si queda vacío
        return sanitized or 'output'
    
    @classmethod
    def _generate_execution_id(cls) -> str:
        """
        Genera un execution_id único basado en timestamp y random.
        
        Returns:
            String único para identificar la ejecución
        """
        timestamp = datetime.now().isoformat()
        random_component = hashlib.md5(timestamp.encode()).hexdigest()[:8]
        return f"exec-{random_component}"
    
    @classmethod
    def create_workflow_structure(
        cls,
        identifier: str,
        timestamp: Optional[datetime] = None
    ) -> Dict[str, Path]:
        """
        Crea estructura completa para complete_workflow con subdirectorios.
        
        Args:
            identifier: Identificador del workflow (nombre API)
            timestamp: Timestamp opcional
            
        Returns:
            Dict con paths de cada subdirectorio
            
        Example:
            >>> paths = OutputManager.create_workflow_structure('Petstore API')
            >>> print(paths['features'])
            output/complete-workflows/20250117_103045-petstore-api/02-features/
        """
        # Crear directorio principal del workflow
        base_dir = cls.create_output_directory(
            'complete_workflow',
            identifier,
            timestamp
        )
        
        # Crear subdirectorios
        subdirs = {
            'swagger_analysis': base_dir / "01-swagger-analysis",
            'features': base_dir / "02-features",
            'jmeter': base_dir / "03-jmeter",
            'curl': base_dir / "04-curl"
        }
        
        # Crear cada subdirectorio
        for subdir in subdirs.values():
            subdir.mkdir(parents=True, exist_ok=True)
        
        # Agregar el directorio base
        subdirs['base'] = base_dir
        
        return subdirs
    
    @classmethod
    def should_use_auto_structure(cls, output_dir: Optional[str]) -> bool:
        """
        Determina si debe usar estructura automática o path manual.
        
        Args:
            output_dir: Path proporcionado por usuario (puede ser None)
            
        Returns:
            True si debe usar OutputManager, False si respetar path manual
        """
        # Si es None o string vacío, usar auto
        if not output_dir:
            return True
        
        # Si es explícitamente "./output", usar auto
        if output_dir in ["./output", "output"]:
            return True
        
        # Cualquier otro path, respetar
        return False
    
    @classmethod
    def extract_identifier_from_swagger(cls, swagger_data: Dict[str, Any]) -> str:
        """
        Extrae identificador apropiado de datos de Swagger.
        
        Args:
            swagger_data: Datos de análisis de Swagger
            
        Returns:
            Identificador sanitizado
        """
        # Intentar obtener título
        identifier = swagger_data.get('title', '')
        
        # Fallback a info.title si existe
        if not identifier and 'info' in swagger_data:
            identifier = swagger_data['info'].get('title', '')
        
        # Fallback final
        if not identifier:
            identifier = 'api'
        
        return identifier
    
    @classmethod
    def extract_identifier_from_curl(cls, curl_command: str) -> str:
        """
        Extrae identificador apropiado de comando cURL.
        
        Args:
            curl_command: Comando cURL
            
        Returns:
            Identificador basado en hash del comando
        """
        # Generar hash corto del comando
        command_hash = hashlib.md5(curl_command.encode()).hexdigest()[:12]
        return f"curl-{command_hash}"
