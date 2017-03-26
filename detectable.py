import cv2
import numpy as np
import math
import sys
from ctable import ctable


"""
This file finds our color table in a photo and saves the averaged colors to a file...

In order to identify our frame, we use two black square frames, one inside another.
This results in 4 consecutive contours having 4 points after approximation.

The bigger frame has thickness and padding equal to X, while the smaller frame has thickness and padding equal to X/2...
This way we identify our frame when we have found 4 frames with distances between top-left corners proportional to 2:2:1 (inside one another)

Okay.. this was my first idea, but it's not a good one, even though in my case it worked... :<

- heavy rotation not supported

ideaz:
- use rect-like figure with 6 points - orientation detection + less ambiguity
- make use of that white border to compare 4 corners of white - and apply kinda correction before
reading the colors
"""

TABLE_COLS = ctable.shape[0]
TABLE_ROWS = ctable.shape[1]

TILE_SIZE = 0.25

THRESHOLD = 70 #for black/white separation
APPROX_EPSILON = 0.005
RATIO_EPSILON = 0.14
MIN_AREA = 300 ** 2

# Only for displaying
CIRCLE_SIZE = 12
CNT_SIZE = 3

if len(sys.argv) < 2:
  print('Provide file name...')
  exit()


filename = sys.argv[1]
img = cv2.imread(filename)
img2 = img.copy()

cv2.namedWindow('image',cv2.WINDOW_NORMAL)
cv2.resizeWindow('image', 600,600)


def cw_rect(pts):
  score = [-float('inf')] * 4
  ret = [None] * 4
    
  for pt in pts:
    for c in range(4):
      t = (-1 if c %3 == 0 else 1) * pt[0][0] - (1-2*(c//2))*pt[0][1]
      
      if t > score[c]:
        score[c] = t
        ret[c] = pt
     
  return np.array(ret, dtype="float32")
  

def show(img):
  cv2.imshow('image',img)

  if cv2.waitKey(0) & 0xff == 27:
    cv2.destroyAllWindows()
    

gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)

ret,edged = cv2.threshold(gray,THRESHOLD,255,1)


im2, contours, hierarchy = cv2.findContours(edged,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)


#contours = sorted(contours, key = cv2.contourArea, reverse = True)
cv2.drawContours(img2, contours, -1, (0,255,0), CNT_SIZE)

#wat??? why???
hierarchy = hierarchy[0]

cand = None
parentstack = []
visited = {}
cidx = 0

while True:
  try:
    curr, cobj = hierarchy[cidx], contours[cidx]
  except:
    print('failidx', cidx)

  was_visited = visited.get(cidx)

  visited[cidx] = True
  
  if not was_visited:
    carea = cv2.contourArea(cobj)
    parentstack.append(False)
    
    if carea > MIN_AREA:
      approx = cw_rect(cv2.approxPolyDP(cobj, APPROX_EPSILON*cv2.arcLength(cobj, True), True))
  
      if len(approx) == 4:
        parentstack.pop()
        parentstack.append(approx) 
      
        # Check if last 4 were rectangles
        last4 = parentstack[-4:]
        if len(last4) == 4 and not bool in [type(x) for x in last4]:
          rect = last4[0][:,0]

          cand_w = min((rect[1]-rect[0])[0],(rect[2]-rect[3])[0])
          cand_h = min((rect[2]-rect[1])[1],(rect[3]-rect[0])[1])
          
          # Now compute the ratios, but apply perspective transform first
          # otherwise we could reject valid candidates

          cand_M = cv2.getPerspectiveTransform(rect, np.float32([[0, 0], [cand_w, 0], [cand_w, cand_h], [0, cand_h]]))
          frames = [None]*4
          
          for t in range(4):
            frames[t] = last4[t].copy()
            frames[t] = cv2.perspectiveTransform(last4[t], cand_M)           
          
          ratios = []
          for t in range(3):
            p1 = frames[t+1][0][0]
            p2 = frames[t][0][0]

            ratios.append(np.linalg.norm(p1-p2))
     
          print('ratio1/0', abs(ratios[1]/ratios[0]))
          print('ratio2/1', abs(ratios[2]/ratios[1]))
            
          if abs(1-ratios[1]/ratios[0]) < RATIO_EPSILON and abs(0.5-ratios[2]/ratios[1]) < RATIO_EPSILON:
            cand = frames
            break

  if not was_visited and curr[2] != -1: #traverse children
    cidx = curr[2]
    
  elif curr[0] != -1: #next sibling
    cidx = curr[0]

  elif curr[3] != -1: #go to parent
    parentstack.pop()
    cidx = curr[3]
  
  else:
    break
  

    
if not cand:
  print('Found no candidates...')
  show(img2)
  show(edged)
  exit(1)
  

for x in range(4):
  cv2.circle(img2, tuple(last4[3][x][0]), CIRCLE_SIZE, (0,0,255), -1)

rect = cand[2][:,0]+2*(cand[3][:,0]-cand[2][:,0])

#average frame borders to increase precision

rect[0][0] = rect[3][0] = (rect[0][0]+rect[3][0])/2
rect[1][0] = rect[2][0] = (rect[1][0]+rect[2][0])/2
rect[0][1] = rect[1][1] = (rect[0][1]+rect[1][1])/2
rect[2][1] = rect[3][1] = (rect[2][1]+rect[3][1])/2


val, inv_M = cv2.invert(cand_M)

rect = cv2.perspectiveTransform(np.asarray([rect]), inv_M)[0]

w = min((rect[1]-rect[0])[0],(rect[2]-rect[3])[0])
h = min((rect[2]-rect[1])[1],(rect[3]-rect[0])[1])


M = cv2.getPerspectiveTransform(rect, np.float32([[0, 0], [w, 0], [w, h], [0, h]]))

dst = cv2.warpPerspective(img,M,(w,h))
show(dst)


neigh_x = int(TILE_SIZE*w/TABLE_COLS)
neigh_y = int(TILE_SIZE*h/TABLE_ROWS)

vctable = np.zeros((TABLE_COLS, TABLE_ROWS, 3), dtype=np.int32)

for x in range(TABLE_COLS):
  for y in range(TABLE_ROWS):
    cx, cy = int(w*(x+0.5)/TABLE_COLS), int(h*(y+0.5)/TABLE_ROWS)
    
    avg = np.mean(dst[cy-neigh_y:cy+neigh_y,cx-neigh_x:cx+neigh_x], axis=(0,1))
    
    #dst[cy-neigh_y:cy+neigh_y,cx-neigh_x:cx+neigh_x] = avg
    dst[cy-neigh_y:cy+neigh_y,cx-neigh_x:cx+neigh_x] = (0,0,255)
    
    vctable[x, y] = avg[::-1]
    
cv2.imshow('image',dst)

if cv2.waitKey(0) & 0xff == 27:
    cv2.destroyAllWindows()

np.save('color-table', vctable)

print('Table saved to color-table.npy')












 