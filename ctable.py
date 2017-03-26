import numpy as np
import cv2

width = 6
height = [6, 3, 1, 1]
whole_height = sum(height)

light_start = 0.25
light_end = 0.75

ctable = np.zeros((width, whole_height, 3), dtype=np.float32)

for x in range(width):
  for y in range(height[0]):
    hls = [np.interp(y, (0, height[0]), (0, 360)), np.interp(x, (0, width-1), (light_start, light_end)), 1]
    
    ctable[x, y] = hls
    
  for y in range(height[1]):
    hls = [np.interp(y, (0, height[1]), (0, 360)), np.interp(x, (0, width-1), (light_start, light_end)), 0.50]
    
    ctable[x, height[0]+y] = hls
  
  ctable[x, height[0]+height[1]] = [np.interp(x, (0, width), (0, 360)), 0.5, 1]
  ctable[x, height[0]+height[1]+height[2]] = [0, np.interp(x, (0, width-1), (light_start, 1)), 0]
   
ctable = cv2.cvtColor(ctable, cv2.COLOR_HLS2RGB)
ctable = np.round(ctable*255).astype(np.uint8)

