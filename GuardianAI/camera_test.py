import cv2

url = "http://10.123.34.14:8080/video"

cap = cv2.VideoCapture(url)

while True:
    ret, frame = cap.read()

    if not ret:
        print("Cannot read frame")
        break

    cv2.imshow("Guardian AI - Live Camera", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()