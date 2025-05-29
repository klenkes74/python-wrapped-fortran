program calculator
    implicit none

    ! Variablen für die Berechnung
    real :: a, b, result
    character(len=10) :: operation

    ! Variablen für Tracing
    character(len=32) :: trace_id
    character(len=16) :: span_id

    ! Variablen für die Kommandozeilenargumente
    character(len=128) :: arg_buffer

    ! Überprüfen Sie, ob genug Argumente vorhanden sind
    if (command_argument_count() < 3) then
        write(0, *) "Fehler: Zu wenige Argumente. Verwendung: calculator <a> <b> <operation> [trace_id] [span_id]"
        stop 1
    end if

    ! Lade Parameter a, b und operation
    call get_command_argument(1, arg_buffer)
    read(arg_buffer, *) a

    call get_command_argument(2, arg_buffer)
    read(arg_buffer, *) b

    call get_command_argument(3, operation)

    ! Lade optionale Tracing-Parameter
    trace_id = "unbekannt"
    span_id = "unbekannt"

    if (command_argument_count() >= 4) then
        call get_command_argument(4, trace_id)
    end if

    if (command_argument_count() >= 5) then
        call get_command_argument(5, span_id)
    end if

    ! Überprüfe auf Nulldivision
    if (operation == "div" .and. abs(b) < 1.0e-10) then
        call log_error("Division durch Null", trace_id, span_id)
        write(0, *) "Fehler: Division durch Null nicht erlaubt"
        stop 1
    end if

    ! Log-Eintrag vor der Berechnung
    call log_info("Starte Berechnung: " // trim(operation) // " mit a=" // trim(arg_buffer), trace_id, span_id)

    ! Führe die entsprechende Operation aus
    select case (operation)
        case ("add")
            result = a + b
            call log_info("Addition ausgeführt", trace_id, span_id)

        case ("sub")
            result = a - b
            call log_info("Subtraktion ausgeführt", trace_id, span_id)

        case ("mul")
            result = a * b
            call log_info("Multiplikation ausgeführt", trace_id, span_id)

        case ("div")
            result = a / b
            call log_info("Division ausgeführt", trace_id, span_id)

        case default
            call log_error("Unbekannte Operation: " // trim(operation), trace_id, span_id)
            write(0, *) "Fehler: Unbekannte Operation. Verwenden Sie add, sub, mul oder div."
            stop 1
    end select

    ! Ergebnis auf die Standardausgabe schreiben
    write(*, '(f0.6)') result

    ! Log-Eintrag nach erfolgreicher Berechnung
    call log_info("Berechnung erfolgreich abgeschlossen. Ergebnis: " // trim(arg_buffer), trace_id, span_id)

contains

    ! Hilfsfunktion für JSON-Logging (INFO Level)
    subroutine log_info(message, trace_id, span_id)
        character(len=*), intent(in) :: message
        character(len=*), intent(in) :: trace_id
        character(len=*), intent(in) :: span_id

        call log_message("INFO", message, trace_id, span_id)
    end subroutine log_info

    ! Hilfsfunktion für JSON-Logging (ERROR Level)
    subroutine log_error(message, trace_id, span_id)
        character(len=*), intent(in) :: message
        character(len=*), intent(in) :: trace_id
        character(len=*), intent(in) :: span_id

        call log_message("ERROR", message, trace_id, span_id)
    end subroutine log_error

    ! Hauptroutine zum Formatieren und Ausgeben von JSON-Logs
    subroutine log_message(level, message, trace_id, span_id)
        character(len=*), intent(in) :: level
        character(len=*), intent(in) :: message
        character(len=*), intent(in) :: trace_id
        character(len=*), intent(in) :: span_id

        character(len=19) :: timestamp
        integer :: values(8)

        ! Aktuelles Datum und Zeit holen
        call date_and_time(VALUES=values)

        ! ISO8601 Format: YYYY-MM-DDThh:mm:ss
        write(timestamp, '(I4,"-",I2.2,"-",I2.2,"T",I2.2,":",I2.2,":",I2.2)') &
            values(1), values(2), values(3), values(5), values(6), values(7)

        ! JSON-Log im Spring Boot Format auf stderr ausgeben
        write(0, '(A)') '{"@timestamp":"' // trim(timestamp) // '",' // &
                        '"level":"' // trim(level) // '",' // &
                        '"thread_name":"fortran-main",' // &
                        '"logger_name":"fortran-calculator",' // &
                        '"message":"' // trim(message) // '",' // &
                        '"traceId":"' // trim(trace_id) // '",' // &
                        '"spanId":"' // trim(span_id) // '",' // &
                        '"service":{"name":"calculator-fortran"}}'
    end subroutine log_message

end program calculator