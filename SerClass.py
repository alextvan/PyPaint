#Serializable classes that are able to be transferred via pickle dumping and loading.

# Class for attributes of drawing, communicates the size of brushes, color, etc.
class DrawData:
    def __init__(self, brush_color, or_pos, rel_pos, brush_sizeC, brush_sizeL):
        self.brush_color = brush_color
        self.or_pos = or_pos
        self.rel_pos = rel_pos
        self.brush_sizeC = brush_sizeC
        self.brush_sizeL = brush_sizeL


class UserList:
    def __init__(self, num_users, dict_users, user_left, upd_score):
        self.num_users = num_users
        self.dict_users = dict_users
        self.user_left = user_left
        self.upd_score = upd_score

# Decrements the dictionary when necessary when a player leaves
def decrement_dict(client_num, user_dict):
        pre_dict = {key: value for (key, value) in user_dict.items() if key < client_num}
        post_dict = {key-1: value for (key, value) in user_dict.items() if key > client_num}
        merged = {**pre_dict,**post_dict}
        return merged

class GameEvent:
     def __init__(self,curr_drawer, curr_round, game_prog, inter_prog, init_flag):
          self.curr_drawer = curr_drawer
          self.curr_round = curr_round
          self.game_prog = game_prog
          self.inter_prog = inter_prog
          self.init_flag = init_flag

        
    