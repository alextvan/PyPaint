import pygame
import sys
import collections
import threading
import socket
import pickle
import re
from time import sleep
from SerClass import DrawData, UserList, decrement_dict, GameEvent


pygame.init()
pygame.display.set_caption("PyPaint")

WIDTH = 1100
HEIGHT = 600
screen = pygame.display.set_mode((WIDTH,HEIGHT))

clock = pygame.time.Clock()

#Images
pencil_icon = pygame.image.load("Images/PencilIcon.png")
paint_icon = pygame.image.load("Images/PaintIcon.png")
eraser_icon = pygame.image.load("Images/EraserIcon.png")
# fill_icon = pygame.transform.scale(pygame.image.load("Images/FillIcon.png"),(95, 95))
clock_icon = pygame.transform.scale(pygame.image.load("Images/ClockIcon.png"), (85,85))
logo = pygame.image.load("Images/PyPaintLogo.png")
scaled_logo = pygame.transform.scale(logo,(300, 70))
background = pygame.image.load("Images/Background.png")

# Start Icons
pygame.display.set_icon(paint_icon) # Icon Image
# Background images/Icons 
screen.blit(background, (0,0))

y_icon_left = 305

# Canvas Features
CANVASORIGINPOS = [200, 70] # Starts at x = 100, y = 70
CANVASDIMENSIONS = [700, 400] # 600 x 400 canvas
pygame.draw.rect(screen, (255,255,255), (CANVASORIGINPOS[0], CANVASORIGINPOS[1], CANVASDIMENSIONS[0], CANVASDIMENSIONS[1]), 0, 5) # Canvas Rect

# Colorbar (bottom bar) Features
COLORBARPOS = [CANVASORIGINPOS[0], CANVASORIGINPOS[1] + CANVASDIMENSIONS[1] + 20]
COLORBARDIMENSIONS = [CANVASDIMENSIONS[0], 90]

pygame.draw.rect(screen, (255,255,255), (COLORBARPOS[0], COLORBARPOS[1], COLORBARDIMENSIONS[0], COLORBARDIMENSIONS[1]), 0, 5)

YBARCENTER = COLORBARDIMENSIONS[1]//2 + COLORBARPOS[1]

canvas_boundh = CANVASORIGINPOS[0] + CANVASDIMENSIONS[0]
canvas_boundv = CANVASORIGINPOS[1] + CANVASDIMENSIONS[1]

bar_bound_x = COLORBARPOS[0] + COLORBARDIMENSIONS[0]
bar_bound_y = COLORBARPOS[1] + COLORBARDIMENSIONS[1]

# FLAGS FOR TOOLS AND BUTTONS
# disable/enable drawing inside the canvas
draw_flag = False

# flags for pencil/drawing button
draw_button_flag, draw_enable = False, False

eraser_button_flag, eraser_enable = False, False

# Default brush size circle has radius 4, 
# Default brush size line has default width 7
brush_sizeC, brush_sizeL = 4, 7

# COLORS
HIGHLIGHTCOLOR = (230,230,230)
BLACK = (0,0,0)
GREY = (79,79,79)
WHITE = (255,255,255)
RED = (203, 32, 41)
LORANGE = (240, 178, 115)
ORANGE = (255, 119, 26)
YELLOW = (255, 248, 77)
LGREEN = (76, 224, 58)
GREEN = (38, 172, 66)
DBLUE = (55, 69, 229)
DDBLUE = (26,22,99)
PINK = (229, 55, 159)
PURPLE = (120, 0, 112)
COLORS = [BLACK, GREY, RED, LORANGE, ORANGE, YELLOW, LGREEN, GREEN, DBLUE, DDBLUE, PINK, PURPLE]
brush_color = BLACK

x1 = CANVASORIGINPOS[0] + 150
y1 = YBARCENTER-20
# Circle background for selected brush color
pygame.draw.circle(screen, (200,200,200), (CANVASORIGINPOS[0]+30, YBARCENTER), 20)

# Color Display at the bottom bar
for i,c in enumerate(COLORS):
        pygame.draw.circle(screen, c, (x1, y1), 15)
        x1 += 60

        if i == 5:
            x1 = CANVASORIGINPOS[0] + 230
            y1 += 40

