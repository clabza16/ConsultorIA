/**
 * BACKEND DINÁMICO PARA CONSULTORIA - GOOGLE APPS SCRIPT
 */

// Helper para crear fecha universal usando el offset del calendario
function getUniversalDate(dateStr, hour, timezone) {
  // dateStr: yyyy-mm-dd
  var offset = Utilities.formatDate(new Date(), timezone, "Z"); // ej: -0300
  // Construir ISO: 2026-02-26T21:00:00-0300
  var iso = dateStr + "T" + (hour < 10 ? "0" + hour : hour) + ":00:00" + offset;
  return new Date(iso);
}

// Token de seguridad compartido
const SHARED_SECRET_TOKEN = "ConsultorIA_v1_Secret_2026";

// 1. OBTENER FECHAS O HORAS DISPONIBLES
function doGet(e) {
  // Verificación de seguridad
  if (e.parameter.secret_token !== SHARED_SECRET_TOKEN) {
    return ContentService.createTextOutput(JSON.stringify({
      "status": "error", "message": "No autorizado"
    })).setMimeType(ContentService.MimeType.JSON);
  }

  try {
    var calendar = CalendarApp.getDefaultCalendar();
    var timezone = calendar.getTimeZone();
    var now = new Date();
    
    // CASO A: Pedir horas de un día específico
    if (e.parameter.date) {
      var dStr = e.parameter.date;
      var dCheck = getUniversalDate(dStr, 12, timezone); // Usamos mediodía para chequear el día de semana
      var dayOfWeek = dCheck.getDay();
      var slots = [];
      
      if (dayOfWeek >= 1 && dayOfWeek <= 5) slots = [19, 20, 21];
      else if (dayOfWeek === 6) slots = [10, 11, 12];
      
      var freeSlots = [];
      slots.forEach(function(h) {
        var sStart = getUniversalDate(dStr, h, timezone);
        var sEnd = getUniversalDate(dStr, h + 1, timezone);
        
        if (sStart > now) {
          var events = calendar.getEvents(sStart, sEnd);
          var conflicts = events.filter(function(ev) {
            return !ev.isAllDayEvent() && ev.getStartTime() < sEnd && ev.getEndTime() > sStart;
          });
          if (conflicts.length === 0) freeSlots.push(h);
        }
      });
      
      return ContentService.createTextOutput(JSON.stringify({
        "status": "success", "hours": freeSlots
      })).setMimeType(ContentService.MimeType.JSON);
    }
    
    // CASO B: Pedir días disponibles
    var future = new Date();
    future.setDate(now.getDate() + 30);
    var availableDates = [];
    
    // Empezar desde hoy
    var tempDate = new Date();
    tempDate.setHours(0,0,0,0);
    
    for (var i = 0; i < 31; i++) {
      var loopDay = new Date(tempDate.getTime() + (i * 24 * 60 * 60 * 1000));
      var dateStr = Utilities.formatDate(loopDay, timezone, "yyyy-MM-dd");
      var dayOfWeek = loopDay.getDay(); // Esto puede fallar si tempDate está en otra TZ
      
      // Mejor chequear el día de la semana usando la TZ del calendario
      var calDayOfWeek = parseInt(Utilities.formatDate(loopDay, timezone, "u")); // 1=Lun, 7=Dom
      
      var hStart = (calDayOfWeek === 6) ? 10 : (calDayOfWeek >= 1 && calDayOfWeek <= 5 ? 19 : -1);
      var hEnd = (calDayOfWeek === 6) ? 13 : (calDayOfWeek >= 1 && calDayOfWeek <= 5 ? 22 : -1);
      
      if (hStart !== -1) {
        var dayAvailable = false;
        for (var h = hStart; h < hEnd; h++) {
          var sStart = getUniversalDate(dateStr, h, timezone);
          var sEnd = getUniversalDate(dateStr, h + 1, timezone);
          
          if (sStart > now) {
            var hasConflict = calendar.getEvents(sStart, sEnd).some(function(ev) {
              return !ev.isAllDayEvent() && ev.getStartTime() < sEnd && ev.getEndTime() > sStart;
            });
            if (!hasConflict) { dayAvailable = true; break; }
          }
        }
        if (dayAvailable) availableDates.push(dateStr);
      }
    }
    
    return ContentService.createTextOutput(JSON.stringify({
      "status": "success", "dates": availableDates
    })).setMimeType(ContentService.MimeType.JSON);
    
  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({
      "status": "error", "message": err.toString()
    })).setMimeType(ContentService.MimeType.JSON);
  }
}

