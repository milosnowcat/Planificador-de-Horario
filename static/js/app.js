// Estado de la aplicación
let materiasCargadas = [];
let materiasAgregadas = [];
const colores = [
    '#667eea', '#764ba2', '#f093fb', '#4facfe',
    '#43e97b', '#fa709a', '#fee140', '#30cfd0',
    '#a8edea', '#fed6e3', '#c471f5', '#12c2e9'
];
let colorIndex = 0;

// Horarios disponibles
let horas = [
    '07:00', '08:00', '09:00', '10:00', '11:00', '12:00',
    '13:00', '14:00', '15:00', '16:00', '17:00', '18:00',
    '19:00', '20:00', '21:00'
];

let diasMap = {
    'L': 1, 'M': 2, 'I': 3, 'J': 4, 'V': 5, 'S': 6
};

// Inicializar el calendario
function inicializarCalendario() {
    const calendario = document.getElementById('calendario');
    
    horas.forEach((hora, index) => {
        // Celda de hora
        const celdaHora = document.createElement('div');
        celdaHora.className = 'calendar-cell time';
        celdaHora.textContent = hora;
        calendario.appendChild(celdaHora);
        
        // Celdas para cada día
        for (let dia = 0; dia < 6; dia++) {
            const celda = document.createElement('div');
            celda.className = 'calendar-cell';
            celda.dataset.hora = index + 7; // 7 = 07:00
            celda.dataset.dia = dia + 1;
            calendario.appendChild(celda);
        }
    });
}

// Buscar materias
document.getElementById('btnBuscar').addEventListener('click', async () => {
    const ciclo = document.getElementById('ciclo').value;
    const centro = document.getElementById('centro').value;
    const carrera = document.getElementById('carrera').value;
    
    if (!centro) {
        alert('Por favor selecciona un centro universitario');
        return;
    }
    
    const loading = document.getElementById('loading');
    const btnBuscar = document.getElementById('btnBuscar');
    
    loading.style.display = 'block';
    btnBuscar.disabled = true;
    
    try {
        const response = await fetch('/api/buscar_materias', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ ciclo, centro, carrera })
        });
        
        const data = await response.json();
        
        if (data.success) {
            materiasCargadas = data.materias;
            mostrarMaterias(materiasCargadas);
            document.getElementById('materiasContainer').style.display = 'block';
        } else {
            alert('Error al buscar materias: ' + data.error);
        }
    } catch (error) {
        alert('Error al conectar con el servidor: ' + error.message);
    } finally {
        loading.style.display = 'none';
        btnBuscar.disabled = false;
    }
});

// Mostrar materias en la lista
function mostrarMaterias(materias) {
    const lista = document.getElementById('listaMaterias');
    lista.innerHTML = '';
    
    // Agrupar por materia
    const materiasAgrupadas = {};
    materias.forEach(materia => {
        const key = `${materia.NRC}_${materia.Materia}`;
        if (!materiasAgrupadas[key]) {
            materiasAgrupadas[key] = {
                ...materia,
                horarios: []
            };
        }
        if (materia.Horas && materia.Dias) {
            materiasAgrupadas[key].horarios.push({
                horas: materia.Horas,
                dias: materia.Dias,
                edificio: materia.Edificio,
                aula: materia.Aula
            });
        }
    });
    
    // Actualizar el total con las materias agrupadas
    document.getElementById('totalMaterias').textContent = Object.keys(materiasAgrupadas).length;
    
    Object.values(materiasAgrupadas).forEach(materia => {
        const item = document.createElement('div');
        item.className = 'materia-item';
        item.dataset.nrc = materia.NRC;
        
        // Verificar si ya está agregada
        const yaAgregada = materiasAgregadas.some(m => m.NRC === materia.NRC);
        if (yaAgregada) {
            item.classList.add('agregada');
        }
        
        let horariosHtml = '';
        materia.horarios.forEach((h, idx) => {
            horariosHtml += `<div class="materia-horario">📅 ${h.dias} ${h.horas} - ${h.edificio} ${h.aula}</div>`;
        });
        
        item.innerHTML = `
            <div class="materia-nombre">${materia.Materia}</div>
            <div class="materia-info">Clave: ${materia.Clave} | NRC: ${materia.NRC} | Sección: ${materia.Sec}</div>
            <div class="materia-info">Profesor: ${materia.Profesor}</div>
            <div class="materia-info">Créditos: ${materia.CR} | Disponibles: ${materia.DIS}</div>
            ${horariosHtml}
        `;
        
        if (!yaAgregada) {
            item.addEventListener('click', () => agregarMateriaAlHorario(materia));
        }
        
        lista.appendChild(item);
    });
}