# Username
user_font = pygame.font.SysFont('arial', 20)
user_name_entered = False
user_name = ''
text_x = WIDTH-180
text_y = 5

# User list bar/attributes
list_font = pygame.font.SysFont('arial', 15)
user_count = 0
client_num = 0
client_score = 0
user_list_dict = {}
user_padding = 40
score_font = pygame.font.SysFont('arial', 15, bold = True)

# Game Event Handling:
# Game State string and their meanings:
# ne = not enough players
# i = intermission
# d = drawing round
game_state = "ne"
game_state_text = ""
word_to_guess = "" # The word that will be replaced for clients to guess
word_to_guess_lower = ""
client_chat_text = ""
server_time = 0 # Server time that gets decoded to the client(s)
curr_drawer = 0 # The current drawer of the game
round_num = 0 # The current round number of the game
event_font = pygame.font.SysFont('arial', 18)
reset_screen_flag = False
score_to_drawer = 20 # Score given to drawer when other players guess right
winner_determined = None # Initialized once a winner is determined

disable_chatting = False # Disables chatting for client
chat_log = collections.deque()

# Create a socket object with IPV4 and TCP connection
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to address and port
server = socket.gethostbyname(socket.gethostname())
server_address = (server, 12345)
client_socket.connect(server_address)

def receive_data(client_socket):
    try:
        while True:
            # Receive data from the server
            data = client_socket.recv(4096)
            if not data:
                break

            # Unpickle the received data
            received_data = pickle.loads(data)

            # Handle game data (update player position)
            handle_game_data(received_data)

    except Exception as e:
        pass
    finally:
        # Close the connection
        print("Disconnected from the server")
        sys.exit()
            
# Function to handle incoming game data from other clients.
def handle_game_data(data):
    global user_count, user_list_dict, game_state, server_time, curr_drawer, round_num, word_to_guess, word_to_guess_lower, disable_chatting, reset_screen_flag, client_num, winner_determined

    # In the case that the data is an instance of the DrawData class. This draws the canvas on other clients from the drawrer    
    if isinstance(data, DrawData):
        pygame.draw.circle(screen, data.brush_color, data.or_pos, data.brush_sizeC)
        pygame.draw.line(screen, data.brush_color, data.or_pos,data.rel_pos, data.brush_sizeL)

        # Handles user list data and number of users in the room
    elif isinstance(data, UserList):
        user_count = data.num_users
        user_list_dict = data.dict_users

        if data.user_left:
            if client_num > data.user_left:
                client_num -= 1
                print("new client num assigned: " + str(client_num))
        # Handles any game event such as drawer transitions, game progress, intermission progress.
    elif isinstance(data, GameEvent):
        curr_drawer = data.curr_drawer
        round_num = data.curr_round
        if data.init_flag == True and client_num == 1:
            data_send = GameEvent(curr_drawer, round_num, data.game_prog, data.inter_prog, True)
            client_socket.sendall(pickle.dumps(data_send))
        
        if data.inter_prog:
            game_state = "i"
        elif data.game_prog:
            game_state = "d"

    # Any other data are explained here: "g" marks the game state, "t" marks the time of timer, "w" marks the word players have to draw or guess, "c" marks the chat logs, "wi" marks the winner is determined
    else:
        if "g" in data:
            game_state = data["g"]
            # Reset screen/Clear screen
            reset_screen_flag = True
            disable_chatting = False
        if "t" in data:
            server_time = data["t"]
        if "w" in data:
            sleep(0.2)
            word_to_guess = data["w"]
            word_to_guess_lower = word_to_guess.lower()
            
            # In the case that the client is not the drawer
            if client_num != curr_drawer:
                mod_word = re.sub("[A-Za-z]"," _", word_to_guess)
                word_to_guess = mod_word
        if "c" in data:
            chat_log.appendleft(data["c"]) # Append any chat information
        if "wi" in data:
            winner_determined = data["wi"] # Initialize winner data
            
