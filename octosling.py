import pygame
import sys
import socket
import struct
import math
from sprites import Player
from sprites import Objects
from sprites import Camera
from sprites import GrabObject
import time
from debug import debug

class Game:
    def __init__(self):
        pygame.init()

        pygame.display.set_caption('Octo Sling')

        desktop_info = pygame.display.Info()
        self.SCREEN_WIDTH, self.SCREEN_HEIGHT = desktop_info.current_w, desktop_info.current_h

        self.clock = pygame.time.Clock()
        #self.game_window = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT), pygame.RESIZABLE)
        self.game_window = pygame.display.set_mode((1280, 720))

        self.background_img = pygame.image.load('images/background_water.png').convert()
        self.background_img = pygame.transform.scale(self.background_img, (self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        self.back_rect = self.background_img.get_rect()
        self.back_rect.topleft = (0,0)

        self.objects = Objects(self.SCREEN_WIDTH, self.SCREEN_HEIGHT, self.game_window, self.background_img)
        self.char = Player(self.game_window, self.SCREEN_WIDTH, self.SCREEN_HEIGHT, self.objects.grab_rect, self.objects.grab_mask)
        self.camera = Camera(self.SCREEN_WIDTH, self.SCREEN_HEIGHT, self.char.rect, self.game_window, self.objects, self.char)
        
        self.running = True

        self.fall = False

        self.grab_obj = GrabObject(self.SCREEN_WIDTH, self.SCREEN_HEIGHT, self.game_window, self.camera, self.char, 800)
        self.grab_obj2 = GrabObject(self.SCREEN_WIDTH, self.SCREEN_HEIGHT, self.game_window, self.camera, self.char, 300)
        self.grab_obj3 = GrabObject(self.SCREEN_WIDTH, self.SCREEN_HEIGHT, self.game_window, self.camera, self.char, 1300)

        #self.char2 = Player(self.game_window, self.SCREEN_WIDTH, self.SCREEN_HEIGHT, self.objects.grab_rect, self.objects.grab_mask, 2)

        self.char2 = pygame.image.load('images/luffy.png')
        self.char2_rect = self.char2.get_rect()
        self.rotate_img = pygame.image.load('images/arm_prototype.png')
        self.arm_rect = self.rotate_img.get_rect()
        self.rotate_mask = pygame.mask.from_surface(self.rotate_img)
        self.rotate_mask_img = self.rotate_mask.to_surface(setcolor=(100, 156, 252), unsetcolor=(0, 0, 0, 0))

        self.hook = pygame.image.load('images/hook_sprite.png')
        self.hook = pygame.transform.scale(self.hook, (50,50))
        self.hook_rect = self.hook.get_rect()
        self.hook_rect.y = 300
        self.hook_mask = pygame.mask.from_surface(self.hook)
        self.hook_mask_img = self.hook_mask.to_surface(setcolor=(255, 255, 255), unsetcolor=(0, 0, 0, 0))

        self.store_score = 0
        self.store_high_score = 0
        self.store_cond = False
        self.prev_score = 0

        self.prev_grab_x = 0
        self.cur_grab_x = 0

        self.max_grab_x = 0

        self.dict_store_grab = {}
        self.grab_cond = True

        self.score_inc = False

        self.list_of_crab = [0,0,0]
        self.score_check = False

        #ip = socket.gethostbyname(socket.gethostname())
        self.ip = "10.0.0.28"

        self.player2_posx = 0
        self.player2_posy = 0

        self.grab_coords = [0,0]

        self.arm_pivotx = 0
        self.arm_pivoty = 0

        self.offsetx = 0
        self.offsety = 0

        self.hookx = 800
        self.hooky = 0
        self.world_hooks = []

        self.stop_spawn = False
        self.race_width = self.SCREEN_WIDTH*5

        self.obj_rod = pygame.image.load('images/fish_rod.png')
        self.obj_rod = pygame.transform.scale(self.obj_rod, (50, 500))
        self.rod_rect = self.obj_rod.get_rect()
        self.rod_rect.x = self.hookx+5

        self.finish_line = pygame.image.load('images/finish_line.png')
        self.finish_rect = self.finish_line.get_rect()
        self.complete = False

    def spawnHook(self, curx, cury):
        cur_data = [curx, cury]
        self.world_hooks.append(cur_data)

    def full_recv(self, socket, byte_stream):
        data = b''

        while (len(data) < byte_stream):
            cur_data = socket.recv(byte_stream - len(data))
            data += cur_data
        return data

    def run(self):

        client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_sock.connect((self.ip, 8080))

        client_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

        client_sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1024)
        client_sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024)

        client_num = client_sock.recv(4)
        player_num = struct.unpack("!f", client_num)
        player_num = player_num[0] #use player_num on .move for self.char (could be 1 or 2)

        while self.running:

            mouse_key = pygame.mouse.get_pressed()
            left_key = mouse_key[0]

            mouse_posx, mouse_posy = pygame.mouse.get_pos()

            rect_x = self.char.rect.x
            rect_y = self.char.rect.y

            arm_angle = self.char.angle

            if (self.char.arm_pivot != 0):
                self.arm_pivotx = self.char.arm_pivot[0]
                self.arm_pivoty = self.char.arm_pivot[1]

            arm_inc_num = self.char.inc_scale_arm

            if (self.char.arm_offset != 0):
                self.offsetx = self.char.arm_offset.x
                self.offsety = self.char.arm_offset.y

            client_sock.sendall(struct.pack("!ffBffffffffB", mouse_posx, mouse_posy, int(left_key), rect_x, rect_y, arm_angle, self.arm_pivotx, self.arm_pivoty, arm_inc_num, self.offsetx, self.offsety, int(self.camera.camera_off)))

            server_pkt = self.full_recv(client_sock, 41)
            unpack_server_pkt = struct.unpack("!ffBffffffff", server_pkt)
            
            (player2_mouse_posx, player2_mouse_posy, player2_mouse_bool, player2_locx, player2_locy,
            p2_angle, p2_pivotx, p2_pivoty, p2_inc_num,
            p2_offsetx, p2_offsety) = unpack_server_pkt

            self.char2_rect.x = player2_locx
            self.char2_rect.y = player2_locy

            client_sock.sendall(struct.pack("!f", player2_locx))

            player2_randy = client_sock.recv(4)
            p2_randy = struct.unpack("!f", player2_randy)

            self.char.p2_mouse_key = (bool(player2_mouse_bool),0,0)
            self.char.p2_img_pos[0] = player2_locx
            self.char.p2_img_pos[1] = player2_locy

            self.char.p2_angle = p2_angle
            self.char.p2_pivot = [p2_pivotx, p2_pivoty]
            self.char.p2_inc_scale_arm = p2_inc_num

            p2width = max(1, int(self.rotate_img.get_width()))
            p2height = max(1, self.char.p2_inc_scale_arm)
            scale_arm = pygame.transform.scale(self.rotate_img, (p2width, p2height))

            self.char.p2_offset = pygame.math.Vector2(p2_offsetx, p2_offsety)

            p2_rotate_img, p2_rotate_rect = self.char.rotate(scale_arm, self.char.p2_angle, self.char.p2_pivot, self.char.p2_offset, self.char.p2_mouse_key, self.char.p2_inc_scale_arm)

            self.hooky = p2_randy[0]

            far_playerx = max(self.char.rect.x, self.char.p2_img_pos[0])

            if (far_playerx > self.hookx-600 and self.race_width - self.char.rect.x > 300):
                self.spawnHook(self.hookx, self.hooky)
                self.hookx += 500

            self.game_window.fill((2, 0, 68))

            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN: #ESC to exit
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()

            self.clock.tick(60)

            self.game_window.blit(self.background_img, self.back_rect)

            if (self.char.rect.y > 1100):
                if (self.store_high_score < self.store_score):
                    self.store_high_score = self.store_score
                self.store_score = 0
                self.max_dist = 0
                self.prev_player_rect_x = 0
                self.max_grab_x = 0
                self.dict_store_grab.clear()
                self.fall = True
                self.list_of_crab[0] = 0
                self.list_of_crab[1] = 0
                self.list_of_crab[2] = 0

            if (self.fall == True):

                self.prev_grab_x = 0
                self.cur_grab_x = 0

                self.objects_new = Objects(self.SCREEN_WIDTH, self.SCREEN_HEIGHT, self.game_window, self.background_img)
                self.char_new = Player(self.game_window, self.SCREEN_WIDTH, self.SCREEN_HEIGHT, self.objects_new.grab_rect, self.objects_new.grab_mask)
                self.camera_new = Camera(self.SCREEN_WIDTH, self.SCREEN_HEIGHT, self.char_new.rect, self.game_window, self.objects, self.char_new)

                self.grab_obj_new = GrabObject(self.SCREEN_WIDTH, self.SCREEN_HEIGHT, self.game_window, self.camera_new, self.char_new, 800)
                self.grab_obj2_new = GrabObject(self.SCREEN_WIDTH, self.SCREEN_HEIGHT, self.game_window, self.camera_new, self.char_new, 300)
                self.grab_obj3_new = GrabObject(self.SCREEN_WIDTH, self.SCREEN_HEIGHT, self.game_window, self.camera_new, self.char_new, 1300)

                self.char_new.velocity_y = 0
                self.char_new.grab_velocity.y = 0
                self.char_new.rect.y = self.SCREEN_HEIGHT//2
                self.char_new.img_pos[1] = self.SCREEN_HEIGHT//2
                self.char_new.img_pos[0] = self.SCREEN_WIDTH//2
                self.camera_new.offset = pygame.math.Vector2(0,0)
                self.camera_new.offset.x = self.char_new.rect.centerx - self.SCREEN_WIDTH // 2

                self.char = self.char_new
                self.objects = self.objects_new
                self.grab_obj = self.grab_obj_new
                self.grab_obj2 = self.grab_obj2_new
                self.grab_obj3 = self.grab_obj3_new
                self.camera = self.camera_new
                
                self.fall = False


            elif(self.fall == False):
                
                self.char.move(self.objects.floor_rect, self.objects.left_wall_rect, self.objects.left_wall_mask, self.camera, self.fall, player_num)
                self.objects.update(self.camera, self.char)
                #self.grab_obj.generateObj()
                #self.grab_obj2.generateObj()
                #self.grab_obj3.generateObj(self.hook_rect, self.hook_mask)
                self.camera.object_offset(self.objects, self.char, self.grab_obj, self.fall)
                self.camera.object_offset(self.objects, self.char, self.grab_obj2, self.fall)
                self.camera.object_offset(self.objects, self.char, self.grab_obj3, self.fall)

                if (self.camera.camera_off):
                    self.game_window.blit(self.char2, (self.char2_rect.x-self.camera.cam_offset_prev, self.char2_rect.y))
                else:
                    self.game_window.blit(self.char2, (self.char2_rect.x-self.camera.offset.x, self.char2_rect.y))

                if (self.char.arm_collide and self.store_cond == False):

                    self.prev_grab_x = self.cur_grab_x
                    self.cur_grab_x = self.char.grab_coords[0]

                    if (self.cur_grab_x > self.max_grab_x):
                        self.max_grab_x = self.cur_grab_x

                    for i in range(self.cur_grab_x-40, self.cur_grab_x+40):
                        if i in self.dict_store_grab:
                            self.grab_cond = False

                    if ((abs(self.cur_grab_x - self.prev_grab_x) > 40 and self.prev_grab_x != self.max_grab_x and self.grab_cond) or self.store_score == 0):
                        self.score_inc = False          
                        self.dict_store_grab[self.cur_grab_x] = self.store_score

                    self.store_cond = True
                elif (self.char.arm_collide == False):
                    self.store_cond = False
                    self.grab_cond = True
                

                if ((self.grab_obj3.check_crab_coll or self.grab_obj2.check_crab_coll or self.grab_obj.check_crab_coll) and self.score_inc == False):
                    self.store_score += 1
                    self.score_inc = True
            
            if (self.camera.camera_off):
                self.game_window.blit(p2_rotate_img, (p2_rotate_rect.x-self.camera.cam_offset_prev, p2_rotate_rect.y))
            else:
                self.game_window.blit(p2_rotate_img, (p2_rotate_rect.x-self.camera.offset.x, p2_rotate_rect.y))

            #if (self.char.rotate_mask != 0 and self.char.rotate_rect != 0):
            #    self.char.mask_collision(self.char.rotate_mask, self.hook_mask, self.char.rotate_rect, self.hook_rect, self.camera)

            for coords in self.world_hooks:
                self.hook_rect.x = coords[0]
                self.hook_rect.y = coords[1]

                self.rod_rect.x = coords[0] + 5
                self.rod_rect.y = coords[1] - 492

                if (self.char.rotate_mask != None):
                    self.char.mask_collision(self.char.rotate_mask, self.hook_mask, self.char.rotate_rect, self.hook_rect, self.camera)

                if (self.camera.camera_off):
                    self.game_window.blit(self.hook, (self.hook_rect.x-self.camera.cam_offset_prev, self.hook_rect.y))
                    self.game_window.blit(self.obj_rod, (self.rod_rect.x-self.camera.cam_offset_prev, self.rod_rect.y))
                else:
                    self.game_window.blit(self.hook, (self.hook_rect.x-self.camera.offset.x, self.hook_rect.y))
                    self.game_window.blit(self.obj_rod, (self.rod_rect.x-self.camera.offset.x, self.rod_rect.y))

            if (self.race_width - self.char.rect.x < 600):
                self.finish_rect.x = self.race_width+600
                self.game_window.blit(self.finish_line, (self.finish_rect.x-self.camera.cam_offset_prev, self.finish_rect.y))

            if (self.char.rect.colliderect(self.finish_rect)):
                self.complete = True

            #debug(f"Score: {self.store_score} High Score: {self.store_high_score}", self.game_window)
            #debug([self.camera.camera_off, self.camera.prev_value, self.char.rect.x], self.game_window)
            #debug([self.race_width, self.char.rect.x, self.race_width - self.char.rect.x, self.finish_rect.x, self.complete], self.game_window)

            pygame.display.update()


def main():
    Game().run()
 
if __name__ == "__main__":
    main()