// Filtrar materias
document.getElementById('filtroMaterias').addEventListener('input', (e) => {
    const filtro = e.target.value.toLowerCase();
    const materiasFiltradas = materiasCargadas.filter(m => 
        m.Materia.toLowerCase().includes(filtro) ||
        m.Profesor.toLowerCase().includes(filtro) ||
        m.NRC.includes(filtro) ||
        m.Clave.toLowerCase().includes(filtro)
    );
    mostrarMaterias(materiasFiltradas);
});

// Agregar materia al horario
function agregarMateriaAlHorario(materia) {
    // Verificar conflictos
    const conflicto = obtenerConflicto(materia);
    if (conflicto) {
        mostrarErrorConflicto(materia, conflicto);
        return;
    }
    
    // Asignar color
    const color = colores[colorIndex % colores.length];
    colorIndex++;
    
    materia.color = color;
    materiasAgregadas.push(materia);
    
    // Actualizar vista
    renderizarHorario();
    actualizarLeyenda();
    mostrarMaterias(materiasCargadas);
}

// Obtener información del conflicto
function obtenerConflicto(nuevaMateria) {
    for (const materiaExistente of materiasAgregadas) {
        for (const horarioNuevo of nuevaMateria.horarios) {
            for (const horarioExistente of materiaExistente.horarios) {
                if (hayTraslape(horarioNuevo, horarioExistente)) {
                    return {
                        materiaExistente: materiaExistente,
                        horarioConflicto: horarioExistente
                    };
                }
            }
        }
    }
    return null;
}

// Mostrar error visual de conflicto
function mostrarErrorConflicto(nuevaMateria, conflicto) {
    // Remover modal anterior si existe
    const modalAnterior = document.getElementById('conflictoModal');
    if (modalAnterior) modalAnterior.remove();
    
    const modal = document.createElement('div');
    modal.id = 'conflictoModal';
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal-content modal-error">
            <div class="modal-header">
                <span class="modal-icon">⚠️</span>
                <h3>Conflicto de Horario</h3>
            </div>
            <div class="modal-body">
                <p>La materia <strong>${nuevaMateria.Materia}</strong> tiene conflicto con:</p>
                <div class="conflicto-info">
                    <div class="conflicto-materia" style="border-left-color: ${conflicto.materiaExistente.color}">
                        <strong>${conflicto.materiaExistente.Materia}</strong>
                        <span>${conflicto.horarioConflicto.dias} ${conflicto.horarioConflicto.horas}</span>
                    </div>
                </div>
                <p class="modal-hint">No es posible agregar materias con horarios que se traslapen.</p>
            </div>
            <div class="modal-actions">
                <button class="btn btn-modal-close" onclick="cerrarModal()">Entendido</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Cerrar al hacer clic fuera
    modal.addEventListener('click', (e) => {
        if (e.target === modal) cerrarModal();
    });
}

// Cerrar modal
function cerrarModal() {
    const modal = document.getElementById('conflictoModal');
    if (modal) {
        modal.classList.add('modal-closing');
        setTimeout(() => modal.remove(), 200);
    }
}

// Verificar traslape de horarios
function hayTraslape(h1, h2) {
    // Verificar si comparten días
    const dias1 = parseDias(h1.dias);
    const dias2 = parseDias(h2.dias);
    
    const diasComunes = dias1.filter(d => dias2.includes(d));
    if (diasComunes.length === 0) return false;
    
    // Verificar si las horas se traslapan
    const [inicio1, fin1] = parseHoras(h1.horas);
    const [inicio2, fin2] = parseHoras(h2.horas);
    
    if (!inicio1 || !inicio2) return false;
    
    return (inicio1 < fin2) && (fin1 > inicio2);
}

// Parsear días (ej: ". M . J . ." -> [2, 4])
function parseDias(diasStr) {
    const dias = [];
    const partes = diasStr.split(' ');
    const letras = ['L', 'M', 'I', 'J', 'V', 'S'];
    
    partes.forEach((parte, idx) => {
        if (parte !== '.' && letras[idx]) {
            dias.push(diasMap[letras[idx]]);
        }
    });
    
    return dias;
}

// Parsear horas (ej: "0700-0800" -> [7, 8])
function parseHoras(horasStr) {
    if (!horasStr) return [null, null];
    
    const partes = horasStr.replace(/\s/g, '').split('-');
    if (partes.length !== 2) return [null, null];
    
    const inicio = parseInt(partes[0]) / 100;
    const fin = parseInt(partes[1]) / 100;
    
    return [inicio, fin];
}

