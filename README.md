# 📚 Planificador de Horario Académico - SIIAU UDG

Aplicación para extraer y planificar horarios académicos de la oferta del SIIAU de la Universidad de Guadalajara.

## 🌟 Características

### Aplicación Web (Nueva)
- **Búsqueda de Materias**: Busca materias por centro universitario y carrera
- **Calendario Semanal Interactivo**: Visualiza tu horario en un calendario visual
- **Detección de Conflictos**: Alerta automática cuando hay traslape de horarios
- **Interfaz Intuitiva**: Diseño moderno y fácil de usar
- **Colores Automáticos**: Cada materia se asigna un color diferente
- **Información Completa**: Ve horarios, profesores, edificios y aulas

### Aplicación de Escritorio (Original)
- Interfaz gráfica con Tkinter
- Búsqueda avanzada con filtros
- Exportación de datos a CSV

## 🚀 Instalación

### Aplicación Web
1. Instala las dependencias:
```bash
pip install -r requirements.txt
```

2. Ejecuta la aplicación web:
```bash
python app.py
```

3. Abre tu navegador en:
```
http://localhost:5000
```

### Aplicación de Escritorio
1. Instala las dependencias:
```bash
pip install -r requirements.txt
```

2. Ejecuta la interfaz de escritorio:
```bash
python gui.py
```

## 📖 Uso de la Aplicación Web

1. **Selecciona tu centro universitario** del menú desplegable
2. **Ingresa el código de tu carrera** (opcional, déjalo vacío para ver todas)
3. **Haz clic en "Buscar Materias"** para cargar las opciones disponibles
4. **Haz clic en cualquier materia** de la lista para agregarla al horario
5. **Visualiza tu horario** en el calendario semanal
6. **Remueve materias** haciendo clic en la X que aparece al pasar el mouse

## 🎨 Características Técnicas

- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Backend**: Flask (Python)
- **Scraping**: BeautifulSoup4
- **Diseño**: Responsive y adaptable a móviles

## 📱 Interfaz Web

La aplicación cuenta con:
- Panel lateral para búsqueda y lista de materias
- Calendario semanal con vista de 7:00 AM a 9:00 PM
- Leyenda de colores para identificar materias
- Sistema de alertas para conflictos de horario

## 🔧 Estructura del Proyecto

```
Avanzadas-UDG/
├── app.py                 # Aplicación web Flask
├── gui.py                 # Aplicación de escritorio (Tkinter)
├── requirements.txt       # Dependencias
├── templates/
│   └── index.html        # Plantilla HTML principal
└── static/
    ├── css/
    │   └── style.css     # Estilos
    └── js/
        └── app.js        # Lógica del cliente
```

## 📝 Notas

- Las cookies de sesión en el código deben actualizarse periódicamente
- La aplicación consulta directamente al sistema SIIAU de la UDG
- Se recomienda usar con responsabilidad

## 📄 Requisitos
- Python 3.8 o superior
- Las dependencias listadas en `requirements.txt`

## 👨‍💻 Créditos
Desarrollado por Moises Ibañez

Para más información, consulta la documentación incluida o contacta al desarrollador.