def toolFunc():
    global brush_color
    
    if draw_flag:

        # Cumulative relative mouse position
        relX = mx+umx
        relY = my+umy

        # Check that all positions (cumualtive and non-cumulative) are within the canvas
        inBounds = mx > CANVASORIGINPOS[0] and mx < canvas_boundh and my > CANVASORIGINPOS[1] and my < canvas_boundv and relX > CANVASORIGINPOS[0] and relX < canvas_boundh and relY > CANVASORIGINPOS[1] and relY < canvas_boundv

        if draw_enable and inBounds:
            # Draw circles & lines of a specified color
            pygame.draw.circle(screen, brush_color, (mx,my), brush_sizeC)
            pygame.draw.line(screen, brush_color, (mx,my),(relX, relY), brush_sizeL)

            data_to_send = DrawData(brush_color, (mx,my), (relX, relY), brush_sizeC, brush_sizeL)
            client_socket.sendall(pickle.dumps(data_to_send))

        elif eraser_enable and inBounds:
            # Draw circles & lines of white
            pygame.draw.circle(screen, WHITE, (mx,my), brush_sizeC)
            pygame.draw.line(screen, WHITE, (mx,my),(relX, relY), brush_sizeL)
        
            data_to_send = DrawData(WHITE, (mx,my), (relX, relY), brush_sizeC, brush_sizeL)
            client_socket.sendall(pickle.dumps(data_to_send))

# This function defines the event system that takes place. This keeps track of what gets display on the event bar. 
def event_sys():
    global client_num, game_state, game_state_text, curr_drawer, round_num

    if game_state == "ne":
        game_state_text = "Not Enough Players!"
        curr_drawer = 0
        round_num = 0
    elif game_state == "i":
        if winner_determined != None:
            game_state_text = "Winner is: " + winner_determined
        else:
            game_state_text = "Intermission.."
    else:
        game_state_text = word_to_guess

    pygame.draw.rect(screen, WHITE, (100, 15, 225, 40), 0, 5)
    g = event_font.render(game_state_text, True, BLACK)
    screen.blit(g,(110,26))

def user_list_display():
    global user_list_dict
    for k,v in user_list_dict.items():
            n = v[0]
            s = v[1]

            y_pos = (CANVASORIGINPOS[1]+5) + ((k-1)*user_padding)

            if k == curr_drawer:
                pygame.draw.rect(screen, RED, (12.5, y_pos, 175, 30), 0, 5)
            else: 
                pygame.draw.rect(screen, WHITE, (12.5, y_pos, 175, 30), 0, 5)

            if len(n) > 7:
                list_text = "{num}:{name}..".format(num = k, name = n[:8])
            else:
                list_text = "{num}:{name}".format(num = k, name = n)
            user_text = list_font.render(list_text, True,BLACK)
            screen.blit(user_text ,(13,y_pos+5))

            score_text = score_font.render(str(s), True,BLACK)
            screen.blit(score_text ,(125,y_pos+5))

# Function handles the chat display
def chat_display():
    global chat_log

    # Redrawing the blue background rect
    pygame.draw.rect(screen, (26,22,99), (CANVASORIGINPOS[0]+CANVASDIMENSIONS[0]+10, CANVASORIGINPOS[1], 180, CANVASDIMENSIONS[1]), 0, 5)
    
    y_pos = 450
    pop_bool = False

    # Iterate through the chatlog
    for m in chat_log:
        text_surface = user_font.render(m, True, BLACK)
        text_rect = text_surface.get_rect()
        text_rect.bottomleft = (925, y_pos)

        # In the case that the chat bubble exceeds the chat frame, we want to exit and pop off the chatlog
        if text_rect.y + text_rect.height + 5 <= 120:
            pop_bool = True
            break

        pygame.draw.rect(screen, WHITE, (text_rect.x - 5, text_rect.y - 5, text_rect.width + 10, text_rect.height + 10), 0, 5)

        screen.blit(text_surface, text_rect.topleft)
        y_pos -= text_rect.height + 30

    if pop_bool:
        chat_log.pop()

