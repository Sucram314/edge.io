import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
import pygame.gfxdraw
import pygame.font
import math
import sys
import colorsys as coloursys
from collections import deque
import time
from pyperclip import copy,paste
from bisect import bisect
import random

pygame.init()
pygame.font.init()

fonts = [pygame.font.SysFont("Verdana",size=i) for i in range(201)]
sizes = [font.size("0")[0] for font in fonts]
font = fonts[50]
header = fonts[100]

clock = pygame.time.Clock()

width = 1280
height = 600
hwidth = width//2
hheight = height//2

pygame.display.set_caption("edge.io")
pygame.display.set_icon(pygame.image.load("C:\\Users\\marcu\\OneDrive\\Pictures\\Saved Pictures\\expressionless.png"))
screen = pygame.display.set_mode((width,height),pygame.RESIZABLE)

BG = (0,0,0)
BLACK = (0,0,0)
WHITE = (255,255,255)
COLS = [(255,95,87),(0,162,255),(118,202,62),(255,191,47),(203,47,255),(47,255,227),(230,230,230)]

SIZE = 50
BAND = 2
LABELSIZE = 14
LABELFONT = fonts[bisect(sizes,LABELSIZE)]

SCENE = "menu"

class Camera:
    def __init__(self,x=0,y=0,m=1):
        self.x = x
        self.y = y
        self.m = m
        self.xv = 0
        self.yv = 0
        self.mv = 0
        self.maxZoom = 5
        self.minZoom = 0.1
        self.cameraPanSpeed = 0.1
        self.cameraZoomSpeed = 0.01
        self.cameraPanFriction = 0.9
        self.cameraZoomFriction = 0.9
        self.offx = hwidth
        self.offy = hheight

    def reset(self,x=0,y=0,m=1):
        self.x = x
        self.y = y
        self.m = m
        self.xv = 0
        self.yv = 0
        self.mv = 0
        self.offx = hwidth
        self.offy = hheight

    def update(self,keys,mx,my,scrolling,dt):
        if keys[pygame.K_w]:
            self.yv -= self.cameraPanSpeed
        elif keys[pygame.K_s]:
            self.yv += self.cameraPanSpeed
        if keys[pygame.K_a]:
            self.xv -= self.cameraPanSpeed
        elif keys[pygame.K_d]:
            self.xv += self.cameraPanSpeed

        if scrolling:
            self.mv += scrolling*self.cameraZoomSpeed*self.m
            self.x,self.y = self.invcoord(mx,my)
            self.offx = mx
            self.offy = my
            
        self.xv *= self.cameraPanFriction
        self.yv *= self.cameraPanFriction
        self.mv *= self.cameraZoomFriction
        self.x += dt*self.xv/self.m
        self.y += dt*self.yv/self.m
        self.m += self.mv
        if self.m > self.maxZoom:
            self.m = self.maxZoom
            self.mv = 0
        elif self.m < self.minZoom:
            self.m = self.minZoom
            self.mv = 0

        global LABELFONT
        LABELFONT = fonts[bisect(sizes,round(LABELSIZE*self.m))]

    def scale(self,x):
        return round(x*self.m)
        
    def coord(self,x,y):
        return (round((x-self.x)*self.m + self.offx),round((y-self.y)*self.m + self.offy))

    def invcoord(self,x,y):
        return (round((x - self.offx)/self.m + self.x),round((y - self.offy)/self.m + self.y))
    
