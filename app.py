from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, send_file
from livereload import Server
import requests
from bs4 import BeautifulSoup
import re
import time
import os
from dotenv import load_dotenv
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from datetime import datetime
from supabase_client import (
    supabase_sign_in,
    supabase_sign_up,
    supabase_get_schedules,
    supabase_create_schedule,
    supabase_create_profile_service,
    supabase_get_user,
    supabase_get_profile,
    supabase_delete_schedule,
    supabase_update_schedule,
    supabase_get_schedule_items,
    supabase_delete_schedule_items,
    supabase_reset_password_email,
    supabase_update_user_password,
    supabase_get_professor_ratings,
    supabase_add_professor_rating,
    supabase_get_all_professor_averages,
)

app = Flask(__name__)
load_dotenv()
app.secret_key = os.environ.get('FLASK_SECRET', 'dev-secret')

# Constantes del SIIAU
POST_URL = "https://siiauescolar.siiau.udg.mx/wal/sspseca.consulta_oferta"

HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "es-419,es;q=0.9",
    "Cache-Control": "max-age=0",
    "DNT": "1",
    "Origin": "https://siiauescolar.siiau.udg.mx",
    "Referer": "https://siiauescolar.siiau.udg.mx/wal/sspseca.forma_consulta",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
    "Content-Type": "application/x-www-form-urlencoded"
}

COOKIES = {
    "21082024SIIAUSESION": "1542435678",
    "21082024SIIAUUDG": "1692153",
    "07122024SIIAUSESION": "611522407",
    "07122024SIIAUUDG": "1692153",
    "06082025SIIAUSESION": "1015485614",
    "06082025SIIAUUDG": "1692153",
    "07082025SIIAUUDG": "1692153",
    "07082025SIIAUSESION": "588707643",
    "cookiesession1": "678B287E4E1A792C793C3634D5FF5F58",
    "03102025SIIAUSESION": "1280826723",
    "03102025SIIAUUDG": "1692153",
    "05102025SIIAUSESION": "1231724026",
    "05102025SIIAUUDG": "1692153"
}

# Centros universitarios
CENTROS = {
    '3': 'CUTLAJO - de Tlajomulco',
    '4': 'CUGDL - de Guadalajara',
    '5': 'CUTlAQUEPAQUE - de Tlaquepaque',
    '6': 'CUCHAPALA - de Chapala',
    'A': 'CUAAD - Arte, Arquitectura y Diseño',
    'B': 'CUCBA - Ciencias Biológicas y Agropecuarias',
    'C': 'CUCEA - Ciencias Económico Administrativas',
    'D': 'CUCEI - Ciencias Exactas e Ingenierías',
    'E': 'CUCS - Ciencias de la Salud',
    'F': 'CUCSH - Ciencias Sociales y Humanidades',
    'G': 'CUALTOS - de los Altos',
    'H': 'CUCIENEGA - de la Ciénega',
    'I': 'CUCOSTA - de la Costa',
    'J': 'CUCSUR - de la Costa Sur',
    'K': 'CUSUR - del Sur',
    'M': 'CUVALLES - de los Valles',
    'N': 'CUNORTE - del Norte',
    'O': 'CUCEI SEDE VALLES',
    'P': 'CUCSUR SEDE VALLES',
    'Q': 'CUCEI SEDE NORTE',
    'R': 'CUALTOS SEDE NORTE',
    'S': 'CUCOSTA SEDE NORTE',
    'T': 'SEDE TLAJOMULCO',
    'U': 'CULAGOS - DE LOS LAGOS',
    'V': 'CICLO DE VERANO',
    'W': 'CUCEA SEDE VALLE',
    'X': 'SIST DE UNIVERSIDAD VIRTUAL',
    'Y': 'ESCUELAS INCORPORADAS',
    'Z': 'CUTONALA - de Tonalá',
}

