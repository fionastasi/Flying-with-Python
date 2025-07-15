from djitellopy import Tello
import cv2
import numpy as np
import time
from simple_pid import PID

# Inicialización de parámetros del dron
drone = Tello()
drone.connect()
drone.streamon()
time.sleep(3)
print(f"Nivel de batería: {drone.get_battery()}%")

global flying

# Parámetros para el seguimiento del color (de color_tracking.py)
width = 800
height = 600
x_threshold = int(0.10 * width)
y_threshold = int(0.10 * height)

H_Min_init = 20
H_Max_init = 30
S_Min_init = 120
S_Max_init = 240
V_Min_init = 30
V_Max_init = 255

# Función para el cierre del programa
def clean_exit():
    print("\nCerrando el programa...")
    if flying:
        drone.send_rc_control(0, 0, 0, 0)
        time.sleep(0.5)
        drone.land()
    cv2.destroyAllWindows()
    drone.streamoff()
    drone.end()
    print("Programa cerrado correctamente.")

def control():
    global flying
    flying = False
    fb_vel = 0  # Velocidad front back
    lr_vel = 0  # Velocidad left right
    ud_vel = 0  # Velocidad up down
    yaw_vel = 0  # Velocidad de rotación sobre el eje

    # Inicialización de los controladores PID
    pid_lr = PID(0.1, 0.01, 0.05, setpoint=width // 2)  # Controlador para el eje horizontal
    pid_ud = PID(0.1, 0.01, 0.05, setpoint=height // 2)  # Controlador para el eje vertical

    # Configuración de límites para las velocidades
    pid_lr.output_limits = (-20, 20)  # Velocidad máxima izquierda/derecha
    pid_ud.output_limits = (-20, 20)  # Velocidad máxima arriba/abajo

    while True:
        frame = drone.get_frame_read().frame
        if frame is None:
            continue

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        frame = cv2.resize(frame, (width, height))

        # Seguimiento del color (detección de objetos)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Valores de los trackbars (puedes ajustarlos en tiempo real con los trackbars)
        lower_hsv = np.array([H_Min_init, S_Min_init, V_Min_init])
        upper_hsv = np.array([H_Max_init, S_Max_init, V_Max_init])

        mask = cv2.inRange(hsv, lower_hsv, upper_hsv)

        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Dibujar lineas de referencia para los límites del centro de la imagen
        cv2.line(frame, (width // 2 - x_threshold, 0), (width // 2 - x_threshold, height), (255, 0, 0), 3)
        cv2.line(frame, (width // 2 + x_threshold, 0), (width // 2 + x_threshold, height), (255, 0, 0), 3)
        cv2.line(frame, (0, height // 2 - y_threshold), (width, height // 2 - y_threshold), (255, 0, 0), 3)
        cv2.line(frame, (0, height // 2 + y_threshold), (width, height // 2 + y_threshold), (255, 0, 0), 3)

        # Despegue automático si la batería es suficiente
        current_battery = drone.get_battery()
        if not flying and current_battery > 15:
            drone.takeoff()
            flying = True

        # Verificar la batería durante el vuelo
        if flying and current_battery <= 10:
            print("Aterrizando, batería muy baja")
            drone.land()
            time.sleep(5)
            flying = False

        # Controles de teclas (mantenimiento de comandos manuales en caso de necesidad)
        key = cv2.waitKey(50) & 0xFF

        if key == ord('c'):
            clean_exit()
            break

        if key == ord('t'):
            if flying:
                pass
            else:
                # Comprobar el nivel de bateria para ver si se puede despegar
                if not flying and current_battery <= 15:
                    print("Nivel de bateria bajo, no se permite volar")
                    continue
                else:
                    drone.takeoff()
                    flying = True

        if key == ord('l'):
            if flying:
                drone.land()
                time.sleep(5)
                flying = False

        if key == ord('w'):
            fb_vel = 60 # Movimiento hacia delante}
            lr_vel = 0
            ud_vel = 0
            yaw_vel = 0
        elif key == ord('s'):
            fb_vel = -60 # Movimiento hacia atrás
            lr_vel = 0
            ud_vel = 0
            yaw_vel = 0
        elif key == ord('a'):
            lr_vel = -60 # Movimiento hacia la izquierda
            fb_vel = 0
            ud_vel = 0
            yaw_vel = 0
        elif key == ord('d'):
            lr_vel = 60 # Movimiento hacia la derecha
            fb_vel = 0
            ud_vel = 0
            yaw_vel = 0
        elif key == ord('r'):
            ud_vel = 60 # Movimiento 
            lr_vel = 0
            fb_vel = 0
            yaw_vel = 0
        elif key == ord('f'):
            ud_vel = -60 # Movimiento descenso
            lr_vel = 0
            fb_vel = 0
            yaw_vel = 0
        elif key == ord('e'):
            yaw_vel = 60 # Giro en sentido horario
            lr_vel = 0
            fb_vel = 0
            ud_vel = 0
        elif key == ord('q'):
            yaw_vel = -60 # Giro en sentido antihorario
            lr_vel = 0
            fb_vel = 0
            ud_vel = 0
        
        else:
            yaw_vel = 0
            lr_vel = 0
            fb_vel = 0
            ud_vel = 0


            min_area = 0.05 * (width * height)  # Área mínima para considerar un objeto
            max_area = 0.08 * (width * height)  # Área máxima para considerar un objeto    
           
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 0.03 * (width * height):  # Filtrar pequeños objetos
                    x, y, w, h = cv2.boundingRect(contour)
                    center = (x + w // 2, y + h // 2)

                    # Dibujar el rectángulo y el centro del objeto
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.circle(frame, center, 5, (0, 0, 255), -1)

                    # Calcular errores
                    error_x = center[0] - (width // 2)
                    error_y = center[1] - (height // 2)

                    # Usar los controladores PID para calcular las velocidades
                    lr_vel = -int(pid_lr(center[0]))  # Velocidad horizontal
                    ud_vel = int(pid_ud(center[1]))  # Velocidad vertical

                    if area < min_area:
                        fb_vel = 15  # Acercarse al objeto
                        cv2.putText(frame, f'Acercandose', (10, 140), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
                    elif area > max_area:
                        fb_vel = -15  # Alejarse del objeto
                        cv2.putText(frame, f'Alejandose', (10, 140), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
                    else:
                        fb_vel = 0  # Mantener la posición
                        cv2.putText(frame, f'Distancia estable', (10, 140), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)

                        # Mostrar información en la pantalla
                        if lr_vel > 0:
                            cv2.putText(frame, f'Objeto a la izquierda', (10, 60), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
                        elif lr_vel < 0:
                            cv2.putText(frame, f'Objeto a la derecha', (10, 60), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
                        else:
                            cv2.putText(frame, f'Objeto centrado horizontalmente', (10, 60), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)

                        if ud_vel > 0:
                            cv2.putText(frame, f'Objeto abajo', (10, 100), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
                        elif ud_vel < 0:
                            cv2.putText(frame, f'Objeto arriba', (10, 100), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
                        else:
                            cv2.putText(frame, f'Objeto centrado verticalmente', (10, 100), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)

                        # Mantener las velocidades de avance y rotación en 0 (puedes agregar controladores PID para estos si es necesario)
                        fb_vel = 0
                        yaw_vel = 0
                        ud_vel = 0

        # Mostrar el video con los resultados
        cv2.imshow('Video Stream', frame)

        # Enviar comandos al dron
        if flying:
            drone.send_rc_control(lr_vel, fb_vel, ud_vel, yaw_vel)

def main():
    try:
        control()
    except KeyboardInterrupt:
        clean_exit()

if __name__ == '__main__':
    main()
