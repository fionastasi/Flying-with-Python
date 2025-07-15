import cv2
import mediapipe as mp
import time
from djitellopy import Tello

# Inicialización del dron
drone = Tello()
drone.connect()
drone.streamon()
print(f"Batería: {drone.get_battery()}%")

# Trackbars
cv2.namedWindow("Configuracion")
def nothing(x): pass
cv2.createTrackbar("Velocidad", "Configuracion", 60, 100, nothing)
cv2.createTrackbar("AlturaMax", "Configuracion", 300, 500, nothing)

# Variables de control
flying = False
modo_gestos = True
speed = 60
MAX_HEIGHT_CM = 300
lr_vel = fb_vel = ud_vel = yaw_vel = 0

# MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

# Landmarks 
THUMB_TIP = 4
THUMB_IP = 3
INDEX_TIP = 8
MIDDLE_TIP = 12
RING_TIP = 16
PINKY_TIP = 20

# Funciones de reconocimiento de gestos
def contar_dedos(lm):
    return sum(lm[i].y < lm[i - 2].y for i in [INDEX_TIP, MIDDLE_TIP, RING_TIP, PINKY_TIP])

def pulgar_extendido(lm):
    return lm[THUMB_TIP].x < lm[THUMB_IP].x

def is_fist(lm):
    return all(lm[i].y > lm[i - 2].y for i in [INDEX_TIP, MIDDLE_TIP, RING_TIP, PINKY_TIP])

def is_only_pinky(lm):
    return (contar_dedos(lm) == 1 and lm[PINKY_TIP].y < lm[PINKY_TIP - 2].y)

def is_cuernito(lm):
    return (lm[INDEX_TIP].y < lm[INDEX_TIP - 2].y and
            lm[PINKY_TIP].y < lm[PINKY_TIP - 2].y and
            all(lm[i].y > lm[i - 2].y for i in [MIDDLE_TIP, RING_TIP]))

def is_CW(lm):
    return (pulgar_extendido(lm) and 
            lm[INDEX_TIP].y < lm[INDEX_TIP - 2].y and
            all(lm[i].y > lm[i - 2].y for i in [MIDDLE_TIP, RING_TIP, PINKY_TIP]))

def is_palma_abierta(lm):
    return contar_dedos(lm) == 5

# Variables de estado
fist_start_time = None
fist_confirmed = False

# Cámara
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

# Loop principal
while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)
    tiempo_actual = time.time()

    # Actualizar desde trackbars
    speed = cv2.getTrackbarPos("Velocidad", "Configuracion")
    MAX_HEIGHT_CM = cv2.getTrackbarPos("AlturaMax", "Configuracion")

    label = "Sin gesto"
    lr_vel = fb_vel = ud_vel = yaw_vel = 0

    if modo_gestos and result.multi_hand_landmarks:
        lm = result.multi_hand_landmarks[0].landmark
        mp_draw.draw_landmarks(frame, result.multi_hand_landmarks[0], mp_hands.HAND_CONNECTIONS)

        if is_fist(lm):
            if fist_start_time is None:
                fist_start_time = tiempo_actual
                fist_confirmed = False
            elif tiempo_actual - fist_start_time >= 2.5 and not fist_confirmed:
                if not flying:
                    if drone.get_battery() > 15:
                        drone.takeoff()
                        flying = True
                        label = "Despegando..."
                    else:
                        label = "Batería baja"
                else:
                    drone.send_rc_control(0, 0, 0, 0)
                    drone.land()
                    flying = False
                    label = "Aterrizando..."
                fist_confirmed = True
            else:
                label = "Puño detectado (mantén...)"
        else:
            fist_start_time = None
            fist_confirmed = False

            if is_only_pinky(lm):
                ud_vel = speed
                label = "Subir"
            elif is_cuernito(lm):
                ud_vel = -speed
                label = "Bajar"
            elif is_CW(lm):
                yaw_vel = speed
                label = "Girar CW"
            elif contar_dedos(lm) == 1 and not pulgar_extendido(lm):
                fb_vel = speed
                label = "Adelante"
            elif contar_dedos(lm) == 2:
                fb_vel = -speed
                label = "Atrás"
            elif contar_dedos(lm) == 3:
                lr_vel = speed
                label = "Derecha"
            elif contar_dedos(lm) == 4:
                if not pulgar_extendido(lm):
                    lr_vel = -speed
                    label = "Izquierda"
                else:
                    yaw_vel = -speed
                    label = "Girar CCW"
            elif is_palma_abierta(lm):
                label = "Detenido (palma)"
            else:
                label = "Sin gesto claro"
    elif modo_gestos:
        label = "Sin detección - Parado"

    # Mostrar estado
    estado = "VOLANDO" if flying else "EN TIERRA"
    modo = "GESTOS" if modo_gestos else "TECLADO"
    cv2.putText(frame, f"Estado: {estado} | Modo: {modo}", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    cv2.putText(frame, f"Gesto: {label}", (10, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
    cv2.imshow("Control por Gestos - Drone", frame)

    if flying:
        drone.send_rc_control(lr_vel, fb_vel, ud_vel, yaw_vel)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        if flying:
            drone.send_rc_control(0, 0, 0, 0)
            time.sleep(0.3)
            drone.land()
        break
    elif key == ord('g'):
        modo_gestos = not modo_gestos
        print("Modo de control:", "Gestos" if modo_gestos else "Teclado")
    elif not modo_gestos:
        # Controles por teclado
        if key == ord('w'):
            fb_vel = speed
        elif key == ord('s'):
            fb_vel = -speed
        elif key == ord('a'):
            lr_vel = -speed
        elif key == ord('d'):
            lr_vel = speed
        elif key == ord('e'):
            yaw_vel = speed
        elif key == ord('q'):
            yaw_vel = -speed
        elif key == ord('r'):
            ud_vel = speed
        elif key == ord('f'):
            ud_vel = -speed
        drone.send_rc_control(lr_vel, fb_vel, ud_vel, yaw_vel)

# Finalización
cap.release()
cv2.destroyAllWindows()
drone.streamoff()
drone.end()