class Button:
    def __init__(self,x,y,w,h,text,col,func=lambda:None,*args):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.surface = pygame.Surface((w,h))
        self.surface.fill(col)
        text = font.render(text,1,WHITE)
        self.surface.blit(text,((self.w-text.get_width())//2,(self.h-text.get_height())//2))
        self.func = func
        self.args = args

    def draw(self):
        screen.blit(self.surface,camera.coord(self.x,self.y))
    
    def update(self,x,y,click):
        x,y = camera.invcoord(x,y)
        if self.x <= x <= self.x + self.w and self.y <= y <= self.y + self.h and click:
            self.func(*self.args)

class Slider:
    def __init__(self,x,y,w,h,text,val,valmax,valmin,snap=True):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.text = fonts[30].render(text,1,WHITE)
        self.val = val
        self.valmin = valmax
        self.valmax = valmin
        self.snap = snap

        self.sliding = False

    def draw(self):
        screen.blit(self.text,camera.coord(self.x-self.text.get_width()-4*BAND,self.y+(self.h-self.text.get_height())/2))
        draw_rect(self.x,self.y,self.w,self.h,WHITE)
        t = (self.val - self.valmin) / (self.valmax - self.valmin)
        w = (self.w-2*BAND)*t
        draw_rect(self.x+BAND+w,self.y+BAND,self.w-2*BAND-w,self.h-2*BAND,BG)
        
        text = fonts[30].render(str(self.val),1,WHITE)
        screen.blit(text,camera.coord(self.x+self.w+4*BAND,self.y+(self.h-text.get_height())/2))

    def update(self,x,y,click,mdown):
        x,y = camera.invcoord(x,y)
        if self.x <= x <= self.x + self.w and self.y <= y <= self.y + self.h and click:
            self.sliding = True

        if self.sliding:
            if mdown:
                self.val = min(1,max(0,(x - self.x) / self.w)) * (self.valmax - self.valmin) + self.valmin
                if self.snap: 
                    self.val = round(self.val)
            else:
                self.sliding = False
    
camera = Camera()

def ease(t):
    return (1 - math.cos(t * math.pi)) / 2

def ease_in(t):
    return 1 - math.cos(t * math.pi / 2)

def lerp(a,b,t):
    return a + (b-a)*t

def mute(col,t=0.5):
    col = coloursys.rgb_to_hsv(*map(lambda x:x/255,col))
    return tuple(map(lambda x:round(x*255), coloursys.hsv_to_rgb(col[0], col[1]*t, col[2])))

def collerp(col1,col2,t):
    return (lerp(col1[0],col2[0],t),lerp(col1[1],col2[1],t),lerp(col1[2],col2[2],t))

def draw_rect(x,y,w,h,col,surface=screen):
    pygame.draw.rect(surface,col,(camera.coord(x,y),(camera.scale(w),camera.scale(h))))

def rot(x,y,a,cx=0,cy=0):
    cos = math.cos(a)
    sin = math.sin(a)
    
    x -= cx
    y -= cy

    rx = x * cos - y * sin
    ry = x * sin + y * cos

    return rx + cx, ry + cy

def draw_rotrect(x,y,w,h,a,col,surface=screen):
    a = math.radians(a)
    
    p = [(x-w/2,y-h/2),(x+w/2,y-h/2),(x+w/2,y+h/2),(x-w/2,y+h/2)]
    p = list(map(lambda s:camera.coord(*rot(s[0],s[1],a,x,y)),p))

    pygame.gfxdraw.filled_polygon(surface,p,col)
    pygame.gfxdraw.aapolygon(surface,p,col)

def draw_circle(x,y,r,col):
    r = camera.scale(r)
    pygame.gfxdraw.filled_circle(screen,*camera.coord(x,y),r,col)
    pygame.gfxdraw.aacircle(screen,*camera.coord(x,y),r,col)

def start(players):
    global SCENE
    game.__init__(sliders[0].val,sliders[1].val,players,sliders[2].val,sliders[3].val)
    SCENE = "game"

BWIDTH = 100
SPACE = 20
BHEIGHT = 80
buttons = []
offx = (6 * BWIDTH + 5 * SPACE) // 2
offy = BHEIGHT // 2
for i in range(6):
    buttons.append(Button(i*(BWIDTH+SPACE) - offx, -offy, BWIDTH, BHEIGHT, f"{i+1}P", COLS[i], start, i+1))

sliders = []
sliders.append(Slider(-350,100,200,50,"width",9,3,20))
sliders.append(Slider(-350,200,200,50,"height",9,3,20))
sliders.append(Slider(150,100,200,50,"endgame",50,10,100))
sliders.append(Slider(150,200,200,50,"interval",2,1,10))

def events():
    dt = clock.tick(60)

    scrolling = 0
    click = 0
    mdown = pygame.mouse.get_pressed()[0]
    mx,my = pygame.mouse.get_pos()
    keys = pygame.key.get_pressed()
    ctrl = keys[pygame.K_LCTRL]
    ctrlzoom = 0

    global width,height,hwidth,hheight,game,SCENE
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if SCENE == "menu":
                    pygame.quit()
                    sys.exit()
                elif SCENE == "game" and not game.waiting:
                    camera.reset()
                    SCENE = "menu"
            elif ctrl:
                if event.key == pygame.K_EQUALS:
                    scrolling = 2
                    ctrlzoom = 1
                elif event.key == pygame.K_MINUS:
                    scrolling = -2
                    ctrlzoom = 1
                elif event.key == pygame.K_0:
                    camera.reset()
                elif event.key == pygame.K_c and SCENE == "game" and not game.waiting:
                    game.save()
                elif event.key == pygame.K_v and (SCENE != "game" or not game.waiting):
                    game.load()
            
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mdown = click = 1
                if SCENE == "game" and not game.waiting:
                    x,y = game.coord(mx,my)
                    
                    if game.valid(x,y) and (game.move != 1 or game.check(x,y)):
                        game.play(x,y)

            elif event.button == 4: 
                scrolling = 1
            elif event.button == 5: 
                scrolling = -1
        elif event.type == pygame.WINDOWRESIZED:
            width = event.x
            height = event.y
            x = hwidth
            y = hheight
            hwidth = width // 2
            hheight = height // 2
            camera.offx += hwidth - x
            camera.offy += hheight - y

    if SCENE == "game":
        if ctrlzoom:
            mx = hwidth
            my = hheight
            
        camera.update(keys,mx,my,scrolling,dt)
    elif SCENE == "menu":
        for button in buttons:
            button.update(mx,my,click)

        for slider in sliders:
            slider.update(mx,my,click,mdown)

class Animation:
    def __init__(self,shape,x,y,dx,dy,t=0.5,s=0,col=None,X=0,Y=0):
        self.shape = shape
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.t = t
        self.s = s
        self.col = col
        self.X = X
        self.Y = Y

    def update(self,t):
        t = ease(max(0,min(1,(t-self.s)/self.t)))

        if self.shape <= 2:
            x = round(self.x + self.dx * t)
            y = round(self.y + self.dy * t)

            if self.shape == 0:
                draw_circle(x,y,SIZE//15,WHITE)
            elif self.shape == 1:
                draw_circle(x,y, 2 * (SIZE - 2*BAND) // 5, self.col)
            else:
                draw_circle(x,y, 2 * (SIZE - 2*BAND) // 5, self.col)
                draw_circle(x,y,SIZE//15,WHITE)
        elif self.shape <= 4:
            col = collerp(self.dx,self.dy,t)
            if self.shape == 3:
                cur = game.get(self.X,self.Y)
                dif = cur.lifetime - game.move
                if 0 <= dif <= 5:
                    draw_rect(self.x+2*BAND+BAND//2+game.shakes[self.Y][self.X][0],self.y+2*BAND+BAND//2+game.shakes[self.Y][self.X][1],SIZE-5*BAND,SIZE-5*BAND,col)
                else:
                    draw_rect(self.x+BAND,self.y+BAND,SIZE-2*BAND,SIZE-2*BAND,col)
            else:
                draw_circle(self.x,self.y, 2 * (SIZE - 2*BAND) // 5, col)

class Particle:
    def __init__(self,shape,x,y,a=0,vx=0,vy=0,va=0,col=None):
        self.shape = shape
        self.x = x
        self.y = y
        self.a = a
        self.vx = vx
        self.vy = vy
        self.va = va
        self.col = col

    def update(self):
        self.vy -= 1
        self.x += self.vx
        self.y -= self.vy
        self.a += self.va
        return self.y <= height*2
            
    def draw(self):
        if self.shape == 0:
            draw_rotrect(self.x,self.y,SIZE-2*BAND,SIZE-2*BAND,self.a,collerp(COLS[-1],BLACK,0.05))

class Cell:
    def __init__(self,x,y,num=0,player=-1):
        self.num = num
        self.player = player
        self.x = x
        self.y = y
        self.lifetime = sys.maxsize

    def start(self,player):
        self.player = player
        self.num = 3

    def stock(self,player,animate=False):
        offx = SIZE*game.w//2
        offy = SIZE*game.h//2
        tx = self.x * SIZE - offx
        ty = self.y * SIZE - offy
        cx = tx + SIZE//2
        cy = ty + SIZE//2
        
        col1 = COLS[-1]
        col1bruh = COLS[self.player]
        if self.player == game.turn:
            if self.num == 1: col1 = mute(COLS[self.player],0.4)
            elif self.num == 2: col1 = mute(COLS[self.player],0.5)
            elif self.num == 3: col1 = mute(COLS[self.player],0.7)
            else: col1 = mute(COLS[self.player],0.8)

        self.player = player
        self.num += 1

        col2 = COLS[-1]
        col2bruh = COLS[self.player]
        if self.player == game.turn:
            if self.num == 1: col2 = mute(COLS[self.player],0.4)
            elif self.num == 2: col2 = mute(COLS[self.player],0.5)
            elif self.num == 3: col2 = mute(COLS[self.player],0.7)
            else: col2 = mute(COLS[self.player],0.8)

        s = 0 if animate else 0.2

        game.animations.appendleft(Animation(3,tx,ty,col1,col2,X=self.x,Y=self.y))
        if self.num > 1:
            game.animations.append(Animation(4,cx,cy,col1bruh,col2bruh))
            if self.num == 2:
                q = SIZE//8
                game.animations.append(Animation(0,cx,cy,q,0,s=s))
                game.animations.append(Animation(0,cx,cy,-q,0,s=s))
            elif self.num == 3:
                o = SIZE//8
                p = SIZE//6
                q = round(math.sin(math.radians(120)) * p)
                r = round(math.cos(math.radians(120)) * p)
                game.animations.append(Animation(0,cx,cy,0,-p,s=s))
                game.animations.append(Animation(0,cx-o,cy,o-q,-r,s=s))
                game.animations.append(Animation(0,cx+o,cy,q-o,-r,s=s))
            elif self.num >= 4:
                o = SIZE//8
                p = SIZE//6
                q = round(math.sin(math.radians(120)) * p)
                r = round(math.cos(math.radians(120)) * p)
                game.animations.append(Animation(0,cx,cy-p,o,p-o,s=s))
                game.animations.append(Animation(0,cx,cy-p,-o,p-o,s=s))
                game.animations.append(Animation(0,cx-q,cy-r,q-o,r+o,s=s))
                game.animations.append(Animation(0,cx+q,cy-r,o-q,r+o,s=s))
            
        if animate: game.animate()
            
        return self.num == 4

    def explode(self):
        self.num = 0
        self.player = -1

    def remove(self):
        if self.player != -1: game.scores[self.player] -= self.num
        self.num = -1
        self.player = -1

        offx = SIZE*game.w//2
        offy = SIZE*game.h//2
        tx = self.x * SIZE - offx
        ty = self.y * SIZE - offy
        cx = tx + SIZE//2
        cy = ty + SIZE//2
            
        game.particles.append(Particle(0,cx,cy,0,random.random()*10-5,random.random()*10+5,random.random()*2-1))

    def draw(self):
        offx = SIZE*game.w//2
        offy = SIZE*game.h//2
        
        tx = self.x * SIZE - offx
        ty = self.y * SIZE - offy

        cx = tx + SIZE//2
        cy = ty + SIZE//2

        if self.x == 0:
            label = LABELFONT.render(str(game.h-self.y),1,COLS[-1])
            x,y = camera.coord(cx-SIZE,cy)
            screen.blit(label,(x-label.get_width()//2,y-label.get_height()//2))

        if self.y == game.h-1:
            label = LABELFONT.render(chr(ord("a")+self.x),1,COLS[-1])
            x,y = camera.coord(cx,cy+SIZE)
            screen.blit(label,(x-label.get_width()//2,y-label.get_height()//2))

        if self.num == -1:
            draw_rect(tx + BAND, ty + BAND, SIZE - 2*BAND, SIZE - 2*BAND, mute(BG,0.95))
            return

        col = COLS[-1]
        if self.player == game.turn:
            if self.num == 1: col = mute(COLS[self.player],0.4)
            elif self.num == 2: col = mute(COLS[self.player],0.5)
            elif self.num == 3: col = mute(COLS[self.player],0.7)
            else: col = mute(COLS[self.player],0.8)

        dif = self.lifetime - game.move
        if 0 <= dif < 6:
            if dif > 5:
                t = 6 - dif
                outline = collerp(COLS[-1],mute((255,255,0),0.8),t)
            else:
                t = 1 - ease_in(1 - dif / 5)
                outline = mute((255,round(255 * t),0),0.8)

            s = game.shakes[self.y][self.x] = ((random.random() - 0.5) * (1 + (6 - dif)/3),(random.random() - 0.5) * (1 + (6 - dif)/3))
            sx = tx + s[0]
            sy = ty + s[1]

            draw_rect(sx + BAND, sy + BAND, SIZE - 2*BAND, SIZE - 2*BAND, outline)
            draw_rect(sx + 2*BAND + BAND//2, sy + 2*BAND + BAND//2, SIZE - 5*BAND, SIZE - 5*BAND, col)
        else:
            draw_rect(tx + BAND, ty + BAND, SIZE - 2*BAND, SIZE - 2*BAND, col)
        
        if self.num <= 0:
            return
        
        draw_circle(cx,cy, 2 * (SIZE - 2*BAND) // 5, COLS[self.player])

        R = SIZE // 15
        
        if self.num == 1:
            draw_circle(cx,cy,R,WHITE)
        elif self.num == 2:
            q = SIZE//8
            draw_circle(cx+q,cy,R,WHITE)
            draw_circle(cx-q,cy,R,WHITE)
        elif self.num == 3:
            p = SIZE//6
            q = round(math.sin(math.radians(120)) * p)
            r = round(math.cos(math.radians(120)) * p)
            
            draw_circle(cx,cy-p,R,WHITE)
            draw_circle(cx-q,cy-r,R,WHITE)
            draw_circle(cx+q,cy-r,R,WHITE)
        elif self.num >= 4:
            q = SIZE//8
            draw_circle(cx+q,cy+q,R,WHITE)
            draw_circle(cx+q,cy-q,R,WHITE)
            draw_circle(cx-q,cy-q,R,WHITE)
            draw_circle(cx-q,cy+q,R,WHITE)

class Game:
    def __init__(self,w=9,h=9,players=4,endgame=50,interval=2):
        self.w = w
        self.h = h
        self.players = players
        self.scores = [0]*self.players
        self.board = [[Cell(i,j) for i in range(w)] for j in range(h)]
        self.turn = 0
        self.move = 1
        self.endgame = endgame
        self.interval = interval
        self.queue = deque()
        self.animations = deque()
        self.particles = []
        self.waiting = False

        self.shrunk = 0
        s = sorted([((2*i-self.w+1)**2+(2*j-self.h+1)**2,i,j) for i in range(self.w) for j in range(self.h) if abs(2*i-self.w+1) > 4 or abs(2*j-self.h+1) > 4], reverse=True)
        
        if s:
            self.remove = [[(s[0][1],s[0][2])]]
            self.get(s[0][1],s[0][2]).lifetime = self.endgame
            
            for i in range(1,len(s)):                
                if s[i][0] == s[i-1][0]:
                    self.remove[-1].append((s[i][1],s[i][2]))
                else:
                    self.remove.append([(s[i][1],s[i][2])])

                self.get(s[i][1],s[i][2]).lifetime = self.endgame + (len(self.remove) - 1) * self.interval

        self.shakes = [[(0,0)]*self.w for i in range(self.h)]

    def save(self):
        res = chr(48+self.w)+chr(48+self.h)+chr(48+self.players)+chr(48+self.turn)+"#"+str(self.move)+"#"+str(self.shrunk)+"#"+str(self.endgame)+"#"+str(self.interval)+"#"
        for y in range(self.h):
            for x in range(self.w):
                cur = self.get(x,y)
                res += chr(48+cur.num+cur.player*6)
        copy(res)
        send_message(0)

    def load(self):
        global SCENE

        try:
            p = paste()
            self.w = ord(p[0]) - 48
            self.h = ord(p[1]) - 48
            self.players = ord(p[2]) - 48

            assert self.w > 0 and self.h > 0 and self.players > 0

            self.turn = ord(p[3]) - 48
            assert 0 <= self.turn < self.players

            p = p.split("#")

            self.move = int(p[1])
            assert self.move >= 1

            self.shrunk = int(p[2])
            assert self.shrunk >= 0

            self.endgame = int(p[3])
            assert self.endgame >= 10

            self.interval = int(p[4])
            assert self.interval >= 1

            p = p[5]
            self.board = []
            self.scores = [0]*self.players
            idx = 0
            
            for y in range(self.h):
                self.board.append([])
                for x in range(self.w):
                    val = ord(p[idx])-47
                    num = val % 6 - 1
                    player = val // 6

                    assert -1 <= num <= 3 and -1 <= player < self.players

                    if player != -1: self.scores[player] += num
                    self.board[y].append(Cell(x,y,num,player))
                    idx += 1

            s = sorted([((2*i-self.w+1)**2+(2*j-self.h+1)**2,i,j) for i in range(self.w) for j in range(self.h) if abs(2*i-self.w+1) > 4 or abs(2*j-self.h+1) > 4], reverse=True)
        
            if s:
                self.remove = [[(s[0][1],s[0][2])]]
                self.get(s[0][1],s[0][2]).lifetime = self.endgame
                
                for i in range(1,len(s)):                
                    if s[i][0] == s[i-1][0]:
                        self.remove[-1].append((s[i][1],s[i][2]))
                    else:
                        self.remove.append([(s[i][1],s[i][2])])

                    self.get(s[i][1],s[i][2]).lifetime = self.endgame + (len(self.remove) - 1) * self.interval
            
            SCENE = "game"
            send_message(1)
        except Exception as e:
            SCENE = "menu"
            send_message(2)
        
    def get(self,x,y):
        return self.board[y][x]

    def valid(self,x,y):
        return 0 <= x < self.w and 0 <= y < self.h and self.get(x,y).num != -1

    def adjacent(self,x,y):
        if self.valid(x-1,y): yield x-1,y,-1,0
        if self.valid(x+1,y): yield x+1,y,1,0
        if self.valid(x,y-1): yield x,y-1,0,-1
        if self.valid(x,y+1): yield x,y+1,0,1

    def influence(self,x,y):
        if self.valid(x-1,y): yield x-1,y
        if self.valid(x-1,y-1): yield x-1,y-1
        if self.valid(x,y-1): yield x,y-1
        if self.valid(x+1,y-1): yield x+1,y-1
        if self.valid(x+1,y): yield x+1,y
        if self.valid(x+1,y+1): yield x+1,y+1
        if self.valid(x,y+1): yield x,y+1
        if self.valid(x-1,y+1): yield x-1,y+1
        if self.valid(x-2,y): yield x-2,y
        if self.valid(x,y-2): yield x,y-2
        if self.valid(x+2,y): yield x+2,y
        if self.valid(x,y+2): yield x,y+2

    def check(self,x,y):
        for nx,ny in self.influence(x,y):
            cur = self.get(nx,ny)
            if cur.player != -1 and cur.player != self.turn:
                return False
            
        return True

    def coord(self,x,y):
        x,y = camera.invcoord(x,y)
        return (x + SIZE*self.w//2) // SIZE, (y + SIZE*self.h//2) // SIZE

    def animate(self,T=0.25):
        global BG
        
        if not self.animations: return
        self.waiting = True
        
        a = time.time()
        dif = 0
        while dif <= T:
            dif = time.time()-a
            t = dif / T
            
            events()
            BG = mute(COLS[game.turn],t=0.6)
            screen.fill(BG)
            self.draw()
            
            for animation in self.animations:
                animation.update(t)

            pygame.display.flip()

        self.animations.clear()
        self.waiting = False

    def play(self,x,y):
        global BG
        
        offx = SIZE*game.w//2
        offy = SIZE*game.h//2
            
        cur = self.get(x,y)
        
        if cur.player != self.turn and (cur.player != -1 or self.move != 1):
            return
        
        if self.move == 1:
            cur.start(self.turn)
            self.scores[self.turn] = 3

            col1 = mute(COLS[game.turn],t=0.6)
            
            self.turn += 1
            if self.turn == self.players:
                self.move += 1
                self.turn = 0

            col2 = mute(COLS[game.turn],t=0.6)

            a = time.time()
            dif = 0
            self.waiting = True
            while dif <= 0.2:
                dif = time.time()-a
                t = dif / 0.2
                
                events()
                BG = collerp(col1,col2,ease(t))
                screen.fill(BG)
                self.draw()
                pygame.display.flip()
            self.waiting = False
            return

        self.scores[self.turn] += 1
        if cur.stock(self.turn,animate=True):
            self.queue.append((x,y))
            
            while self.queue:
                for i in range(len(self.queue)):
                    curx, cury = self.queue.popleft()
                    cx = curx * SIZE - offx + SIZE//2
                    cy = cury * SIZE - offy + SIZE//2

                    self.get(curx,cury).explode()

                    edged = 4
                    for nexx,nexy,dx,dy in self.adjacent(curx, cury):
                        self.animations.append(Animation(2,cx,cy,dx*SIZE,dy*SIZE,col=COLS[game.turn]))
                        
                        nex = self.get(nexx,nexy)
                        edged -= 1

                        if nex.player != self.turn and nex.player != -1: 
                            self.scores[nex.player] -= nex.num
                            self.scores[self.turn] += nex.num

                        if nex.num >= 4: 
                            self.scores[self.turn] -= 1
                        
                        if nex.stock(self.turn):
                            self.queue.append((nexx,nexy))

                    self.scores[self.turn] -= edged


                game.animate()

        for i in range(self.w):
            for j in range(self.h):
                cur = self.get(i,j)
                if cur.num != -1 and game.move + 1 > cur.lifetime:
                    cur.remove()

        col1 = mute(COLS[game.turn],t=0.6)
        pre = self.turn

        self.turn += 1
        m0 = m = self.move
        if self.turn == self.players:
            self.turn = 0
            m += 1
    
        while self.scores[self.turn] == 0 and self.turn != pre:
            self.turn += 1
            if self.turn == self.players:
                self.turn = 0
                m += 1

        col2 = mute(COLS[game.turn],t=0.6)

        a = time.time()
        dif = 0
        self.waiting = True
        while dif <= 0.2:
            dif = time.time()-a
            t = ease(dif / 0.2)
            self.move = m0 + (m - m0) * t
            events()
            BG = collerp(col1,col2,t)
            screen.fill(BG)
            self.draw()
            pygame.display.flip()
        self.waiting = False
        self.move = m

    def draw(self):        
        for i in range(self.w):
            for j in range(self.h):
                self.get(i,j).draw()

        self.particles = [particle for particle in self.particles if particle.update()]
        for particle in self.particles:
            particle.draw()

        stepx,stepy = font.size("0")
        stepx //= 2
        for i in range(len(self.scores)):
            text = font.render(str(self.scores[i]),1,COLS[i])
            screen.blit(text,(stepx,stepx+i*stepy))

        text = font.render(str(math.floor(self.move)),1,WHITE)
        screen.blit(text,(width-text.get_width()-stepx,stepx))
            
title = header.render("edge.io",1,WHITE)
game = Game()

tempmessage = None
temptimestamp = 0
tempfade = 0.8
templifetime = 1
messages = [fonts[30].render("copied to clipboard!",1,WHITE),
            fonts[30].render("loaded from clipboard!",1,WHITE),
            fonts[30].render("invalid clipboard code!",1,WHITE)]

def send_message(i):
    global tempmessage,temptimestamp,templifetime
    tempmessage = messages[i]
    temptimestamp = time.time()

while 1:
    events()
    if SCENE == "game":
        BG = mute(COLS[game.turn],t=0.6)
        screen.fill(BG)
        game.draw()
    elif SCENE == "menu":
        t = (time.time() % 36) / 6
        i = math.floor(t)
        t -= i
        BG = mute(collerp(COLS[i],COLS[(i+1)%6],t),t=0.6)
        screen.fill(BG)
        screen.blit(title,camera.coord(-title.get_width()//2,-150-title.get_height()//2))
        for button in buttons:
            button.draw()

        for slider in sliders:
            slider.draw()

    if tempmessage:
        t = time.time()
        if t - temptimestamp <= templifetime:
            t = max(0,min(1,(tempfade-t+temptimestamp)/(templifetime-tempfade)+1))
            tempmessage.set_alpha(round(255 * ease(t)))
            screen.blit(tempmessage,(hwidth - tempmessage.get_width()//2, font.size("0")[0]//2))
        else:
            tempmessage = None

    pygame.display.flip()
