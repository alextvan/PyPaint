import socket
import pickle
import threading
import sys
import time
import random
from SerClass import DrawData, UserList, GameEvent
from ParseDictionary import f, find_word

# Create a socket object with IPV4 and TCP connection
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to address and port
server = socket.gethostbyname(socket.gethostname())
server_address = (server, 12345)
server_socket.bind(server_address)
server_socket.listen(2)
print("Waiting for connections:\n")

# Create a list to store client connections
clients = []

# Create a list for the threads connected
threads = []

# Number of users actually accepted
user_accepted_count = 0

# Key = player number, Value = [player name, score]
users_accepted = {}
players_turn = []

# Event system handling variables:
curr_drawer = 0 # Current Drawer

# Max number of rounds and the current round number
round_number_max = 3
round_number = 0

# Game progress and intermission progress boolean flags
game_prog = False
inter_prog = False
valid_players = 2 # Minimum number of players needed for the game to start

word_to_guess = "" # The current word to guess

# Durations of certain events
intermission_duration = 10
round_duration = 75
server_time = 0
stop_countdown_flag = False # This allows for the counter to abruptly stop
countdown_thread = None # Global countdown thread object

# Game state abbreviation
game_state = "ne"

def reset_scores():
    """
    This function resets the scores of all valid users
    """
    global users_accepted
    for k in users_accepted:
        users_accepted[k][1] = 0

def determine_winner():
    """
    This function determines the winner of all valid users
    """
    global users_accepted
    max_value = -1
    max_key = -1

    for key in users_accepted:
        if users_accepted[key][1] > max_value:
            max_value = users_accepted[key][1]
            max_key = key
    return users_accepted[max_key][0]

def countdown(duration):
    """
    This function performs a countdown server-sided and transmits data to all clients. Once the timer done, depending on the state of the game, this function performs differently.

    @param duration: The number of seconds to countdown
    """
    global inter_prog, game_prog, server_time, round_number, curr_drawer, game_state, stop_countdown_flag, word_to_guess

    timer_value = duration
    countdown_start_time = time.time()

    rand_ind = random.randint(1,400)
    word_to_guess = find_word(rand_ind)
    
    # While the timer is greater than 0, send data + countdown
    while timer_value > 0:
        elapsed_time = time.time() - countdown_start_time
        timer_value = max(duration - int(elapsed_time), 0)
        server_time = timer_value

        if user_accepted_count < valid_players or stop_countdown_flag:
            timer_value = 0
            server_time = 0
        
        send_to_all_c({"t": server_time})

        time.sleep(1)

    # Once the timer reaches 0
    if timer_value <= 0:
        # In the case that the intermission just finished
        if inter_prog == True:
            game_state = "d"
            
            round_number += 1
            curr_drawer += 1

            inter_prog = False
            game_prog = True

            print(f"current drawer: {curr_drawer} in round number {round_number}")

            game_data = GameEvent(curr_drawer,round_number, game_prog, inter_prog, True)
            send_to_all_c(game_data)
            send_to_all_c({"g":game_state, "w": word_to_guess})
            
        # In the case that the game is still in progress 
        elif game_prog == True:
            
            # increment the current drawer by 1 in the case that we dont have an abrupt stop
            if stop_countdown_flag == False:
                curr_drawer += 1
            else:
                stop_countdown_flag = False

            # If we exceed, then we have to start a new round
            if curr_drawer > user_accepted_count:
                round_number += 1
                curr_drawer = 1
                
            # The same case that the round number is still less than or equal to the maximum number of rounds
            if round_number <= round_number_max:
                inter_prog = False
                game_state = "d"
                send_to_all_c({"g":game_state})
                
                # In the case that we reach intermission round, reset everything
            else: 
                # Flags
                inter_prog = True
                game_prog = False

                # Make the current drawer and round number 0, change the game_state var to "i" (intermission)
                curr_drawer = 0
                round_number = 0
                game_state = "i"

                # Determine the winner then reset the scores
                winner_data = determine_winner()
                reset_scores()

                # Send respective data
                send_to_all_c({"g":game_state, "wi": winner_data})
                user_list_data = UserList(user_accepted_count, users_accepted, None, None)
                send_to_all_c(user_list_data)
            
            print(f"current drawer: {curr_drawer} in round number {round_number}")
            game_data = GameEvent(curr_drawer,round_number, game_prog, inter_prog, True)
            send_to_all_c(game_data)

            # Finally, send the word we have randomized. If it is intermission then there is no word.
            if game_prog:
                send_to_all_c({"w": word_to_guess})

def start_countdown(duration):
    """
    This function starts a thread for the countdown function. This is because the countdown function must run in parallel with receiving and giving data, otherwise nothing will be able to received.

    @param duration: The number of seconds to countdown
    """
    global countdown_thread

    # Start a new thread for the countdown, target is function countdown.
    print("Countdown started.")
    countdown_thread = threading.Thread(target=countdown, args=(duration,))
    countdown_thread.start()
        
def send_to_all_c(data):
    """
    Allows for sending data param to all clients

    @param data: Any data to be pickled and sent
    """
    global clients
    for c in clients:
        try:
            c.sendall(pickle.dumps(data))
        except socket.error:
            clients.remove(c)
            c.close()

