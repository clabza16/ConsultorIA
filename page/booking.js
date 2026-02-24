// URL de tu aplicación de Google Apps Script (PEGAR AQUÍ DESPUÉS DE IMPLEMENTAR)
const GOOGLE_SCRIPT_URL = 'https://script.google.com/macros/s/AKfycbxLFSV72yDd1PIGgL7wCpAMxmuAKIKYP2HO8k2MqtoGTc7Vu0VyLKvLflI5TvwFFcyz/exec';

document.addEventListener('DOMContentLoaded', () => {
    const bookingModal = document.getElementById('booking-modal');
    const closeBtn = document.querySelector('.close-modal');
    const scheduleBtns = document.querySelectorAll('a[href="#agendar"], .btn-booking');
    const calendarDays = document.getElementById('calendar-days');
    const currentMonthText = document.getElementById('current-month');
    const prevMonthBtn = document.getElementById('prev-month');
    const nextMonthBtn = document.getElementById('next-month');
    const bookingStatus = document.getElementById('booking-status');

    // Elementos del nuevo formulario
    const step1 = document.getElementById('booking-form-step-1');
    const stepHours = document.getElementById('hour-selection-step');
    const hourSlots = document.getElementById('hour-slots');
    const step2 = document.getElementById('booking-details-form');
    const selectedDateDisplay = document.getElementById('selected-date-display');
    const finalConfirmBtn = document.getElementById('final-confirm-btn');
    const backToCalendar = document.getElementById('back-to-calendar');
    const backToCalendarFromHours = document.getElementById('back-to-calendar-from-hours');

    let date = new Date();
    let currYear = date.getFullYear();
    let currMonth = date.getMonth();
    let selectedDateString = "";
    let selectedHour = "";
    let availableDates = [];

    const months = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio",
        "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"];

    // Función para obtener fechas desde el backend
    const fetchAvailableDates = async () => {
        try {
            const response = await fetch(GOOGLE_SCRIPT_URL);
            const result = await response.json();
            if (result.status === "success") {
                availableDates = result.dates;
                renderCalendar();
            }
        } catch (e) {
            console.error("Error al obtener fechas:", e);
        }
    }

    fetchAvailableDates();

    // Open Modal
    scheduleBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            resetModal();
            bookingModal.style.display = 'flex';
            document.body.style.overflow = 'hidden';
            renderCalendar();
        });
    });

    const resetModal = () => {
        step1.style.display = 'block';
        stepHours.style.display = 'none';
        step2.style.display = 'none';
        bookingStatus.innerHTML = '';
        document.getElementById('user-name').value = '';
        document.getElementById('user-email').value = '';
    }

    // Close Modal
    closeBtn.addEventListener('click', () => {
        bookingModal.style.display = 'none';
        document.body.style.overflow = 'auto';
    });

    window.onclick = (event) => {
        if (event.target == bookingModal) {
            bookingModal.style.display = 'none';
            document.body.style.overflow = 'auto';
        }
    }

    const renderCalendar = () => {
        let firstDayofMonth = new Date(currYear, currMonth, 1).getDay();
        let lastDateofMonth = new Date(currYear, currMonth + 1, 0).getDate();
        let lastDayofMonth = new Date(currYear, currMonth, lastDateofMonth).getDay();
        let lastDateofLastMonth = new Date(currYear, currMonth, 0).getDate();
        let liTag = "";

        let firstDayCorrected = firstDayofMonth === 0 ? 6 : firstDayofMonth - 1;

        for (let i = firstDayCorrected; i > 0; i--) {
            liTag += `<li class="inactive">${lastDateofLastMonth - i + 1}</li>`;
        }

        for (let i = 1; i <= lastDateofMonth; i++) {
            let currentDate = new Date(currYear, currMonth, i);
            let dateStr = `${currYear}-${String(currMonth + 1).padStart(2, '0')}-${String(i).padStart(2, '0')}`;

            let isToday = i === date.getDate() && currMonth === new Date().getMonth()
                && currYear === new Date().getFullYear();

            let isAvailable = availableDates.includes(dateStr);
            let className = isToday ? "active" : "";
            if (isAvailable) className += " available";

            liTag += `<li class="${className}" data-date="${dateStr}" onclick="${isAvailable ? 'goToHours(this)' : ''}">${i}</li>`;
        }

        for (let i = lastDayofMonth; i < 7; i++) {
            if (i === 0) break;
            liTag += `<li class="inactive">${i - lastDayofMonth + 1}</li>`;
        }

        currentMonthText.innerText = `${months[currMonth]} ${currYear}`;
        calendarDays.innerHTML = liTag;
    }

    prevMonthBtn.addEventListener("click", () => {
        currMonth = currMonth - 1;
        if (currMonth < 0) {
            currMonth = 11;
            currYear--;
        }
        renderCalendar();
    });

    nextMonthBtn.addEventListener("click", () => {
        currMonth = currMonth + 1;
        if (currMonth > 11) {
            currMonth = 0;
            currYear++;
        }
        renderCalendar();
    });

    // Step navigation: Day -> Hours
    window.goToHours = async (element) => {
        selectedDateString = element.getAttribute('data-date');
        step1.style.display = 'none';
        bookingStatus.innerHTML = '<p style="text-align: center; color: var(--accent);">Cargando horarios...</p>';

        try {
            const response = await fetch(`${GOOGLE_SCRIPT_URL}?date=${selectedDateString}`);
            const result = await response.json();
            bookingStatus.innerHTML = '';

            if (result.status === "success" && result.hours.length > 0) {
                stepHours.style.display = 'block';
                hourSlots.innerHTML = result.hours.map(h => `
                    <button class="hour-btn" style="padding: 0.5rem; border: 1px solid var(--accent); border-radius: 8px; background: white; color: var(--accent); cursor: pointer;" onclick="goToDetails(${h})">${h}:00</button>
                `).join('');
            } else {
                bookingStatus.innerHTML = '<p style="text-align: center; color: #ef4444;">No hay horarios disponibles para este día.</p>';
                step1.style.display = 'block';
            }
        } catch (e) {
            console.error(e);
            bookingStatus.innerHTML = '<p style="text-align: center; color: #ef4444;">Error al cargar horarios.</p>';
            step1.style.display = 'block';
        }
    }

    // Step navigation: Hours -> Details
    window.goToDetails = (hour) => {
        selectedHour = hour;
        const parts = selectedDateString.split('-');
        const displayDate = `${parts[2]}/${parts[1]}/${parts[0]}`;

        selectedDateDisplay.innerHTML = `
            <p style="font-weight: 600; color: #0369a1; font-size: 0.9rem;">Fecha: ${displayDate}</p>
            <p style="font-weight: 600; color: #0369a1; font-size: 0.9rem;">Hora: ${selectedHour}:00</p>
        `;

        stepHours.style.display = 'none';
        step2.style.display = 'block';
    }

    backToCalendarFromHours.addEventListener('click', () => {
        stepHours.style.display = 'none';
        step1.style.display = 'block';
    });

    backToCalendar.addEventListener('click', () => {
        step2.style.display = 'none';
        stepHours.style.display = 'block';
    });

    finalConfirmBtn.addEventListener('click', async () => {
        const name = document.getElementById('user-name').value;
        const email = document.getElementById('user-email').value;

        if (!name || !email) {
            alert('Por favor, ingresa tu nombre y correo electrónico.');
            return;
        }

        bookingStatus.innerHTML = '<p style="text-align: center; margin-top: 1rem; color: var(--accent);">Confirmando reserva...</p>';
        finalConfirmBtn.disabled = true;

        try {
            const response = await fetch(GOOGLE_SCRIPT_URL, {
                method: 'POST',
                body: JSON.stringify({
                    date: selectedDateString,
                    hour: selectedHour,
                    name: name,
                    email: email
                })
            });

            const result = await response.json();

            if (result.status === "success") {
                showSuccess("¡Tu cupo ha sido reservado! Revisa tu email para la invitación del calendario.");
            } else {
                throw new Error(result.message);
            }

        } catch (error) {
            console.error('Error:', error);
            bookingStatus.innerHTML = `<p style="text-align: center; margin-top: 1rem; color: #ef4444;">Error: ${error.message}</p>`;
            finalConfirmBtn.disabled = false;
        }
    });

    const showSuccess = (msg) => {
        step2.style.display = 'none';
        bookingStatus.innerHTML = `
            <div style="margin-top: 1.5rem; padding: 2rem; background: #f0fdf4; border-radius: 12px; border: 1px solid #bbf7d0; text-align: center;">
                <p style="font-size: 2rem; margin-bottom: 1rem;">✅</p>
                <p style="font-weight: 600; color: #15803d; font-size: 1.25rem;">¡Reserva Exitosa!</p>
                <p style="margin-top: 0.5rem; color: #166534;">${msg}</p>
            </div>
        `;
    }
});
