# MCP-ALAIIA: API Testing Automation Tools

Un servidor MCP (Model Context Protocol) para automatización de pruebas de APIs que incluye análisis de contratos Swagger, generación de archivos Feature de Karate DSL y creación de planes de prueba JMeter.

## 🚀 Características

### 🔍 swagger_analysis
- **Descripción**: Analiza especificaciones Swagger/OpenAPI desde URL o archivo
- **Entrada**: URL del contrato Swagger + formato (detailed/summary)
- **Salida**: Reporte completo de análisis en formato JSON

**Información extraída:**
- Datos generales de la API (título, versión, descripción, endpoints)
- Por cada endpoint: método HTTP, path, headers requeridos, parámetros, request body, respuestas

### 🎯 feature_generator  
- **Descripción**: Genera archivos .feature de Karate DSL para testing funcional
- **Entrada**: Datos de análisis Swagger + directorio de salida
- **Salida**: Archivos .feature listos para ejecutar con Karate

**Características:**
- Generación automática de escenarios para cada endpoint
- Estructura Given-When-Then
- Validaciones de request/response
- Configuraciones de background

### ⚡ jmeter_generator
- **Descripción**: Genera planes de prueba JMeter .jmx para testing de performance
- **Entrada**: Datos fuente (Swagger o Features) + tipo + archivo de salida
- **Salida**: Archivo .jmx listo para JMeter

**Incluye:**
- Thread Groups con parámetros configurables
- HTTP requests para todos los endpoints
- Headers requeridos y trazado UUID
- Request bodies para operaciones POST/PUT

### 🔄 complete_workflow
- **Descripción**: Ejecuta el pipeline completo en una sola operación
- **Flujo**: Swagger Analysis → Feature Generation → JMeter Generation
- **Entrada**: URL de Swagger + directorio de salida
- **Salida**: Conjunto completo de artefactos de testing

## 📋 Prerequisitos

- **Python**: 3.13 o superior
- **uv**: Package manager (recomendado) o pip
- **VS Code**: Para usar el servidor MCP
- **Git**: Para clonar el repositorio

## 🛠️ Instalación y Configuración

### Paso 1: Clonar el Repositorio

```bash
git clone <repository-url>
cd mcp-alaiia
```

### Paso 2: Instalar Dependencias

**Opción A: Con uv (recomendado)**
```bash
# Instalar uv si no lo tienes
pip install uv

# Crear entorno virtual e instalar dependencias
uv venv
uv pip install fastmcp pydantic httpx pyyaml
```

**Opción B: Con pip estándar**
```bash
# Crear entorno virtual
python -m venv .venv

# Activar entorno virtual
# En Windows:
.venv\Scripts\activate
# En Linux/Mac:
source .venv/bin/activate

# Instalar dependencias
pip install fastmcp pydantic httpx pyyaml
```

### Paso 3: Configurar VS Code

El archivo `.vscode/mcp.json` ya está configurado para usar Python global. Si prefieres usar el entorno virtual:

```json
{
    "servers": {
        "my-mcp-server-alaiia": {
            "type": "stdio",
            "command": ".venv\\Scripts\\python",
            "args": ["main.py"]
        }
    },
    "inputs": []
}
```

### Paso 4: Verificar Instalación

```bash
# Probar el servidor MCP
python main.py

# Deberías ver el mensaje de inicio del servidor FastMCP
```

## 🔧 Uso del Servidor MCP

### Desde VS Code

1. Asegúrate de tener la extensión MCP instalada
2. El servidor se configurará automáticamente con el archivo `.vscode/mcp.json`
3. Usa las 4 herramientas disponibles:
   - `swagger_analysis`
   - `feature_generator` 
   - `jmeter_generator`
   - `complete_workflow`

### Ejemplo de Uso Completo

```javascript
// Ejecutar flujo completo
complete_workflow({
    "swagger_url": "http://localhost:8080/v3/api-docs",
    "output_dir": "./output"
})
```

Esto generará:
- `./output/features/api_tests.feature` - Archivo Karate DSL
- `./output/test_plan_from_swagger.jmx` - Plan JMeter desde Swagger
- `./output/test_plan_from_features.jmx` - Plan JMeter desde Features

## 📁 Estructura del Proyecto

