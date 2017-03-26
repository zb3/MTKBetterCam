import sys
import numpy as np
import cv2
import pickle

if len(sys.argv) < 2:
  print('Provide file name...')
  exit()

filename = sys.argv[1]
img = cv2.imread(filename)

with open('model.data', 'rb') as f:
  cls = pickle.loads(f.read())

for row in img:
  pixels = row.astype(np.float32)
    
  pixels = pixels/255

  pixels = 255*cls.predict(pixels[:,::-1])
  
  row[...] = np.round(pixels[:,::-1]).clip(0, 255).astype(np.uint8)
  
  
cv2.imwrite(filename+'.out.ppm', img);
print('Image written to', filename+'.out.ppm')