def send_to_all_except_one(data, cl_exclude):
    """
    Allows for sending data param to all but one client

    @param data: Any data to be pickled and sent
    @param cl_exclude: the client to be excluded being sent data
    """
    global clients
    for c in clients:
        if c != cl_exclude:
            try:
                c.sendall(pickle.dumps(data))
            except socket.error:
                clients.remove(c)
                c.close()

def handle_client(client_socket):
    """
    Allows for receiving messages and data via a client. 

    @param client_socket: the socket of the player that is receiving the data
    """
    global user_accepted_count, users_accepted, score_board, time, curr_drawer, game_prog, round_prog, inter_prog, server_time, round_number, game_state, intermission_duration, round_duration, stop_countdown_flag, word_to_guess, clients

    try:
        while True:
            # Receive data from the client
            data = client_socket.recv(4096)

            # No data/Null data
            if not data:
                break

            received_data = pickle.loads(data)

            # In the case that the data given is some sort of drawing data
            if isinstance(received_data, DrawData):
                send_to_all_except_one(received_data, client_socket)

            elif isinstance(received_data, UserList):
                
                print("list:", received_data.dict_users, "\nnumber of users: ", received_data.num_users)

                # Instantiate server variables that need to be updated
                user_accepted_count = received_data.num_users
                users_accepted = received_data.dict_users

                send_to_all_except_one(received_data, client_socket)

                # In the case that there are enough players to start a game
                if user_accepted_count >= valid_players and game_prog == False and inter_prog == False and received_data.user_left == None and received_data.upd_score == False:
                    
                    inter_prog = True
                    game_state = "i"
                    message = {"g": game_state}
                    send_to_all_c(message)
                    start_countdown(intermission_duration)
                    
                # In the case that a user leaves mid-round or mid-game and there are not enough players
                elif user_accepted_count < valid_players and received_data.user_left and (game_prog == True or inter_prog == True) and received_data.upd_score == False: 
                    print("reset")
                    # In the case that there are not enough players, we want to reset the game.
                    # Set game state to NE
                    # Set server time to 0 (already done in countdown)
                    game_state = "ne"
                    send_to_all_except_one({"g": game_state}, client_socket)

                    # Set all Player scores to 0
                    reset_scores()
                    user_list_data = UserList(user_accepted_count, users_accepted, None, None)
                    send_to_all_except_one(user_list_data, client_socket)
                    # Make no one the drawrer
                    curr_drawer = 0
                    # Reset the rounds
                    round_number = 0
                    
                    # Turn both intermission and game progression to False
                    inter_prog = False
                    game_prog = False
                
                # In the case that someone leaves
                elif received_data.user_left and game_prog and inter_prog == False:
                    if received_data.user_left == curr_drawer:
                        stop_countdown_flag = True
                    elif received_data.user_left < curr_drawer:
                        curr_drawer += 1
                        data_send = GameEvent(curr_drawer, round_number, game_prog, inter_prog, False)
                        send_to_all_except_one(data_send, client_socket)
                        send_to_all_except_one({"w": word_to_guess}, client_socket)

            elif isinstance(received_data, GameEvent):
                
                curr_drawer = received_data.curr_drawer
                round_number = received_data.curr_round
                game_prog = received_data.game_prog
                inter_prog = received_data.inter_prog

                if round_number <= round_number_max and game_prog and inter_prog == False:
                    inter_prog = False
                    game_prog = True
                    start_countdown(round_duration)
                else:
                    inter_prog = True
                    game_prog = False
                    start_countdown(intermission_duration)
            else:
                if "c" in received_data:
                    send_to_all_except_one(received_data, client_socket)
            
            

    except Exception as e:
        pass
        
    finally:
        print(f"Disconnection from {client_address}")
        if client_socket in clients:
            clients.remove(client_socket)
        client_socket.close()
        sys.exit()

try:
    while True:
        # Accept a connection
        client_socket, client_address = server_socket.accept()
        print(f"Connection from {client_address}")

        # Add the new client to the list
        clients.append(client_socket)
        
        # Start a new thread to handle the client
        client_thread = threading.Thread(target=handle_client, args=(client_socket,))
        threads.append(client_thread)
        client_thread.start()

        # Send the following data: 
        user_list_data = UserList(user_accepted_count, users_accepted, None, None)
        client_socket.sendall(pickle.dumps(user_list_data))
        
        game_data = GameEvent(curr_drawer, round_number, game_prog, inter_prog, False)
        client_socket.sendall(pickle.dumps(game_data))
        client_socket.sendall(pickle.dumps({"t": server_time, "w": word_to_guess}))


except Exception as e :
    print("Exception Thrown " + str(e))
    server_socket.close()
finally:
    # Code for when the server closes:
    # Close the file
    f.close()

    # Close all client connections
    for client_socket in clients:
        client_socket.close()
    
    # Close/join any threads necessary
    for t in threads:
        t.join()

    # Close/join countdown thread if alive
    if countdown_thread and countdown_thread.is_alive():
        countdown_thread.join()

    # Close the server socket
    server_socket.close()                