# 📚 Planificador de Horario Académico - SIIAU UDG

> Aplicación web completa para planificar horarios académicos, consultar materias disponibles y evaluar profesores de la Universidad de Guadalajara.


<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/Flask-2.0+-green.svg" alt="Flask">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
  <img src="https://img.shields.io/badge/UDG-SIIAU-red.svg" alt="UDG">
</p>

<p align="center">
  <a href="#-características-principales">Características</a> •
  <a href="#-demo">Demo</a> •
  <a href="#-instalación">Instalación</a> •
  <a href="#-guía-de-uso">Guía de Uso</a> •
  <a href="#-tecnologías">Tecnologías</a> •
  <a href="#-contribuir">Contribuir</a>
</p>

---

## 📸 Demo

<div align="center">

### Vista de inicio
><img src="static\assets\home.png">

### Planificador de Horarios
><img src="static\assets\planner.png">

### Evaluación de Profesores
><img src="static\assets\professors.png">

</div>

> **💡 Nota**: Este proyecto te permite consultar materias del SIIAU, crear horarios personalizados, guardarlos en tu cuenta, exportarlos en PDF y calificar a tus profesores de manera anónima.

---

## ⚡ Inicio Rápido

```bash
# Clonar el repositorio
git clone https://github.com/moisesibanez17/Planificador-de-Horario.git
cd Planificador-de-Horario

# Crear entorno virtual e instalar dependencias
python -m venv venv
venv\Scripts\activate  # En Windows
pip install -r requirements.txt

# Configurar variables de entorno (ver sección Instalación)
# Crear archivo .env con tus credenciales de Supabase

# Ejecutar la aplicación
python app.py
```

Luego abre tu navegador en **http://localhost:5000** 🚀

---

## 🌟 Características Principales

### 📅 Planificador de Horarios
- **Búsqueda de materias** por centro universitario y carrera
- **Calendario semanal interactivo** con visualización de 7:00 AM a 9:00 PM
- **Detección automática de conflictos** de horario
- **Colores automáticos** para identificar cada materia fácilmente
- **Exportación a PDF** con calendario visual profesional
- **Múltiples horarios** personalizados guardados en tu cuenta

### 👤 Sistema de Usuarios
- **Registro y autenticación** con Supabase
- **Confirmación por email** para validar cuentas
- **Recuperación de contraseña** mediante email
- **Dashboard personalizado** para gestionar horarios
- **Sesiones seguras** con Flask

### 👨‍🏫 Evaluación de Profesores
- **Búsqueda de profesores** con autocompletado
- **Calificaciones anónimas** en múltiples categorías:
  - Claridad de explicación
  - Disponibilidad
  - Justicia en evaluaciones
  - Puntualidad
- **Visualización de promedios** y estadísticas
- **Comentarios opcionales** sobre experiencias

### 📄 Generación de PDFs
- **Calendario visual** con horarios organizados por día y hora
- **Tabla detallada** con información completa de cada materia
- **Códigos de colores** para identificar materias
- **Información completa**: NRC, profesor, edificio, aula, días y horarios

### 💬 Sistema de Retroalimentación
- Envío de **sugerencias y reportes** de errores
- Interfaz dedicada para **feedback de usuarios**

---

## 🚀 Instalación

