import os
import requests

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_ANON_KEY = os.environ.get('SUPABASE_ANON_KEY')
SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_KEY')

headers_base = {
    'apikey': SUPABASE_ANON_KEY,
    'Content-Type': 'application/json'
}


def supabase_sign_in(email, password):
    """Sign in a user via Supabase auth and return json with access_token and user."""
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        return None
    url = f"{SUPABASE_URL}/auth/v1/token?grant_type=password"
    payload = {"email": email, "password": password}
    try:
        r = requests.post(url, json=payload, headers=headers_base, timeout=10)
        if r.ok:
            return r.json()
        # return error payload for debugging
        print('supabase_sign_in error:', r.status_code, r.text)
        return r.json()
    except Exception as e:
        print('supabase_sign_in exception:', str(e))
        return None


def supabase_sign_up(email, password, full_name=None):
    """Register a user via Supabase auth (returns user info if success)."""
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        return None
    url = f"{SUPABASE_URL}/auth/v1/signup"
    payload = {"email": email, "password": password}
    if full_name:
        payload["data"] = {"full_name": full_name}
    try:
        r = requests.post(url, json=payload, headers=headers_base, timeout=10)
        if r.ok:
            return r.json()
        print('supabase_sign_up error:', r.status_code, r.text)
        return r.json()
    except Exception as e:
        print('supabase_sign_up exception:', str(e))
        return None


def supabase_reset_password_email(email, redirect_url=None):
    """Send password reset email."""
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        return None
    url = f"{SUPABASE_URL}/auth/v1/recover"
    payload = {"email": email}
    if redirect_url:
        payload["gotrue_meta_security"] = {}
        payload["redirect_to"] = redirect_url
        
    try:
        r = requests.post(url, json=payload, headers=headers_base, timeout=10)
        # Supabase returns 200 OK even if email doesn't exist (security)
        # or empty JSON body {}
        if r.ok:
            return True
        print('supabase_reset_password_email error:', r.status_code, r.text)
        return False
    except Exception as e:
        print('supabase_reset_password_email exception:', str(e))
        return False