def extract_rows_from_table(soup):
    """Extrae las filas de la tabla principal, expandiendo los horarios."""
    tabla = soup.find('table')
    if not tabla:
        return []

    filas = tabla.find_all('tr', recursive=False)
    datos_finales = []
    for tr in filas:
        tds = tr.find_all('td', recursive=False)
        if not tds or not re.match(r'^\d{4,}', tds[0].get_text(strip=True)):
            continue

        def txt(cell):
            return cell.get_text(' ', strip=True)

        # Información base de la materia
        base_info = {
            'NRC': txt(tds[0]),
            'Clave': txt(tds[1]) if len(tds) > 1 else '',
            'Materia': txt(tds[2]) if len(tds) > 2 else '',
            'Sec': txt(tds[3]) if len(tds) > 3 else '',
            'CR': txt(tds[4]) if len(tds) > 4 else '',
            'CUP': txt(tds[5]) if len(tds) > 5 else '',
            'DIS': txt(tds[6]) if len(tds) > 6 else '',
        }

        # Extraer profesor
        profesor = ''
        if len(tds) > 8:
            inner_prof = tds[8].find('table')
            if inner_prof:
                prof_tr = inner_prof.find('tr')
                if prof_tr and len(prof_tr.find_all('td')) >= 2:
                    profesor = prof_tr.find_all('td')[1].get_text(' ', strip=True)
                elif prof_tr:
                    profesor = txt(prof_tr)
            else:
                profesor = txt(tds[8])
        base_info['Profesor'] = profesor

        # Procesar horario
        horario_str = ''
        if len(tds) > 7:
            inner_table = tds[7].find('table')
            if inner_table:
                parts = []
                for ir in inner_table.find_all('tr'):
                    parts.append(' | '.join([c.get_text(' ', strip=True) for c in ir.find_all('td')]))
                horario_str = ' ; '.join(p for p in parts if p.strip())
            else:
                horario_str = txt(tds[7])

        if horario_str.strip():
            sesiones = horario_str.split(';')
            for sesion in sesiones:
                partes = [p.strip() for p in sesion.split('|')]
                fila_expandida = base_info.copy()
                fila_expandida.update({
                    'SesionNum': partes[0] if len(partes) > 0 else '',
                    'Horas': partes[1] if len(partes) > 1 else '',
                    'Dias': partes[2] if len(partes) > 2 else '',
                    'Edificio': partes[3] if len(partes) > 3 else '',
                    'Aula': partes[4] if len(partes) > 4 else '',
                    'Periodo': partes[5] if len(partes) > 5 else '',
                })
                datos_finales.append(fila_expandida)
        else:
            fila_vacia = base_info.copy()
            fila_vacia.update({
                'SesionNum': '', 'Horas': '', 'Dias': '', 'Edificio': '', 'Aula': '', 'Periodo': ''
            })
            datos_finales.append(fila_vacia)

    return datos_finales

def get_next_p_start(soup):
    """Busca el siguiente valor de p_start."""
    form = soup.find('form', attrs={'name': True})
    if not form:
        inp = soup.find('input', attrs={'name': 'p_start'})
    else:
        inp = form.find('input', attrs={'name': 'p_start'})
    if inp and inp.get('value'):
        try:
            return int(inp.get('value'))
        except ValueError:
            return None
    return None

def fetch_all_pages(session, post_url, payload_base):
    """Itera páginas y acumula resultados."""
    results = []
    p_start = 0
    seen_any = False
    page = 0

    while page < 5:  # Límite de páginas para evitar bucles infinitos
        page += 1
        payload = dict(payload_base)
        payload['p_start'] = str(p_start)

        try:
            resp = session.post(post_url, data=payload, timeout=30)
            if resp.status_code != 200:
                break

            soup = BeautifulSoup(resp.text, 'html.parser')
            page_rows = extract_rows_from_table(soup)

            if page_rows:
                seen_any = True
                results.extend(page_rows)
            else:
                if seen_any or page == 1:
                    break

            # Buscar siguiente página
            next_button = soup.find('input', {'value': '100 Próximos'})
            if next_button:
                mostrar_val = int(payload_base.get('mostrarp', '100'))
                p_start += mostrar_val
                continue

            next_p = get_next_p_start(soup)
            if next_p and next_p > p_start:
                p_start = next_p
                continue

            break

            time.sleep(1)

        except Exception as e:
            print(f"Error en página {page}: {str(e)}")
            break

    return results

@app.route('/')
def index():
    """Página de inicio (Landing Page)."""
    user = None
    profile = None
    if session.get('user'):
        user = session['user']
        if session.get('access_token'):
            profile = supabase_get_profile(session['access_token'], user['id'])
    return render_template('index.html', user=user, profile=profile)

@app.route('/feedback')
def feedback():
    """Página de sugerencias."""
    user = session.get('user')
    profile = None
    if user and session.get('access_token'):
        profile = supabase_get_profile(session['access_token'], user['id'])
    return render_template('feedback.html', user=user, profile=profile)

@app.route('/planner')
def planner():
    """Página del planificador de horarios."""
    user = None
    profile = None
    is_pro = False
    if session.get('user'):
        user = session['user']
        if session.get('access_token'):
            profile = supabase_get_profile(session['access_token'], user['id'])
            is_pro = profile.get('is_pro', False) if profile else False
            
    return render_template('planner.html', centros=CENTROS, user=user, profile=profile, is_pro=is_pro)

@app.route('/beneficios')
def beneficios():
    """Redirige a la página externa de beneficios UDG."""
    return redirect("https://beneficios.diferente.page/")


@app.route('/login')
def login_view():
    return render_template('signin.html')


@app.route('/signup')
def signup_view():
    return render_template('signup.html')


@app.route('/auth/login', methods=['POST'])
def auth_login():
    data = request.form
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        flash('Email y contraseña requeridos', 'error')
        return redirect(url_for('login_view'))
    res = supabase_sign_in(email, password)
    if not res or 'access_token' not in res:
        flash('Error al autenticar', 'error')
        return redirect(url_for('login_view'))
    session['access_token'] = res['access_token']
    session['user'] = res['user']
    return redirect(url_for('dashboard'))


