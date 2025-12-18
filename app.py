from flask import Flask, render_template, request, jsonify
import requests
from bs4 import BeautifulSoup
import re
import time

app = Flask(__name__)

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
    return render_template('index.html', centros=CENTROS)

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
        ciclo = data.get('ciclo', '202520')

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
    app.run(debug=True, host='0.0.0.0', port=5000)