// Renderizar el horario en el calendario
function renderizarHorario() {
    // Limpiar clases existentes
    document.querySelectorAll('.clase-block').forEach(el => el.remove());
    
    // Agregar cada materia
    materiasAgregadas.forEach(materia => {
        materia.horarios.forEach(horario => {
            const dias = parseDias(horario.dias);
            const [horaInicio, horaFin] = parseHoras(horario.horas);
            
            if (!horaInicio || !horaFin) return;
            
            dias.forEach(dia => {
                // Calcular posición
                const duracion = horaFin - horaInicio;
                const inicioIndex = horaInicio - 7; // 7 es la primera hora (07:00)
                
                // Encontrar la celda correspondiente
                const celda = document.querySelector(
                    `.calendar-cell[data-hora="${Math.floor(horaInicio)}"][data-dia="${dia}"]`
                );
                
                if (celda) {
                    const bloque = document.createElement('div');
                    bloque.className = 'clase-block';
                    bloque.style.backgroundColor = materia.color;
                    bloque.style.height = `${duracion * 60}px`;
                    
                    bloque.innerHTML = `
                        <div class="clase-nombre">${materia.Materia.substring(0, 25)}</div>
                        <div class="clase-info">${horario.horas}</div>
                        <div class="clase-info">${horario.edificio} ${horario.aula}</div>
                        <button class="clase-remove" onclick="removerMateria('${materia.NRC}')">×</button>
                    `;
                    
                    celda.appendChild(bloque);
                }
            });
        });
    });
}

// Remover materia del horario
function removerMateria(nrc) {
    materiasAgregadas = materiasAgregadas.filter(m => m.NRC !== nrc);
    renderizarHorario();
    actualizarLeyenda();
    mostrarMaterias(materiasCargadas);
}

// Actualizar leyenda
function actualizarLeyenda() {
    const legendItems = document.getElementById('legendItems');
    
    if (materiasAgregadas.length === 0) {
        legendItems.innerHTML = '<p class="empty-message">No hay materias agregadas aún</p>';
        return;
    }
    
    legendItems.innerHTML = '';
    materiasAgregadas.forEach(materia => {
        const item = document.createElement('div');
        item.className = 'legend-item';
        item.innerHTML = `
            <div class="legend-color" style="background-color: ${materia.color}"></div>
            <div class="legend-text">${materia.Materia} (${materia.NRC})</div>
            <button class="legend-remove" onclick="removerMateria('${materia.NRC}')" title="Eliminar materia">×</button>
        `;
        legendItems.appendChild(item);
    });
}

// Limpiar horario
document.getElementById('btnLimpiarHorario').addEventListener('click', () => {
    if (confirm('¿Estás seguro de que deseas limpiar todo el horario?')) {
        materiasAgregadas = [];
        colorIndex = 0;
        renderizarHorario();
        actualizarLeyenda();
        mostrarMaterias(materiasCargadas);
    }
});

// Guardar horario a la base de datos
document.addEventListener('DOMContentLoaded', () => {
    const btnGuardarHorario = document.getElementById('btnGuardarHorario');
    if (btnGuardarHorario) {
        btnGuardarHorario.addEventListener('click', guardarHorario);
    }
});

function guardarHorario() {
    const nombreInput = document.getElementById('nombreHorario');
    const nombre = nombreInput.value.trim() || 'Mi horario';
    
    if (materiasAgregadas.length === 0) {
        alert('No hay materias en el horario. Agrega materias antes de guardar.');
        return;
    }

    // Serializar el horario
    const horarioData = {
        nombre: nombre,
        materias: materiasAgregadas,
        fecha_creacion: new Date().toISOString()
    };

    // Enviar a la ruta de crear horario
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '/schedules/create';
    
    const nameInput = document.createElement('input');
    nameInput.type = 'hidden';
    nameInput.name = 'name';
    nameInput.value = nombre;
    
    const dataInput = document.createElement('input');
    dataInput.type = 'hidden';
    dataInput.name = 'data';
    dataInput.value = JSON.stringify(horarioData);
    
    form.appendChild(nameInput);
    form.appendChild(dataInput);
    document.body.appendChild(form);
    
    console.log('Guardando horario:', horarioData);
    form.submit();
}

// Inicializar al cargar la página
window.addEventListener('DOMContentLoaded', () => {
    inicializarCalendario();
});