// 2. PROCESAR RESERVA
function doPost(e) {
  var lock = LockService.getScriptLock();
  lock.tryLock(10000);

  try {
    var calendar = CalendarApp.getDefaultCalendar();
    var timezone = calendar.getTimeZone();
    var data = e.postData && e.postData.contents ? JSON.parse(e.postData.contents) : e.parameter;
    
    // Verificación de seguridad
    if (data.secret_token !== SHARED_SECRET_TOKEN) {
      throw new Error("Petición no autorizada");
    }
    
    
    var sStart = getUniversalDate(data.date, parseInt(data.hour), timezone);
    var sEnd = getUniversalDate(data.date, parseInt(data.hour) + 1, timezone);

    if (calendar.getEvents(sStart, sEnd).some(ev => !ev.isAllDayEvent() && ev.getStartTime() < sEnd && ev.getEndTime() > sStart)) {
      throw new Error("Horario ocupado");
    }

    var initials = data.name.split(" ").map(n => n[0]).join("").toUpperCase().substring(0, 3);
    calendar.createEvent("ConsultorIA: Clase 1 - " + initials, sStart, sEnd, {
      description: "Reserva web. Sesión 1+2.",
      guests: data.email,
      sendInvites: true
    });
    
    logToSheet(data.date, data.name, data.email, data.phone, data.hour);
    
    // ENVIAR NOTIFICACIÓN AL ADMINISTRADOR
    try {
      var adminEmail = "clabza16@gmail.com";
      var subject = "NUEVA RESERVA: " + data.name + " (" + data.date + ")";
      var body = "Se ha registrado una nueva reserva en ConsultorIA:\n\n" +
                 "Nombre: " + data.name + "\n" +
                 "Email: " + data.email + "\n" +
                 "Teléfono: " + (data.phone || "No proporcionado") + "\n" +
                 "Fecha: " + data.date + "\n" +
                 "Hora: " + data.hour + ":00\n\n" +
                 "Revisa el Excel de Reservas para más detalles.";
      MailApp.sendEmail(adminEmail, subject, body);
    } catch (e) {
      console.error("Error enviando email: " + e.toString());
    }
    
    return ContentService.createTextOutput(JSON.stringify({
      "status": "success", "message": "Confirmado"
    })).setMimeType(ContentService.MimeType.JSON);

  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({
      "status": "error", "message": err.toString()
    })).setMimeType(ContentService.MimeType.JSON);
  } finally {
    lock.releaseLock();
  }
}

function logToSheet(date, name, email, phone, hour) {
  var ss;
  var files = DriveApp.getFilesByName("ConsultorIA_Reservas");
  if (files.hasNext()) ss = SpreadsheetApp.open(files.next());
  else ss = SpreadsheetApp.create("ConsultorIA_Reservas");
  
  var sheet = ss.getSheetByName("Reservas") || ss.insertSheet("Reservas");
  if (sheet.getLastRow() == 0) sheet.appendRow(["Fecha", "Nombre", "Email", "Telefono", "Horario", "Timestamp"]);
  sheet.appendRow([date, name, email, phone, hour + ":00", new Date()]);
}

// FUNCIÓN DE CONFIGURACIÓN INICIAL (Ejecuta esto para dar permisos)
function setup() {
  console.log("Activando permisos...");
  DriveApp.getRootFolder();
  CalendarApp.getDefaultCalendar().getName();
  console.log("¡Permisos listos!");
}