def supabase_update_user_password(access_token, new_password):
    """Update user password."""
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        return None, "Configuración de Supabase faltante"
    if not access_token:
        return None, "Token de acceso faltante (sesión expirada)"
    url = f"{SUPABASE_URL}/auth/v1/user"
    headers = {
        'apikey': SUPABASE_ANON_KEY,
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    payload = {"password": new_password}
    try:
        r = requests.put(url, json=payload, headers=headers, timeout=10)
        if r.ok:
            return r.json(), None
        
        error_data = {}
        try:
            error_data = r.json()
        except:
            pass
        
        error_msg = error_data.get('msg') or error_data.get('message') or r.text
        print('supabase_update_user_password error:', r.status_code, error_msg)
        return None, error_msg
    except Exception as e:
        print('supabase_update_user_password exception:', str(e))
        return None, str(e)


def supabase_get_schedules(access_token, user_id):
    """Get schedules for a given user using user's access token (so RLS applies)."""
    if not SUPABASE_URL:
        return []
    url = f"{SUPABASE_URL}/rest/v1/schedules?select=*&user_id=eq.{user_id}"
    headers = {
        'apikey': SUPABASE_ANON_KEY,
        'Authorization': f'Bearer {access_token}'
    }
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.ok:
            return r.json()
        print('supabase_get_schedules error:', r.status_code, r.text)
        return []
    except Exception as e:
        print('supabase_get_schedules exception:', str(e))
        return []


def supabase_create_schedule(access_token, user_id, name='Mi horario', data=None):
    """Create a schedule for the user with optional materials data."""
    if not SUPABASE_URL:
        print('supabase_create_schedule: missing SUPABASE_URL')
        return None
    url = f"{SUPABASE_URL}/rest/v1/schedules"
    headers = {
        'apikey': SUPABASE_ANON_KEY,
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'Prefer': 'return=representation'
    }
    body = {
        "user_id": user_id,
        "name": name,
        "metadata": data or {}
    }
    print(f'Creating schedule with body: {body}')
    try:
        r = requests.post(url, json=body, headers=headers, timeout=10)
        print(f'supabase_create_schedule response: {r.status_code} {r.text}')
        if r.ok:
            result = r.json()
            print(f'Schedule created successfully: {result}')
            
            # Create schedule items if data contains materias
            if data and 'materias' in data:
                schedule_id = None
                if isinstance(result, list):
                    if len(result) > 0:
                        schedule_id = result[0].get('id')
                elif isinstance(result, dict):
                    schedule_id = result.get('id')
                
                if schedule_id:
                    supabase_create_schedule_items(access_token, schedule_id, data['materias'])
                else:
                    print(f"Error: Could not extract schedule_id from result: {result}")
            
            return result
        print('supabase_create_schedule error:', r.status_code, r.text)
        return None
    except Exception as e:
        print('supabase_create_schedule exception:', str(e))
        return None


def _format_time(t):
    """Helper to format time from HHMM to HH:MM"""
    if not t:
        return None
    t = t.strip()
    if len(t) == 4 and t.isdigit():
        return f"{t[:2]}:{t[2:]}"
    return t


def _get_days_from_string(day_str):
    """Convert day string (e.g. 'L . I . .') to list of integers (1-6)."""
    days = []
    if not day_str:
        return days
    s = day_str.upper()
    if 'L' in s: days.append(1) # Lunes
    if 'M' in s: days.append(2) # Martes
    if 'I' in s: days.append(3) # Miercoles
    if 'J' in s: days.append(4) # Jueves
    if 'V' in s: days.append(5) # Viernes
    if 'S' in s: days.append(6) # Sabado
    return days


def supabase_create_schedule_items(access_token, schedule_id, materias):
    """Create individual schedule items (courses) for a schedule."""
    if not SUPABASE_URL or not materias:
        print(f'supabase_create_schedule_items: missing URL or materias')
        return 0, ["Missing URL or materias"]
    
    print(f'\n========== CREATING SCHEDULE ITEMS ==========')
    print(f'Schedule ID: {schedule_id}')
    print(f'Total materias: {len(materias)}')
    
    url = f"{SUPABASE_URL}/rest/v1/schedule_items"
    headers = {
        'apikey': SUPABASE_ANON_KEY,
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'Prefer': 'return=representation'
    }
    
    errors = []
    item_count = 0
    
    try:
        for materia in materias:
            # Get horarios if available, otherwise create empty
            horarios = materia.get('horarios', [])
            
            print(f'\nProcessing materia: {materia.get("Materia", "N/A")} - {len(horarios)} horarios')
            
            for horario in horarios:
                raw_horas = horario.get('horas', '')
                start_time = None
                end_time = None
                
                if raw_horas and '-' in raw_horas:
                    parts = raw_horas.split('-')
                    start_time = _format_time(parts[0])
                    end_time = _format_time(parts[1])
                
                # Parse days string to list of integers
                day_str = horario.get('dias', '')
                days_indices = _get_days_from_string(day_str)
                
                if not days_indices:
                    print(f'  ⚠️ No valid days found for {day_str}, skipping...')
                    continue

                for day_idx in days_indices:
                    body = {
                        "schedule_id": schedule_id,
                        # "course_code": materia.get('Clave', ''),
                        "title": materia.get('Materia', ''),
                        # "instructor": materia.get('Profesor', ''), # Column missing in DB schema
                        "day": day_idx,
                        "start_time": start_time,
                        "end_time": end_time,
                        # "room": horario.get('aula', ''), # Column missing in DB schema
                        # "nrc": materia.get('NRC', '') # Column missing in DB schema
                    }
                    
                    print(f'  Inserting item: {body["title"]} - Day {day_idx} - {body["start_time"]}-{body["end_time"]}')
                    
                    r = requests.post(url, json=body, headers=headers, timeout=10)
                    
                    if not r.ok:
                        msg = f"Failed to insert {body['title']}: {r.status_code} {r.text}"
                        print(f'  ❌ {msg}')
                        errors.append(msg)
                    else:
                        item_count += 1
                        print(f'  ✓ SUCCESS')
        
        print(f'\n✓ Created {item_count} schedule items total')
        print(f'========== END CREATE SCHEDULE ITEMS ==========\n')
        return item_count, errors
        
    except Exception as e:
        msg = f"Exception creating schedule items: {str(e)}"
        print(f'❌ {msg}')
        import traceback
        traceback.print_exc()
        errors.append(msg)
        return item_count, errors



def supabase_get_user(access_token):
    """Get user info from access token."""
    if not SUPABASE_URL:
        return None
    url = f"{SUPABASE_URL}/auth/v1/user"
    headers = {
        'apikey': SUPABASE_ANON_KEY,
        'Authorization': f'Bearer {access_token}'
    }
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.ok:
            return r.json()
        print('supabase_get_user error:', r.status_code, r.text)
        return None
    except Exception as e:
        print('supabase_get_user exception:', str(e))
        return None


def supabase_create_profile_service(user_id, email, full_name=None):
    """Create a profile row using the Service Role key (server-side only)."""
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print('supabase_create_profile_service: missing SUPABASE_URL or SUPABASE_SERVICE_KEY')
        return None
    url = f"{SUPABASE_URL}/rest/v1/profiles"
    headers = {
        'apikey': SUPABASE_SERVICE_KEY,
        'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'return=representation'
    }
    # Usamos upsert para evitar errores si el perfil ya existe (por un trigger)
    headers['Prefer'] = 'return=representation,resolution=merge-duplicates'
    
    body = {
        'id': user_id,
        'email': email,
        'full_name': full_name or '',
        'is_pro': False
    }
    print(f'Creating profile with body: {body}')
    try:
        r = requests.post(url, json=body, headers=headers, timeout=10)
        print(f'supabase_create_profile_service response: {r.status_code} {r.text}')
        if r.ok:
            result = r.json()
            print(f'Profile created successfully: {result}')
            if isinstance(result, list) and len(result) > 0:
                return result[0]
            return result
        
        print('supabase_create_profile_service error:', r.status_code, r.text)
        return None
    except Exception as e:
        print('supabase_create_profile_service exception:', str(e))
        import traceback
        traceback.print_exc()
        return None


def supabase_get_profile(access_token, user_id):
    """Get user profile including is_pro status."""
    if not SUPABASE_URL:
        return None
    url = f"{SUPABASE_URL}/rest/v1/profiles?id=eq.{user_id}"
    headers = {
        'apikey': SUPABASE_ANON_KEY,
        'Authorization': f'Bearer {access_token}'
    }
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.ok:
            data = r.json()
            return data[0] if data else None
        print('supabase_get_profile error:', r.status_code, r.text)
        return None
    except Exception as e:
        print('supabase_get_profile exception:', str(e))
        return None


def supabase_delete_schedule(access_token, schedule_id):
    """Delete a schedule by ID."""
    if not SUPABASE_URL:
        return False
    url = f"{SUPABASE_URL}/rest/v1/schedules?id=eq.{schedule_id}"
    headers = {
        'apikey': SUPABASE_ANON_KEY,
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    try:
        r = requests.delete(url, headers=headers, timeout=10)
        if r.ok:
            print(f'Schedule {schedule_id} deleted successfully')
            return True
        print('supabase_delete_schedule error:', r.status_code, r.text)
        return False
    except Exception as e:
        print('supabase_delete_schedule exception:', str(e))
        return False

def supabase_get_professor_ratings(professor_name):
    """Get all ratings for a specific professor."""
    if not SUPABASE_URL:
        return [], "Falta SUPABASE_URL"
    # Use RPC or direct query. Direct query is easier if table exists.
    url = f"{SUPABASE_URL}/rest/v1/professor_ratings?professor_name=eq.{professor_name}&select=*"
    headers = {
        'apikey': SUPABASE_ANON_KEY,
        'Content-Type': 'application/json'
    }
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.ok:
            return r.json(), None
        
        error_detail = r.text
        try:
            error_json = r.json()
            error_detail = error_json.get('message', r.text)
        except:
            pass
            
        print('supabase_get_professor_ratings error:', r.status_code, error_detail)
        return [], error_detail
    except Exception as e:
        print('supabase_get_professor_ratings exception:', str(e))
        return [], str(e)


def supabase_add_professor_rating(access_token, user_id, professor_name, rating, comment):
    """Add a rating for a professor. Allows anonymous ratings if access_token/user_id are None."""
    if not SUPABASE_URL:
        return None, "Falta SUPABASE_URL"
    
    url = f"{SUPABASE_URL}/rest/v1/professor_ratings"
    
    # Si hay token usamos el token del usuario (RLS)
    # Si no hay, usamos el service key si está disponible (bypassa RLS) o la anon key
    auth_header = f'Bearer {access_token}' if access_token else f'Bearer {SUPABASE_SERVICE_KEY}' if SUPABASE_SERVICE_KEY else f'Bearer {SUPABASE_ANON_KEY}'
    
    headers = {
        'apikey': SUPABASE_SERVICE_KEY if (not access_token and SUPABASE_SERVICE_KEY) else SUPABASE_ANON_KEY,
        'Authorization': auth_header,
        'Content-Type': 'application/json',
        'Prefer': 'return=representation'
    }
    
    body = {
        "user_id": user_id,
        "professor_name": professor_name,
        "rating": rating,
        "comment": comment
    }
    
    try:
        r = requests.post(url, json=body, headers=headers, timeout=10)
        if r.ok:
            return r.json(), None
        
        error_detail = r.text
        try:
            error_json = r.json()
            error_detail = error_json.get('message', r.text)
        except:
            pass
            
        print('supabase_add_professor_rating error:', r.status_code, error_detail)
        return None, error_detail
    except Exception as e:
        print('supabase_add_professor_rating exception:', str(e))
        return None, str(e)

def supabase_get_all_professor_averages():
    """Get all ratings and calculate average and count per professor."""
    if not SUPABASE_URL:
        return {}, "Falta SUPABASE_URL"
    
    url = f"{SUPABASE_URL}/rest/v1/professor_ratings?select=professor_name,rating"
    headers = {
        'apikey': SUPABASE_ANON_KEY,
        'Content-Type': 'application/json'
    }
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.ok:
            ratings = r.json()
            averages = {}
            for r_entry in ratings:
                name = r_entry['professor_name']
                rating = r_entry['rating']
                if name not in averages:
                    averages[name] = {'total_rating': 0, 'count': 0}
                averages[name]['total_rating'] += rating
                averages[name]['count'] += 1
            
            # Formatear para facilitar uso
            result = {}
            for name, stats in averages.items():
                result[name] = {
                    'average': round(stats['total_rating'] / stats['count'], 1),
                    'count': stats['count']
                }
            return result, None
        
        return {}, r.text
    except Exception as e:
        return {}, str(e)

def supabase_update_schedule(access_token, schedule_id, name=None, color=None, notes=None, metadata=None):
    """Update schedule properties (name, color, notes, metadata)."""
    if not SUPABASE_URL:
        return None
    url = f"{SUPABASE_URL}/rest/v1/schedules?id=eq.{schedule_id}"
    headers = {
        'apikey': SUPABASE_ANON_KEY,
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'Prefer': 'return=representation'
    }
    body = {}
    if name:
        body['name'] = name
    # if color:
    #     body['color'] = color # Column missing in DB schema
    # if notes:
    #     body['notes'] = notes # Column likely missing in DB schema
    if metadata is not None:
        body['metadata'] = metadata
    
    print(f'Updating schedule {schedule_id} with: {body.keys()}')
    try:
        r = requests.patch(url, json=body, headers=headers, timeout=10)
        if r.ok:
            result = r.json()
            print(f'Schedule updated: {result}')
            return result
        print('supabase_update_schedule error:', r.status_code, r.text)
        return None
    except Exception as e:
        print('supabase_update_schedule exception:', str(e))
        return None

def supabase_get_schedule_items(access_token, schedule_id):
    """Get all schedule items (courses) for a schedule."""
    if not SUPABASE_URL:
        return []
    url = f"{SUPABASE_URL}/rest/v1/schedule_items?schedule_id=eq.{schedule_id}"
    headers = {
        'apikey': SUPABASE_ANON_KEY,
        'Authorization': f'Bearer {access_token}'
    }
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.ok:
            return r.json()
        print('supabase_get_schedule_items error:', r.status_code, r.text)
        return []
    except Exception as e:
        print('supabase_get_schedule_items exception:', str(e))
        return []


def supabase_delete_schedule_items(access_token, item_ids):
    """Delete specific schedule items by their IDs."""
    if not SUPABASE_URL or not item_ids:
        return True
    
    # Convert list to comma-separated string for 'in' filter
    ids_str = ','.join(str(id) for id in item_ids)
    url = f"{SUPABASE_URL}/rest/v1/schedule_items?id=in.({ids_str})"
    
    headers = {
        'apikey': SUPABASE_ANON_KEY,
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    try:
        r = requests.delete(url, headers=headers, timeout=10)
        if r.ok:
            print(f'Deleted schedule items: {item_ids}')
            return True
        print('supabase_delete_schedule_items error:', r.status_code, r.text)
        return False
    except Exception as e:
        print('supabase_delete_schedule_items exception:', str(e))
        return False