def update_drawer_color():
    global brush_color
    # Renders the right color for the brush color selected
    pygame.draw.circle(screen, brush_color, (CANVASORIGINPOS[0]+30, YBARCENTER), 15)

    inBounds = mx > COLORBARPOS[0] and mx < bar_bound_x and my > COLORBARPOS[1] and my < bar_bound_y
    if draw_enable and inBounds:
        color = screen.get_at((mx, my))
        if color != WHITE:
            brush_color = color


        


# Start a thread to receive data from the server
receive_thread = threading.Thread(target=receive_data, args=(client_socket,))
receive_thread.start()

try:
    # Update starts here
    while True:
        # Mouse position
        mx, my = pygame.mouse.get_pos()
        umx, umy = pygame.mouse.get_rel()

        # Left Icon Buttons/Tools
        draw_button = pygame.Rect(112.5,y_icon_left+200, 75, 75)
        eraser_button = pygame.Rect(12.5,y_icon_left+200, 75, 75)
        # fill_button = pygame.Rect(12.5,y_icon_left+100, 75, 75) 1

        # Highlight Mechanic for Draw Button
        if draw_enable:
            pygame.draw.rect(screen, HIGHLIGHTCOLOR, draw_button, 0, 5)
        else:
            pygame.draw.rect(screen, WHITE, draw_button, 0, 5)
        
        # Highlight Mechanic for Eraser Button
        if eraser_enable:
            pygame.draw.rect(screen, HIGHLIGHTCOLOR, eraser_button, 0, 5)
        else:
            pygame.draw.rect(screen, WHITE, eraser_button, 0, 5)
        
        # Overlay icon for tools
        screen.blit(pencil_icon, (100.5,490))
        screen.blit(eraser_icon, (0, 490))
        screen.blit(scaled_logo, (WIDTH/2-190,-5))
        screen.blit(clock_icon, (5,-5))
        # Redrawing the blue rect for the input
        pygame.draw.rect(screen, DDBLUE, (CANVASORIGINPOS[0]+CANVASDIMENSIONS[0]+10, CANVASORIGINPOS[1]+CANVASDIMENSIONS[1]+10, 180, 50), 0, 5)

        # UI notifier
        pygame.draw.rect(screen, DDBLUE, (text_x-10, 540, 180, 40), 0, 5)
        g = event_font.render("Hit enter to submit\nusername or chat", True, WHITE)
        screen.blit(g,(text_x+20, 540))
        
        # In the case that the user has entered their name
        if user_name_entered:

            # If the drawer is the client number/this player
            if curr_drawer == client_num:
                # Clicking Mechanic for Draw Button
                if draw_button.collidepoint((mx,my)):
                    if pygame.mouse.get_pressed()[0] == True:
                        draw_button_flag = True
                    else:
                        if draw_button_flag == True:
                            # Any one time button click code goes here
                            draw_enable = not draw_enable
                            draw_button_flag = False

                            #Change other buttons to unhighlight/false
                            eraser_enable = False
                            fill_enable = False

                # Clicking Mechanic for Eraser Button
                elif eraser_button.collidepoint((mx,my)):
                    if pygame.mouse.get_pressed()[0] == True:
                        eraser_button_flag = True
                    else:
                        if eraser_button_flag == True:
                            # Any one time button click code goes here
                            eraser_enable = not eraser_enable
                            eraser_button_flag = False

                            #Change other buttons to unhighlight/false
                            draw_enable = False
                            fill_enable = False
            else:
                # In the case that the client is not the drawer, disable their flags, making them unable to draw.
                draw_enable = False
                eraser_enable = False
                fill_enable = False

            # Chat stuff goes here
            client_chat_text = client_chat_text + "|"

            text_surface = user_font.render(client_chat_text, True, WHITE)

            screen.blit(text_surface, (CANVASORIGINPOS[0]+CANVASDIMENSIONS[0]+20, CANVASORIGINPOS[1]+CANVASDIMENSIONS[1]+10))

            if client_chat_text[-1] == "|":
                client_chat_text = client_chat_text[:-1]

        else:
            draw_enable = False
            eraser_enable = False
            fill_enable = False

        update_drawer_color()

        # Username input
        text_box = pygame.draw.rect(screen, (26,22,99), (text_x,text_y,175,30), 0, 5)

        if user_name_entered == False:
            user_name = user_name + "|"

        text_surface = user_font.render(user_name, True, (255,255,255))

        screen.blit(text_surface, (text_x+5,text_y))

        if user_name[-1] == "|" and user_name_entered == False:
            user_name = user_name[:-1]


        #Player List Bar 
        pygame.draw.rect(screen, DDBLUE, (7.5, CANVASORIGINPOS[1], 185, 320), 0, 5)
        # Player List
        user_list_display()

        # Chat List/Logs
        chat_display()
        
        # Time Text
        time_text = list_font.render(str(server_time), True,BLACK)
        screen.blit(time_text ,(40,35))

        # Method for handling event system
        event_sys()

        # Round display
        round_num_text = "Round " + str(round_num) + "/3"
        pygame.draw.rect(screen, WHITE, (710, 15, 125, 40), 0, 5)
        g = event_font.render(round_num_text, True, BLACK)
        screen.blit(g,(720,26))

        toolFunc()
        
        # In the case that a round has ended or game has ended, reset/redraw the screen
        if reset_screen_flag:
            pygame.draw.rect(screen, (255,255,255), (CANVASORIGINPOS[0], CANVASORIGINPOS[1], CANVASDIMENSIONS[0], CANVASDIMENSIONS[1]), 0, 5)
            reset_screen_flag = False

        # Collect events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # In the case that a user name has been entered
                if user_name_entered:
                    # Delete the user from the list of accepted users
                    del user_list_dict[client_num]
                    user_count -= 1
                    
                    # Decrement the dictionary properly
                    new_dict = decrement_dict(client_num, user_list_dict)
                    print(new_dict)

                    # Send this data to other clients
                    data_send = UserList(user_count, new_dict, client_num, False)
                    client_socket.sendall(pickle.dumps(data_send))

                client_socket.close()
                pygame.quit()
                sys.exit()
                
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    draw_flag = True
            
            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    draw_flag = False
            
            if event.type == pygame.KEYDOWN:

                # In the case that the username has not been entered
                if user_name_entered == False:
                    
                    if event.key == pygame.K_BACKSPACE:
                        user_name = user_name[:-1]

                    elif (event.unicode.isalpha() or event.unicode.isnumeric() or event.key == pygame.K_SPACE) and len(user_name) <= 10:
                        user_name += event.unicode
                    
                    elif event.key == pygame.K_RETURN and len(user_name) != 0 and user_count <= 7:
                        user_name_entered = True
                        user_count += 1
                        client_num = user_count
                        user_list_dict[client_num] = [user_name, 0]

                        print(user_list_dict)
                        data_send = UserList(user_count, user_list_dict, None, False)
                        client_socket.sendall(pickle.dumps(data_send))
                else:
                    
                    if disable_chatting == False and client_num != curr_drawer:
                        if event.key == pygame.K_BACKSPACE:
                            client_chat_text = client_chat_text[:-1]

                        elif (event.unicode.isalpha() or event.unicode.isnumeric() or event.key == pygame.K_SPACE) and len(client_chat_text) <= 20:
                            # Wrap in the case that there are exactly 10 characters
                            if len(client_chat_text) == 17:
                                client_chat_text += "\n"

                            client_chat_text += event.unicode

                        elif event.key == pygame.K_RETURN and client_chat_text.lower() == word_to_guess_lower and game_state == "d":

                            user_list_dict[client_num][1] += server_time
                            user_list_dict[curr_drawer][1] += score_to_drawer
                            disable_chatting = True
                            client_chat_text = ""

                            data_send = UserList(user_count, user_list_dict, None, True)
                            client_socket.sendall(pickle.dumps(data_send))
                        
                        elif event.key == pygame.K_RETURN and len(client_chat_text) != 0:
                            chat_log.appendleft(client_chat_text)
                            client_socket.sendall(pickle.dumps({"c":client_chat_text}))
                            client_chat_text = ""




        pygame.display.update()
        clock.tick(60)

except Exception as e:
    print("Exception Thrown " + str(e))
    client_socket.close()
    sys.exit()