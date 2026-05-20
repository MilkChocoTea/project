import cv2
import numpy as np
print('cv2 version:', cv2.__version__)
try:
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    marker = cv2.aruco.generateImageMarker(aruco_dict, 0, 200)
    cv2.imwrite('aruco_marker_0.png', marker)
    print('成功')
except Exception as e:
    print('錯誤:', e)