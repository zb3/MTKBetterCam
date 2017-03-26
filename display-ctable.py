import numpy as np
import cv2
from ctable import ctable

block_width, block_height = 100, 100
border = 60

canvas_width, canvas_height = ctable.shape[0]*block_width, ctable.shape[1]*block_height
border2 = border//2

img_w, img_h = canvas_width + 8*border, canvas_height + 8*border
img = np.zeros((img_h, img_w, 3), dtype=np.uint8)

img[:,:] = (255,255,255)

cframe = border

img[cframe:-cframe, cframe:-cframe] = (0,0,0)

cframe += border
img[cframe:-cframe, cframe:-cframe] = (255,255,255)

cframe += border

img[cframe:-cframe, cframe:-cframe] = (0,0,0)

cframe += border2

img[cframe:-cframe, cframe:-cframe] = (255,255,255)

cframe += border2

img[cframe:-cframe, cframe:-cframe] = (0,255,0)


for x in range(ctable.shape[0]):
  xstart = cframe + x*block_width
  
  for y in range(ctable.shape[1]):
    ystart = cframe + y*block_height
    img[ystart:ystart+block_height,xstart:xstart+block_width] = ctable[x,y][::-1]


cv2.namedWindow('image',cv2.WINDOW_NORMAL)
cv2.moveWindow('image', 300, 80)
cv2.resizeWindow('image', 600, 600)
cv2.imshow('image',img)


if cv2.waitKey(0) & 0xff == 27:
  cv2.destroyAllWindows()