### Requisitos Previos
- Python 3.8 o superior
- Cuenta en [Supabase](https://supabase.com) (gratis)
- Git

### Paso 1: Clonar el Repositorio
```bash
git clone https://github.com/moisesibanez17/Planificador-de-Horario.git
cd Planificador-de-Horario
```

### Paso 2: Crear Entorno Virtual
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

### Paso 3: Instalar Dependencias
```bash
pip install -r requirements.txt
```

### Paso 4: Configurar Variables de Entorno
Crea un archivo `.env` en la raíz del proyecto con las siguientes variables:

```env
# Supabase Configuration
SUPABASE_URL=tu_supabase_url
SUPABASE_KEY=tu_supabase_anon_key

# Flask Configuration
FLASK_SECRET=tu_clave_secreta_aqui
```

> **Nota**: Obtén tus credenciales de Supabase desde el [dashboard de tu proyecto](https://app.supabase.com)

### Paso 5: Configurar Base de Datos en Supabase

Ejecuta las siguientes consultas SQL en el SQL Editor de Supabase:

```sql
-- Tabla de horarios
CREATE TABLE schedules (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla de items de horario
CREATE TABLE schedule_items (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  schedule_id UUID REFERENCES schedules(id) ON DELETE CASCADE,
  nrc TEXT,
  materia TEXT,
  clave TEXT,
  seccion TEXT,
  creditos TEXT,
  cupo TEXT,
  disponible TEXT,
  profesor TEXT,
  edificio TEXT,
  aula TEXT,
  dias TEXT,
  horas TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla de calificaciones de profesores
CREATE TABLE professor_ratings (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  professor_name TEXT NOT NULL,
  user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
  clarity INTEGER CHECK (clarity BETWEEN 1 AND 5),
  availability INTEGER CHECK (availability BETWEEN 1 AND 5),
  fairness INTEGER CHECK (fairness BETWEEN 1 AND 5),
  punctuality INTEGER CHECK (punctuality BETWEEN 1 AND 5),
  comment TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices para mejor rendimiento
CREATE INDEX idx_schedules_user_id ON schedules(user_id);
CREATE INDEX idx_schedule_items_schedule_id ON schedule_items(schedule_id);
CREATE INDEX idx_professor_ratings_name ON professor_ratings(professor_name);
```

### Paso 6: Ejecutar la Aplicación

**FastAPI Version:**
```bash
uv icorn app:app --reload --port 5000
```

O directamente con Python:
```bash
python app.py
```

La aplicación estará disponible en: **http://localhost:5000**

- **Docs Interactiva**: http://localhost:5000/api/docs
- **ReDoc**: http://localhost:5000/api/redoc

---

## 📖 Guía de Uso

### 1️⃣ Crear una Cuenta
1. Haz clic en **"Registrarse"** en la página principal
2. Completa el formulario con tu información
3. Verifica tu email (revisa tu bandeja de spam)
4. Inicia sesión con tus credenciales

### 2️⃣ Crear un Horario
1. Accede a **Dashboard** → **Crear Horario**
2. Ingresa un nombre para tu horario
3. Selecciona tu **centro universitario**
4. Ingresa el **código de carrera** (opcional)
5. Haz clic en **"Buscar Materias"**
6. Haz clic en las materias para agregarlas
7. Guarda tu horario

### 3️⃣ Evaluar Profesores
1. Ve a la sección **"Profesores"**
2. Busca el nombre del profesor
3. Califica en las diferentes categorías
4. Agrega comentarios opcionales
5. Envía tu evaluación (anónima)

### 4️⃣ Exportar a PDF
1. Abre el horario que deseas exportar
2. Haz clic en **"Descargar PDF"**
3. El archivo se descargará automáticamente

---

## 🛠️ Tecnologías

### Backend
- **FastAPI** - Framework web moderno y rápido
- **Uvicorn** - Servidor ASGI de alta performance
- **Supabase** - Base de datos PostgreSQL y autenticación
- **BeautifulSoup4** - Web scraping del SIIAU
- **ReportLab** - Generación de PDFs
- **python-dotenv** - Gestión de variables de entorno

### Frontend
- **HTML5** - Estructura semántica
- **CSS3** - Diseño moderno y responsive
- **JavaScript (Vanilla)** - Interactividad del cliente
- **Fetch API** - Comunicación con el backend

### Otros
- **Requests** - Peticiones HTTP al SIIAU
- **Pandas** - Procesamiento de datos
- **LiveReload** - Recarga automática durante desarrollo

---

## 📂 Estructura del Proyecto

```
Planificador-de-Horario/
│
├── app.py                      # Aplicación principal Flask
├── supabase_client.py          # Cliente de Supabase
├── requirements.txt            # Dependencias del proyecto
├── .env                        # Variables de entorno (no versionado)
├── .gitignore                  # Archivos ignorados por Git
│
├── templates/                  # Plantillas HTML
│   ├── index.html             # Página de inicio
│   ├── planner.html           # Planificador público
│   ├── signin.html            # Inicio de sesión
│   ├── signup.html            # Registro
│   ├── dashboard.html         # Panel de usuario
│   ├── schedule_detail.html   # Detalle de horario
│   ├── professors.html        # Evaluación de profesores
│   ├── feedback.html          # Formulario de retroalimentación
│   ├── pricing.html           # Planes de precios
│   ├── forgot_password.html   # Recuperar contraseña
│   ├── reset_password.html    # Restablecer contraseña
│   └── confirmation.html      # Confirmación de email
│
└── static/                     # Archivos estáticos
    ├── css/                   # Estilos CSS
    ├── js/                    # Scripts JavaScript
    └── images/                # Imágenes y recursos
```

---

## 🔐 Seguridad

- ✅ **Autenticación segura** con Supabase
- ✅ **Sesiones encriptadas** con Flask
- ✅ **Variables de entorno** para credenciales sensibles
- ✅ **Validación de formularios** en cliente y servidor
- ✅ **Prevención de SQL injection** mediante ORM
- ✅ **HTTPS recomendado** para producción

---

## 🐛 Solución de Problemas

### "Error al conectar con Supabase"
- Verifica que las variables `SUPABASE_URL` y `SUPABASE_KEY` estén correctas en `.env`
- Confirma que tu proyecto de Supabase esté activo

### "Cookies de sesión inválidas"
- Las cookies del SIIAU en `app.py` deben actualizarse periódicamente
- Obtén nuevas cookies desde las herramientas de desarrollador de tu navegador

### "Error al generar PDF"
- Asegúrate de que ReportLab esté instalado: `pip install reportlab`
- Verifica que tengas permisos de escritura en el directorio

---

## 🤝 Contribuir

¡Las contribuciones son bienvenidas! Si deseas mejorar este proyecto:

1. Haz un **Fork** del repositorio
2. Crea una **rama** para tu feature (`git checkout -b feature/AmazingFeature`)
3. **Commit** tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. **Push** a la rama (`git push origin feature/AmazingFeature`)
5. Abre un **Pull Request**

---

## 📝 Notas Importantes

- 🔄 Las **cookies de sesión** del SIIAU deben actualizarse periódicamente para mantener el scraping funcionando
- ⚠️ La aplicación consulta directamente el sistema **SIIAU de la UDG** - úsala responsablemente
- 📧 Para producción, configura el **servicio de email** en Supabase
- 🌐 Centros universitarios soportados: CUCEI, CUCEA, CUCS, CUAAD, y más

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

---

## 👨‍💻 Autor

**Moises Ibañez**

- GitHub: [@moisesibanez17](https://github.com/moisesibanez17)
- Proyecto: [Planificador-de-Horario](https://github.com/moisesibanez17/Planificador-de-Horario)

---

## 🙏 Agradecimientos

- Universidad de Guadalajara por el sistema SIIAU
- Comunidad de desarrolladores de Flask y Python
- Supabase por su excelente plataforma

---

## 📞 Soporte

Si tienes preguntas o necesitas ayuda:
- 🐛 Reporta bugs en [Issues](https://github.com/moisesibanez17/Planificador-de-Horario/issues)
- 💡 Sugiere nuevas características en el formulario de feedback dentro de la aplicación
- 📧 Contacta al desarrollador directamente

---

**¡Disfruta planificando tus horarios! 📚✨**