```
mcp-alaiia/
├── .vscode/
│   └── mcp.json              # Configuración MCP para VS Code
├── src/
│   ├── presentation/
│   │   └── mcp_server.py     # Servidor FastMCP con 4 herramientas
│   ├── shared/
│   └── tools/                # Herramientas ALAIIA organizadas por dominio
│       ├── swagger_analysis/
│       ├── feature_generator/
│       └── jmeter_generator/
├── output/                   # Directorio de archivos generados
├── main.py                   # Punto de entrada del servidor MCP
├── pyproject.toml           # Configuración del proyecto
└── README.md               # Este archivo
```

## 🔄 Flujos de Trabajo

### Flujo Individual
```
swagger_analysis → feature_generator
swagger_analysis → jmeter_generator
```

### Flujo Completo
```
complete_workflow (todo en uno)
```

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto está bajo la licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 🆘 Soporte

Para reportar bugs o solicitar nuevas funcionalidades, por favor abre un issue en el repositorio.

---

**Estado del Proyecto**: ✅ Funcional - Servidor MCP completamente operativo con FastMCP 2.12.4

## 🚨 Solución de Problemas

### Error de Codificación Unicode
Si encuentras errores como `UnicodeEncodeError`, asegúrate de que la configuración de VS Code use Python global en lugar del entorno virtual.

### Dependencias No Encontradas
Verifica que las dependencias estén instaladas:
```bash
python -c "import fastmcp, pydantic, httpx; print('Dependencies OK')"
```

### Servidor MCP No Responde
1. Verifica que el comando en `.vscode/mcp.json` sea correcto
2. Prueba ejecutar `python main.py` manualmente
3. Revisa que no haya otros procesos usando el mismo puerto

## 🏗️ Arquitectura

El proyecto sigue principios SOLID y arquitectura hexagonal:

```
src/
├── tools/
│   ├── swagger_analysis/
│   │   ├── domain/          # Modelos y reglas de negocio
│   │   ├── application/     # Servicios de aplicación
│   │   └── infrastructure/  # Implementaciones concretas
│   ├── feature_generator/
│   │   ├── domain/
│   │   ├── application/
│   │   └── infrastructure/
│   └── jmeter_generator/
│       ├── domain/
│       ├── application/
│       └── infrastructure/
└── mcp_tools.py            # Orquestador principal
```

## 🔧 Instalación

```bash
# Clonar el repositorio
git clone <repository-url>
cd mcp-alaiia

# Instalar dependencias
pip install -e .
```

## 📖 Uso

### Uso Programático

```python
from src.mcp_tools import MCPToolsOrchestrator

orchestrator = MCPToolsOrchestrator()

# Análisis de Swagger
swagger_result = await orchestrator.analyze_swagger_from_url(
    "https://petstore.swagger.io/v2/swagger.json"
)

# Generación de Features
features_result = await orchestrator.generate_features_from_swagger(
    swagger_result["data"], 
    "./output/features"
)

# Generación de JMeter
jmeter_result = await orchestrator.generate_jmeter_from_swagger(
    swagger_result["data"], 
    "./output/test_plan.jmx"
)

# Flujo completo
complete_result = await orchestrator.complete_workflow(
    "https://petstore.swagger.io/v2/swagger.json",
    "./output"
)
```

### Uso desde MCP

El servidor MCP está configurado para usar FastMCP y puede conectarse desde cualquier cliente MCP compatible:

```bash
# Ejecutar servidor MCP
python main.py
```

**Configuración en `.vscode/mcp.json`:**
```json
{
  "servers": {
    "my-mcp-server-alaiia": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "main.py"]
    }
  }
}
```

## 🔄 Flujo de Trabajo

1. **Swagger Analysis**: Analiza el contrato API desde una URL
2. **Feature Generation**: Genera archivos .feature basados en el análisis
3. **JMeter Generation**: Crea planes de prueba JMeter desde Swagger o Features

Las herramientas están diseñadas para trabajar en conjunto:
- La Herramienta 1 alimenta a las Herramientas 2 y 3
- La Herramienta 2 puede alimentar a la Herramienta 3 como alternativa

## 🎯 Principios de Diseño

- **SOLID**: Cada herramienta respeta los principios de responsabilidad única, abierto/cerrado, etc.
- **Hexagonal Architecture**: Separación clara entre dominio, aplicación e infraestructura
- **Dinámico**: No hay datos hardcodeados; todo se genera dinámicamente
- **Interoperabilidad**: Las herramientas se comunican entre sí de manera fluida

## 📁 Estructura de Salida

```
output/
├── features/
│   ├── pets_api_tests.feature
│   ├── store_api_tests.feature
│   └── user_api_tests.feature
├── test_plan_from_swagger.jmx
├── test_plan_from_features.jmx
└── swagger_analysis.json
```

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.