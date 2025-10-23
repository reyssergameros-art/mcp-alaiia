# Database Query Tool - Configuración

## Valores por Defecto

La herramienta `database_query` ahora soporta valores por defecto para las conexiones a base de datos, lo que permite un uso más amigable sin necesidad de especificar todos los parámetros en cada consulta.

## 📁 Archivos Modificados

### 1. `domain/config.py` (NUEVO)
Archivo de configuración centralizada que contiene todos los valores por defecto para diferentes tipos de base de datos.

```python
# Valores por defecto para PostgreSQL
POSTGRES_HOST: str = "localhost"
POSTGRES_PORT: int = 5432
POSTGRES_DATABASE: str = "quality"
POSTGRES_USERNAME: str = "postgres"
POSTGRES_PASSWORD: str = "Quality"
```

### 2. `domain/models.py` (MODIFICADO)
El modelo `DatabaseConnection` ahora aplica automáticamente los valores por defecto en el método `__post_init__()`.

## 🚀 Uso Simplificado

### Antes (verbose)
```python
await mcp_my-mcp-server_database_query({
    "db_type": "postgres",
    "host": "localhost",
    "port": 5432,
    "database": "quality",
    "username": "postgres",
    "password": "Quality",
    "query": "SELECT * FROM priority"
})
```

### Ahora (simple) ✨
```python
await mcp_my-mcp-server_database_query({
    "db_type": "postgres",
    "query": "SELECT * FROM priority"
})
```

## 🔧 Personalización

### Cambiar Valores por Defecto

Edita el archivo `src/tools/database_query/domain/config.py`:

```python
@dataclass
class DatabaseDefaults:
    # Cambia estos valores según tu entorno
    POSTGRES_HOST: str = "tu-servidor.com"
    POSTGRES_PORT: int = 5432
    POSTGRES_DATABASE: str = "tu-base-de-datos"
    POSTGRES_USERNAME: str = "tu-usuario"
    POSTGRES_PASSWORD: str = "tu-contraseña"
```

### Sobrescribir Valores en Tiempo de Ejecución

Los valores por defecto solo se aplican si no se especifican. Puedes sobrescribir cualquier valor:

```python
# Usa una base de datos diferente manteniendo otros valores por defecto
await mcp_my-mcp-server_database_query({
    "db_type": "postgres",
    "database": "otra_base_datos",  # Sobrescribe solo la BD
    "query": "SELECT * FROM tabla"
})
```

## 🏗️ Arquitectura SOLID

La implementación respeta los principios SOLID:

- **Single Responsibility**: `config.py` solo maneja configuración
- **Open/Closed**: Extensible para nuevas bases de datos sin modificar código existente
- **Liskov Substitution**: Los valores por defecto no rompen el contrato del modelo
- **Interface Segregation**: Configuración separada de la lógica de negocio
- **Dependency Inversion**: El dominio depende de abstracciones, no de implementaciones

## 📊 Soporte Multi-Base de Datos

La configuración está preparada para múltiples bases de datos:

```python
# PostgreSQL (activo)
DB_DEFAULTS.get_defaults_for_db_type("postgres")

# MySQL (preparado para futuro)
DB_DEFAULTS.get_defaults_for_db_type("mysql")

# SQL Server (preparado para futuro)
DB_DEFAULTS.get_defaults_for_db_type("sqlserver")
```

## ⚠️ Seguridad

**IMPORTANTE**: El archivo `config.py` contiene credenciales. Asegúrate de:

1. NO commitear credenciales de producción
2. Usar variables de entorno en producción
3. Agregar `config.py` al `.gitignore` si es necesario
4. Usar diferentes configs para dev/staging/prod

## 🧪 Ejemplos de Uso

### Contar registros
```python
{
    "db_type": "postgres",
    "query": "SELECT COUNT(*) FROM priority"
}
```

### Consultar con filtros
```python
{
    "db_type": "postgres",
    "query": "SELECT * FROM priority WHERE name LIKE '%alta%'",
    "output_format": "table"
}
```

### Cambiar formato de salida
```python
{
    "db_type": "postgres",
    "query": "SELECT * FROM priority",
    "output_format": "json"  # json, csv, markdown, table
}
```

### Limitar resultados
```python
{
    "db_type": "postgres",
    "query": "SELECT * FROM priority",
    "max_rows": 5
}
```

## 📝 Notas

- Los valores por defecto solo se aplican cuando no se especifica un `connection_string`
- Si un parámetro es `None`, se usa el valor por defecto
- Si un parámetro tiene un valor, ese valor tiene prioridad sobre el default
- La validación de conexión sigue siendo la misma

## 🎯 Beneficios

✅ **Menos código**: Prompts más cortos y legibles  
✅ **Mantenibilidad**: Cambios centralizados en un solo archivo  
✅ **Flexibilidad**: Sobrescritura selectiva cuando sea necesario  
✅ **SOLID**: Respeta principios de diseño  
✅ **Escalable**: Fácil agregar nuevas bases de datos  