@app.route('/auth/register', methods=['POST'])
def auth_register():
    data = request.form
    email = data.get('email')
    password = data.get('password')
    confirm_password = data.get('confirm_password')
    full_name = data.get('full_name')
    
    if not email or not password:
        flash('Email y contraseña requeridos', 'error')
        return redirect(url_for('signup_view'))
        
    if password != confirm_password:
        flash('Las contraseñas no coinciden', 'error')
        return redirect(url_for('signup_view'))
        
    res = supabase_sign_up(email, password, full_name)
    if not res:
        flash('Error de conexión con el servicio de autenticación', 'error')
        return redirect(url_for('login_view'))

    # Verificar si la respuesta contiene 'user' o es el objeto usuario directamente
    user = None
    if 'user' in res:
        user = res['user']
    elif 'id' in res and 'email' in res:
        user = res

    if not user:
        # Intentar obtener mensaje de error específico
        error_msg = res.get('msg') or res.get('error_description') or res.get('message') or res.get('error')
        
        if not error_msg:
            error_msg = f"Respuesta desconocida del servidor: {res}"
        
        error_str = str(error_msg)

        if "security purposes" in error_str and "seconds" in error_str:
             flash('Por seguridad, debes esperar unos segundos antes de intentar registrarte de nuevo.', 'error')
        elif "User already registered" in error_str:
             flash('Este correo ya está registrado. Intenta iniciar sesión.', 'error')
        else:
             flash(f'Error al registrar: {error_str}', 'error')
        
        return redirect(url_for('login_view'))

    user_id = user.get('id') if user else None
    # Intentar crear profile en la base de datos usando Service Role (backend)
    if user_id:
        import time
        # Pequeña espera para asegurar que Supabase Auth haya propagado el usuario
        time.sleep(1) 
        try:
            prof = supabase_create_profile_service(user_id, email, full_name)
            if prof:
                app.logger.info('Profile creado para %s', user_id)
            else:
                # Reintento si falló (posible race condition)
                time.sleep(2)
                prof = supabase_create_profile_service(user_id, email, full_name)
                if prof:
                    app.logger.info('Profile creado para %s en el segundo intento', user_id)
                else:
                    app.logger.warning('No se pudo crear el profile para %s tras reintento', user_id)
        except Exception as e:
            app.logger.exception('Error al crear profile: %s', e)

    flash('Registro exitoso. Por favor revise su correo (y la carpeta de no deseados) para confirmar su cuenta y poder iniciar sesión.', 'success')
    return redirect(url_for('login_view'))


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Página de recuperación de contraseña."""
    if request.method == 'POST':
        email = request.form.get('email')
        if not email:
            flash('Por favor ingresa tu correo', 'error')
            return redirect(url_for('forgot_password'))
        
        # Generar URL de callback absoluta
        callback_url = url_for('auth_callback', _external=True)
        
        success = supabase_reset_password_email(email, redirect_url=callback_url)
        if success:
            flash('Si el correo está registrado, recibirás un enlace para restablecer tu contraseña.', 'success')
        else:
            flash('Error al enviar el correo. Intenta más tarde.', 'error')
        
        return redirect(url_for('login_view'))
        
    return render_template('forgot_password.html')

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    """Página para establecer nueva contraseña."""
    # Verificar que el usuario esté autenticado (vía link de recuperación)
    if not session.get('access_token'):
        flash('Enlace inválido o expirado. Por favor solicita uno nuevo.', 'error')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')
        
        if not password or len(password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres', 'error')
            return redirect(url_for('reset_password'))
            
        if password != confirm:
            flash('Las contraseñas no coinciden', 'error')
            return redirect(url_for('reset_password'))
            
        # Actualizar contraseña en Supabase
        user, error_msg = supabase_update_user_password(session['access_token'], password)
        
        if user:
            flash('Has restablecido la contraseña con éxito.', 'success')
            session.clear() # Cerrar sesión para obligar a login con nueva pass
            return redirect(url_for('login_view'))
        else:
            flash(f'Error al actualizar la contraseña: {error_msg}', 'error')
            
    return render_template('reset_password.html')

@app.route('/auth/callback', methods=['GET', 'POST'])
def auth_callback():
    """Manejar la confirmación de email desde Supabase."""
    # Support both GET (query params) and POST (JSON body from JS fetch)
    if request.method == 'POST':
        data = request.get_json() or {}
        access_token = data.get('access_token')
        refresh_token = data.get('refresh_token')
        token_type = data.get('token_type')
        expires_in = data.get('expires_in')
        error = data.get('error')
        error_description = data.get('error_description')
        type_ = data.get('type')
    else:
        access_token = request.args.get('access_token')
        refresh_token = request.args.get('refresh_token')
        token_type = request.args.get('token_type')
        expires_in = request.args.get('expires_in')
        error = request.args.get('error')
        error_description = request.args.get('error_description')
        type_ = request.args.get('type')

    if error:
        msg = f'Error en confirmación: {error_description}'
        if request.method == 'POST':
            return jsonify({'error': msg}), 400
        flash(msg, 'error')
        return redirect(url_for('login_view'))

    if not access_token:
        msg = 'Token de acceso faltante'
        if request.method == 'POST':
            return jsonify({'error': msg}), 400
        flash(msg, 'error')
        return redirect(url_for('login_view'))

    # Obtener info del usuario
    user = supabase_get_user(access_token)
    if not user:
        msg = 'Error al obtener información del usuario'
        if request.method == 'POST':
            return jsonify({'error': msg}), 400
        flash(msg, 'error')
        return redirect(url_for('login_view'))

    # Establecer sesión
    session['access_token'] = access_token
    session['user'] = user
    if refresh_token:
        session['refresh_token'] = refresh_token

    # Si es recuperación de contraseña, redirigir a reset-password
    if type_ == 'recovery':
        if request.method == 'POST':
            return jsonify({'redirect': url_for('reset_password')})
        return redirect(url_for('reset_password'))

    if request.method == 'POST':
        return jsonify({'redirect': url_for('dashboard')}) # Or confirmation page
    return render_template('confirmation.html')


@app.route('/dashboard')
def dashboard():
    if not session.get('access_token'):
        return redirect(url_for('login_view'))
    access_token = session['access_token']
    user = session.get('user')
    user_id = user.get('id')
    
    # Obtener profile para verificar estado pro
    profile = supabase_get_profile(access_token, user_id)
    is_pro = profile.get('is_pro', False) if profile else False
    
    # Obtener horarios
    schedules = supabase_get_schedules(access_token, user_id)
    
    # Limitar horarios si no es pro
    max_schedules = 999 if is_pro else 1
    can_create_more = len(schedules) < max_schedules
    
    return render_template('dashboard.html', 
                         schedules=schedules, 
                         user=user,
                         profile=profile,
                         is_pro=is_pro,
                         can_create_more=can_create_more,
                         schedule_count=len(schedules),
                         max_schedules=max_schedules)


@app.route('/schedules/create', methods=['POST'])
def create_schedule():
    if not session.get('access_token'):
        flash('Debes iniciar sesión para guardar horarios', 'error')
        return redirect(url_for('login_view'))
    
    access_token = session['access_token']
    user_id = session['user']['id']
    
    # Verificar límite de horarios
    profile = supabase_get_profile(access_token, user_id)
    
    # Si no existe perfil, intentar crearlo (fix para error de FK)
    if not profile:
        print(f"Profile not found for user {user_id}, attempting to create one...")
        user_data = session.get('user', {})
        email = user_data.get('email')
        full_name = user_data.get('user_metadata', {}).get('full_name')
        if email:
            profile = supabase_create_profile_service(user_id, email, full_name)
            if profile:
                print("Profile created successfully")
            else:
                print("Failed to create profile")
        else:
            print("Cannot create profile: email not found in session")

    is_pro = profile.get('is_pro', False) if profile else False
    schedules = supabase_get_schedules(access_token, user_id)
    
    if not is_pro and len(schedules) >= 1:
        flash('Límite alcanzado. Upgrade a Pro para crear más horarios', 'error')
        return redirect(url_for('index'))
    
    name = request.form.get('name') or 'Mi horario'
    schedule_data = request.form.get('data', '{}')  # Datos del horario (JSON)
    
    print(f'Creating schedule: {name} for user {user_id}')
    print(f'Schedule data raw length: {len(schedule_data)}')
    
    # Parsear los datos JSON
    try:
        import json
        data_parsed = json.loads(schedule_data)
        if 'materias' in data_parsed:
            print(f"Data contains {len(data_parsed['materias'])} materias")
        else:
            print("Data does NOT contain 'materias' key")
    except Exception as e:
        print(f"Error parsing schedule data: {e}")
        data_parsed = {}
    
    s = supabase_create_schedule(access_token, user_id, name, data=data_parsed)
    if s:
        print(f'Schedule created successfully: {s}')
        flash(f'¡Horario "{name}" guardado exitosamente!', 'success')
        # Si s es una lista, obtener el primer elemento
        schedule_id = s[0]['id'] if isinstance(s, list) and len(s) > 0 else s.get('id') if isinstance(s, dict) else None
        if schedule_id:
            return redirect(url_for('view_schedule', schedule_id=schedule_id))
        return redirect(url_for('dashboard'))
    else:
        print('Failed to create schedule')
        flash('Error al guardar horario. Por favor intenta de nuevo.', 'error')
        return redirect(url_for('index'))

@app.route('/schedules/<schedule_id>/delete', methods=['POST'])
def delete_schedule(schedule_id):
    if not session.get('access_token'):
        return jsonify({'error': 'not authenticated'}), 401
    access_token = session['access_token']
    success = supabase_delete_schedule(access_token, schedule_id)
    if success:
        flash('Horario eliminado', 'success')
    else:
        flash('Error al eliminar horario', 'error')
    return redirect(url_for('dashboard'))

@app.route('/schedules/<schedule_id>/edit', methods=['POST'])
def edit_schedule(schedule_id):
    if not session.get('access_token'):
        return jsonify({'error': 'not authenticated'}), 401
    access_token = session['access_token']
    name = request.form.get('name')
    color = request.form.get('color')
    notes = request.form.get('notes')
    
    # Procesar items eliminados (DB)
    deleted_items = request.form.get('deleted_items')
    if deleted_items:
        try:
            # Split and strip, keep as strings to support both UUIDs and Integers
            item_ids = [id.strip() for id in deleted_items.split(',') if id.strip()]
            if item_ids:
                supabase_delete_schedule_items(access_token, item_ids)
        except Exception as e:
            print(f"Error deleting items: {e}")

    # Procesar actualización de metadatos y sincronización de nombre
    metadata_materias = request.form.get('metadata_materias')
    new_metadata = None
    
    try:
        # Siempre obtener metadatos actuales para sincronizar nombre y preservar datos
        schedules = supabase_get_schedules(access_token, session['user']['id'])
        current_schedule = next((s for s in schedules if str(s.get('id')) == str(schedule_id)), None)
        
        if current_schedule:
            new_metadata = current_schedule.get('metadata', {}) or {}
            
            # Si hay actualización de materias legacy
            if metadata_materias:
                import json
                new_metadata['materias'] = json.loads(metadata_materias)
                print(f"Updating metadata with {len(new_metadata['materias'])} materias")
            
            # Sincronizar nombre en metadatos si cambió
            if name:
                new_metadata['nombre'] = name
            
            # Guardar color y notas en metadatos (fallback por si no existen columnas)
            if color:
                new_metadata['color'] = color
            if notes:
                new_metadata['notes'] = notes
                
    except Exception as e:
        print(f"Error preparing metadata update: {e}")
    
    success = supabase_update_schedule(access_token, schedule_id, name=name, color=color, notes=notes, metadata=new_metadata)
    if success:
        if deleted_items:
            flash('Horario actualizado y materias eliminadas correctamente', 'success')
        else:
            flash('Horario actualizado correctamente', 'success')
        return redirect(url_for('view_schedule', schedule_id=schedule_id))
    else:
        flash('Error al actualizar horario', 'error')
        return redirect(url_for('dashboard'))

@app.route('/pricing')
def pricing():
    """Página de planes de precios."""
    user = session.get('user') if session.get('access_token') else None
    is_pro = False
    if user:
        profile = supabase_get_profile(session['access_token'], user['id'])
        is_pro = profile.get('is_pro', False) if profile else False
    return render_template('pricing.html', user=user, is_pro=is_pro)

@app.route('/professors')
def professors_view():
    """Página para calificar profesores."""
    user = None
    is_pro = False
    if session.get('user'):
        user = session['user']
        if session.get('access_token'):
            profile = supabase_get_profile(session['access_token'], user['id'])
            is_pro = profile.get('is_pro', False) if profile else False
            
    return render_template('professors.html', centros=CENTROS, user=user, is_pro=is_pro)

@app.route('/api/buscar_profesores', methods=['POST'])
def buscar_profesores():
    """API para buscar profesores únicos."""
    try:
        data = request.json
        centro = data.get('centro', '')
        carrera = data.get('carrera', '')
        ciclo = data.get('ciclo', '')

        payload = {
            "ciclop": ciclo,
            "cup": centro,
            "majrp": carrera,
            "crsep": "",
            "materiap": "",
            "horaip": "",
            "horafp": "",
            "edifp": "",
            "aulap": "",
            "ordenp": "0",
            "mostrarp": "500",
            "dispp": "1",
        }

        with requests.Session() as s:
            s.headers.update(HEADERS)
            s.cookies.update(COOKIES)
            materias = fetch_all_pages(s, POST_URL, payload)

        # Extraer profesores únicos y sus materias
        profesores_dict = {}
        for m in materias:
            prof = m.get('Profesor', '').strip()
            materia_nombre = m.get('Materia', '').strip()
            if prof and prof != '.' and prof != 'POR ASIGNAR':
                if prof not in profesores_dict:
                    profesores_dict[prof] = set()
                if materia_nombre:
                    profesores_dict[prof].add(materia_nombre)
        
        # Obtener promedios de calificaciones
        ratings_averages, _ = supabase_get_all_professor_averages()

        # Convertir a lista de objetos para el frontend
        profesores_lista = []
        for name in sorted(profesores_dict.keys()):
            rating_data = ratings_averages.get(name, {'average': 0, 'count': 0})
            profesores_lista.append({
                'nombre': name,
                'materias': sorted(list(profesores_dict[name])),
                'rating_average': rating_data['average'],
                'rating_count': rating_data['count']
            })

        return jsonify({
            'success': True,
            'profesores': profesores_lista,
            'total': len(profesores_lista)
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/rate_professor', methods=['POST'])
def rate_professor():
    """API para calificar a un profesor. Ahora permite calificaciones anónimas."""
    try:
        data = request.json
        prof_name = data.get('professor_name')
        rating = data.get('rating')
        comment = data.get('comment', '')
        
        if not prof_name or not rating:
            return jsonify({'success': False, 'error': 'Datos incompletos'}), 400
            
        # Intentar obtener info del usuario si está logueado
        access_token = session.get('access_token')
        user_id = session.get('user', {}).get('id') if session.get('user') else None

        res, error_msg = supabase_add_professor_rating(
            access_token,
            user_id,
            prof_name,
            int(rating),
            comment
        )
        
        if res:
            return jsonify({'success': True, 'data': res})
        else:
            # Manejar token expirado o errores de tabla
            error_str = str(error_msg)
            if "JWT expired" in error_str:
                return jsonify({'success': False, 'error': 'Tu sesión ha expirado. Por favor, inicia sesión de nuevo.', 'auth_error': True}), 401
            
            if "relation" in error_str and "does not exist" in error_str:
                error_msg = "La tabla 'professor_ratings' no existe en Supabase. Por favor ejecuta el SQL proporcionado."
            
            return jsonify({'success': False, 'error': error_msg}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/professor_ratings/<path:name>')
def get_professor_ratings(name):
    """API para obtener calificaciones de un profesor."""
    try:
        ratings, error = supabase_get_professor_ratings(name)
        if error:
             return jsonify({'success': False, 'error': error}), 500
        return jsonify({'success': True, 'ratings': ratings})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada', 'success')
    return redirect(url_for('index'))

@app.route('/schedules/<schedule_id>')
def view_schedule(schedule_id):
    """Ver detalles de un horario."""
    if not session.get('access_token'):
        return redirect(url_for('login_view'))
    
    access_token = session['access_token']
    user = session.get('user')
    user_id = user.get('id')
    
    # Obtener todos los horarios del usuario
    schedules = supabase_get_schedules(access_token, user_id)
    schedule = next((s for s in schedules if str(s.get('id')) == str(schedule_id)), None)
    
    if not schedule:
        flash('Horario no encontrado', 'error')
        return redirect(url_for('dashboard'))
    
    # Get schedule items from the database
    schedule_items = supabase_get_schedule_items(access_token, schedule_id)
    
    # SELF-HEALING: If no items in DB but metadata has materias, migrate them now
    if not schedule_items and schedule.get('metadata') and 'materias' in schedule.get('metadata', {}):
        print(f"Migrating legacy materias for schedule {schedule_id}...")
        materias = schedule['metadata']['materias']
        if materias:
            # Import here to avoid circular imports if any
            from supabase_client import supabase_create_schedule_items
            count, errors = supabase_create_schedule_items(access_token, schedule_id, materias)
            
            if errors:
                print(f"Migration errors: {errors}")
                flash(f"Error migrando materias: {errors[0]}", "error")
            else:
                # Refresh items
                schedule_items = supabase_get_schedule_items(access_token, schedule_id)
                print(f"Migration complete. Found {len(schedule_items)} items.")
                flash(f"Se migraron {count} materias al nuevo formato.", "success")

    profile = supabase_get_profile(access_token, user_id)
    is_pro = profile.get('is_pro', False) if profile else False
    
    return render_template('schedule_detail.html', 
                         schedule=schedule,
                         schedule_items=schedule_items, 
                         user=user,
                         is_pro=is_pro)


@app.route('/schedules/<schedule_id>/download-pdf')
def download_schedule_pdf(schedule_id):
    """Descargar horario como PDF con calendario visual."""
    if not session.get('access_token'):
        return redirect(url_for('login_view'))
    
    access_token = session['access_token']
    user = session.get('user')
    user_id = user.get('id')
    
    # Verificar si es Pro
    profile = supabase_get_profile(access_token, user_id)
    is_pro = profile.get('is_pro', False) if profile else False
    
    if not is_pro:
        flash('Esta función está disponible solo en Plan Pro', 'error')
        return redirect(url_for('view_schedule', schedule_id=schedule_id))
    
    # Obtener horario y items
    schedules = supabase_get_schedules(access_token, user_id)
    schedule = next((s for s in schedules if str(s.get('id')) == str(schedule_id)), None)
    
    if not schedule:
        flash('Horario no encontrado', 'error')
        return redirect(url_for('dashboard'))
    
    # Get schedule items from database
    schedule_items = supabase_get_schedule_items(access_token, schedule_id)
    
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter, landscape
        
        # Crear PDF en orientación horizontal para el calendario
        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=landscape(letter), 
                              topMargin=0.5*inch, bottomMargin=0.5*inch,
                              leftMargin=0.5*inch, rightMargin=0.5*inch)
        story = []
        styles = getSampleStyleSheet()
        
        # Título principal
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=12,
            alignment=1,
            fontName='Helvetica-Bold'
        )
        story.append(Paragraph(f"Horario UDG: {schedule.get('name', 'Mi Horario')}", title_style))
        
        # Subtítulo con info
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#64748b'),
            alignment=1,
            spaceAfter=20
        )
        user_name = profile.get('full_name', user.get('email', ''))
        story.append(Paragraph(f"{user_name} • Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", subtitle_style))
        
        # Preparar datos del calendario
        schedule_data = prepare_schedule_data(schedule, schedule_items)
        
        if schedule_data and 'materias' in schedule_data and schedule_data['materias']:
            # Crear calendario de horario
            story.append(Paragraph("Calendario de Clases", styles['Heading2']))
            story.append(Spacer(1, 0.15*inch))
            
            # Crear tabla de horario
            calendar_table = create_schedule_table(schedule_data)
            story.append(calendar_table)
            
            story.append(PageBreak())
            
            # Sección de materias detalladas
            story.append(Paragraph("Detalle de Materias", styles['Heading2']))
            story.append(Spacer(1, 0.15*inch))
            
            courses_table = create_courses_detail_table(schedule_data)
            story.append(courses_table)
        else:
            story.append(Paragraph("No hay materias registradas en este horario", subtitle_style))
        
        # Generar PDF
        doc.build(story)
        pdf_buffer.seek(0)
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"Horario_{schedule.get('name', 'UDG').replace(' ', '_')}.pdf"
        )
    except Exception as e:
        import traceback
        print(f'Error generating PDF: {e}')
        print(traceback.format_exc())
        flash('Error al generar PDF', 'error')
        return redirect(url_for('view_schedule', schedule_id=schedule_id))

def prepare_schedule_data(schedule, schedule_items):
    """Prepara los datos del horario para el PDF."""
    # Paleta de colores vibrantes para diferentes materias
    color_palette = [
        '#ef4444', '#f97316', '#f59e0b', '#84cc16', 
        '#22c55e', '#14b8a6', '#06b6d4', '#3b82f6',
        '#6366f1', '#8b5cf6', '#a855f7', '#d946ef',
        '#ec4899', '#f43f5e'
    ]
    
    # PRIORITY 1: Use metadata if available (has complete data: NRC, Professor, etc)
    metadata = schedule.get('metadata', {})
    if metadata and 'materias' in metadata and len(metadata['materias']) > 0:
        # Asignar colores a materias de metadata
        materias = metadata['materias']
        for idx, materia in enumerate(materias):
            if 'color' not in materia or not materia['color']:
                materia['color'] = color_palette[idx % len(color_palette)]
        return metadata
    
    # PRIORITY 2: Fallback to schedule_items (only has basic data: title, day, time)
    if schedule_items and len(schedule_items) > 0:
        # Agrupar items por materia
        materias_dict = {}
        color_idx = 0
        
        for item in schedule_items:
            key = item.get('course_code') or item.get('title')
            if key not in materias_dict:
                # Asignar color único a cada materia
                materias_dict[key] = {
                    'Materia': item.get('title', 'Sin nombre'),
                    'Profesor': item.get('instructor', 'N/A'),  # Will be empty - column doesn't exist in DB
                    'NRC': item.get('nrc', 'N/A'),  # Will be empty - column doesn't exist in DB
                    'Clave': item.get('course_code', ''),
                    'color': color_palette[color_idx % len(color_palette)],
                    'horarios': []
                }
                color_idx += 1
            
            materias_dict[key]['horarios'].append({
                'horas': f"{item.get('start_time', '')}-{item.get('end_time', '')}",
                'dias': item.get('day', ''),
                'edificio': item.get('building', ''),
                'aula': item.get('room', '')  # Will be empty - column doesn't exist in DB
            })
        
        return {'materias': list(materias_dict.values())}
    
    return {'materias': []}

def create_schedule_table(schedule_data):
    """Crea la tabla del calendario de horario."""
    dias_nombres = ['', 'L', 'M', 'Mi', 'J', 'V', 'S']  # Nombres cortos para ahorrar espacio
    horas_range = range(7, 22)  # 7 AM a 10 PM
    
    # Preparar matriz de clases por hora y día
    grid = {}
    for hora in horas_range:
        grid[hora] = {dia: [] for dia in range(1, 7)}
    
    # Llenar grid con materias
    for materia in schedule_data.get('materias', []):
        for horario in materia.get('horarios', []):
            horas_str = horario.get('horas', '')
            dias_val = horario.get('dias', '')
            
            # Parsear horas
            start_hour, end_hour = parse_hours(horas_str)
            if start_hour is None:
                continue
            
            # Parsear días
            dias_list = parse_days(dias_val)
            
            for dia in dias_list:
                for hora in range(int(start_hour), int(end_hour) + 1):
                    if hora in grid and dia in grid[hora]:
                        grid[hora][dia].append({
                            'nombre': materia['Materia'],
                            'edificio': horario.get('edificio', ''),
                            'aula': horario.get('aula', ''),
                            'color': materia.get('color', '#3b82f6')
                        })
    
    # Construir tabla
    data = []
    header_row = ['Hora'] + [dias_nombres[i] for i in range(1, 7)]
    data.append(header_row)
    
    for hora in horas_range:
        row = [f"{hora}:00"]
        for dia in range(1, 7):
            clases = grid[hora][dia]
            if clases:
                # Mostrar primera clase de esa celda
                clase = clases[0]
                # Nombre corto para que quepa
                nombre_corto = clase['nombre'][:18]
                edificio = clase.get('edificio', '')
                aula = clase.get('aula', '')
                # Mostrar edificio + aula si ambos existen
                location = f"{edificio} {aula}" if edificio and aula else aula
                cell_text = f"{nombre_corto}\n{location[:10]}"
                row.append(cell_text)
            else:
                row.append('')
        data.append(row)
    
    # Crear tabla con dimensiones ajustadas para landscape
    col_widths = [0.5*inch] + [1.4*inch] * 6  # Reducido para que quepa en la página
    table = Table(data, colWidths=col_widths, rowHeights=0.3*inch)  # Altura reducida
    
    # Estilo base
    table_style_commands = [
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Todo centrado
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        
        # Body
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 7),  # Fuente más pequeña
        ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#f1f5f9')),
        
        # Grid
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#1e40af')),
    ]
    
    # Agregar colores de fondo a las celdas con clases
    for hora_idx, hora in enumerate(horas_range):
        for dia in range(1, 7):
            clases = grid[hora][dia]
            if clases:
                clase = clases[0]
                color_hex = clase['color']
                try:
                    # Convertir color hex a color más claro para fondo
                    if color_hex.startswith('#'):
                        bg_color = colors.HexColor(color_hex)
                        # Aplicar color a la celda
                        row_idx = hora_idx + 1  # +1 porque row 0 es header
                        col_idx = dia  # dia ya es 1-6
                        table_style_commands.append(
                            ('BACKGROUND', (col_idx, row_idx), (col_idx, row_idx), bg_color)
                        )
                        # Texto blanco para mejor contraste
                        table_style_commands.append(
                            ('TEXTCOLOR', (col_idx, row_idx), (col_idx, row_idx), colors.whitesmoke)
                        )
                except:
                    # Si falla el color, usar azul default
                    pass
    
    table_style = TableStyle(table_style_commands)
    table.setStyle(table_style)
    return table

def create_courses_detail_table(schedule_data):
    """Crea tabla detallada de materias."""
    from reportlab.platypus import Paragraph
    from reportlab.lib.styles import getSampleStyleSheet
    
    styles = getSampleStyleSheet()
    
    # Estilo para el header
    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.whitesmoke,
        fontName='Helvetica-Bold',
        alignment=0  # LEFT
    )
    
    # Estilo para el body
    body_style = ParagraphStyle(
        'BodyStyle',
        parent=styles['Normal'],
        fontSize=7,
        fontName='Helvetica',
        alignment=0,  # LEFT
        leading=9  # Espaciado entre líneas
    )
    
    # Header row con Paragraphs
    data = [[
        Paragraph('Materia', header_style),
        Paragraph('NRC', header_style),
        Paragraph('Profesor', header_style),
        Paragraph('Día', header_style),
        Paragraph('Horario', header_style),
        Paragraph('Aula', header_style)
    ]]
    
    for materia in schedule_data.get('materias', []):
        for horario in materia.get('horarios', []):
            dias_str = parse_days_to_string(horario.get('dias', ''))
            row = [
                Paragraph(materia.get('Materia', ''), body_style),
                Paragraph(materia.get('NRC', ''), body_style),
                Paragraph(materia.get('Profesor', ''), body_style),
                Paragraph(dias_str, body_style),
                Paragraph(horario.get('horas', ''), body_style),
                Paragraph(f"{horario.get('edificio', '')} {horario.get('aula', '')}", body_style)
            ]
            data.append(row)
    
    # Ajustar anchos para landscape con 6 columnas (total: ~10 inches disponibles)
    table = Table(data, colWidths=[1.8*inch, 0.7*inch, 2.2*inch, 0.6*inch, 1.1*inch, 1.0*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#1e40af')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    return table

def parse_hours(hours_str):
    """Parsea string de horas tipo '08:00-10:00' o '0800-1000'."""
    if not hours_str or 'null' in str(hours_str):
        return None, None
    
    parts = str(hours_str).split('-')
    if len(parts) < 2:
        return None, None
    
    try:
        start = parts[0].strip()
        end = parts[1].strip()
        
        # Si tiene formato HH:MM
        if ':' in start:
            start_hour = int(start.split(':')[0])
            end_hour = int(end.split(':')[0])
        else:
            # Formato HHMM
            start_hour = int(start[:2]) if len(start) >= 2 else int(start)
            end_hour = int(end[:2]) if len(end) >= 2 else int(end)
        
        return start_hour, end_hour
    except:
        return None, None

def parse_days(days_val):
    """Parsea días a lista de números (1=Lun, 2=Mar, etc)."""
    if days_val is None:
        return []
    
    # Si es número directo
    if isinstance(days_val, int):
        return [days_val]
    
    days_str = str(days_val).upper()
    
    # Si es solo dígitos
    if days_str.isdigit():
        return [int(days_str)]
    
    # Parsear formato de letras
    days = []
    if 'L' in days_str and 'M' not in days_str: days.append(1)  # Lunes solo
    if 'M' in days_str and 'I' not in days_str and 'W' not in days_str: days.append(2)  # Martes
    if 'I' in days_str or 'W' in days_str or ('M' in days_str and 'I' in days_str): days.append(3)  # Miércoles
    if 'J' in days_str: days.append(4)  # Jueves
    if 'V' in days_str: days.append(5)  # Viernes
    if 'S' in days_str and 'V' not in days_str: days.append(6)  # Sábado
    
    return days

def parse_days_to_string(days_val):
    """Convierte días a string legible (L, M, Mi, J, V, S)."""
    days_list = parse_days(days_val)
    dias_map = {1: 'L', 2: 'M', 3: 'Mi', 4: 'J', 5: 'V', 6: 'S'}
    return ' '.join([dias_map.get(d, '') for d in days_list])

@app.route('/favicon.ico')
def favicon():
    """Servir favicon."""
    return '', 204

@app.route('/api/buscar_materias', methods=['POST'])
def buscar_materias():
    """API para buscar materias."""
    try:
        data = request.json
        centro = data.get('centro', '')
        carrera = data.get('carrera', '')
        ciclo = data.get('ciclo', '')

        # Construir payload
        payload = {
            "ciclop": ciclo,
            "cup": centro,
            "majrp": carrera,
            "crsep": "",
            "materiap": "",
            "horaip": "",
            "horafp": "",
            "edifp": "",
            "aulap": "",
            "ordenp": "0",
            "mostrarp": "500",
            "dispp": "1",
        }

        # Realizar búsqueda
        with requests.Session() as s:
            s.headers.update(HEADERS)
            s.cookies.update(COOKIES)
            materias = fetch_all_pages(s, POST_URL, payload)

        return jsonify({
            'success': True,
            'materias': materias,
            'total': len(materias)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/get_centros')
def get_centros():
    """API para obtener lista de centros."""
    return jsonify(CENTROS)

if __name__ == '__main__':
    app.run(debug=True, port=5001)