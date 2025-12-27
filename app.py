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
    """Página principal con el calendario."""
    user = None
    if session.get('user'):
        user = session['user']
    return render_template('index.html', centros=CENTROS, user=user)


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
    if not email or not password:
        flash('Email y contraseña requeridos', 'error')
        return redirect(url_for('login_view'))
    res = supabase_sign_up(email, password)
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
        try:
            prof = supabase_create_profile_service(user_id, email)
            if prof:
                app.logger.info('Profile creado para %s', user_id)
            else:
                app.logger.warning('No se creó profile para %s', user_id)
        except Exception as e:
            app.logger.exception('Error al crear profile: %s', e)

    flash('Registro exitoso. Por favor revise su correo (y la carpeta de no deseados) para confirmar su cuenta y poder iniciar sesión.', 'success')
    return redirect(url_for('login_view'))


@app.route('/auth/callback')
def auth_callback():
    """Manejar la confirmación de email desde Supabase."""
    access_token = request.args.get('access_token')
    refresh_token = request.args.get('refresh_token')
    token_type = request.args.get('token_type')
    expires_in = request.args.get('expires_in')
    error = request.args.get('error')
    error_description = request.args.get('error_description')

    if error:
        flash(f'Error en confirmación: {error_description}', 'error')
        return redirect(url_for('login_view'))

    if not access_token:
        flash('Token de acceso faltante', 'error')
        return redirect(url_for('login_view'))

    # Obtener info del usuario
    user = supabase_get_user(access_token)
    if not user:
        flash('Error al obtener información del usuario', 'error')
        return redirect(url_for('login_view'))

    # Establecer sesión
    session['access_token'] = access_token
    session['user'] = user
    if refresh_token:
        session['refresh_token'] = refresh_token

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
        email = session.get('user', {}).get('email')
        if email:
            profile = supabase_create_profile_service(user_id, email)
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
    """Descargar horario como PDF."""
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
    
    # Obtener horario
    schedules = supabase_get_schedules(access_token, user_id)
    schedule = next((s for s in schedules if str(s.get('id')) == str(schedule_id)), None)
    
    if not schedule:
        flash('Horario no encontrado', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        # Crear PDF
        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Título
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#5a67d8'),
            spaceAfter=30,
            alignment=1
        )
        story.append(Paragraph(schedule.get('name', 'Mi Horario'), title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Información
        info_style = ParagraphStyle(
            'Info',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#6b7280')
        )
        story.append(Paragraph(f"<b>ID:</b> {schedule.get('id')}", info_style))
        
        created_at = schedule.get('created_at', 'N/A')
        if created_at:
            story.append(Paragraph(f"<b>Creado:</b> {created_at}", info_style))
        
        if schedule.get('notes'):
            story.append(Spacer(1, 0.15*inch))
            story.append(Paragraph(f"<b>Notas:</b>", info_style))
            story.append(Paragraph(schedule.get('notes'), info_style))
        
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph("Información General", styles['Heading2']))
        story.append(Spacer(1, 0.1*inch))
        
        # Tabla con información
        data = [['Propiedad', 'Valor']]
        data.append(['Nombre', schedule.get('name', 'N/A')])
        data.append(['ID', schedule.get('id', 'N/A')[:8] + '...'])
        data.append(['Fecha de Creación', str(schedule.get('created_at', 'N/A'))[:10]])
        data.append(['Color', schedule.get('color', '#000000')])
        
        table = Table(data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#5a67d8')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(table)
        
        # Generar PDF
        doc.build(story)
        pdf_buffer.seek(0)
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"{schedule.get('name', 'horario').replace(' ', '_')}.pdf"
        )
    except Exception as e:
        print(f'Error generating PDF: {e}')
        flash('Error al generar PDF', 'error')
        return redirect(url_for('view_schedule', schedule_id=schedule_id))

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