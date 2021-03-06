import ConfigParser
from pymclevel import schematic, materials
from entity import TileEntity
import nbt
import logging
import re
import os
from random import randint

log = logging.getLogger(__name__)

'''
class BO3:
    
    def __init__(self,filename=''):
        self._lines = []
        self._X_tracker = [0,0,0]
        self._Y_tracker = [0,0,0]
        self._Z_tracker = [0,0,0]
        self.block_data = []
        if filename != '':
            fp = open(filename)
            for line in fp.readlines():
                if line.startswith("Block("):
                    self._lines.append(line)
            fp.close()
            for block in self._lines:
                data = block.replace("Block(", "").replace(")","").strip().split(",")
                x = int(data[0])
                y = int(data[1])
                z = int(data[2])
                if "." in data[3]:
                    b_id = 0
                    value = data[3].split(".")[1]
                    for p_id, name in materials.block_map.items():
                        t_id = str(data[3].split(".")[0])
                        if name.replace("minecraft:", "") == t_id.lower():
                            b_id = p_id
                else:
                    b_id = 0
                    for p_id, name in materials.block_map.items():
                        t_id = str(data[3].split(":")[0])
                        if name.replace("minecraft:", "") == t_id.lower():
                            b_id = p_id
                    value = 0
                    
                if x < self._X_tracker[0]:
                    self._X_tracker[0] = x
                if x > self._X_tracker[1]:
                    self._X_tracker[1] = x
                
                if y < self._Y_tracker[0]:
                    self._Y_tracker[0] = y
                if y > self._Y_tracker[1]:
                    self._Y_tracker[1] = y
                    
                if z < self._Z_tracker[0]:
                    self._Z_tracker[0] = z
                if z > self._Z_tracker[1]:
                    self._Z_tracker[1] = z
                    
                self.block_data.append((x,y,z,b_id,value))
                
            if self._X_tracker[0] < 0:
                self._X_tracker[2] = abs(self._X_tracker[0])
                self._X_tracker[1] += abs(self._X_tracker[0])
                
            if self._Y_tracker[0] < 0:
                self._Y_tracker[2] = abs(self._Y_tracker[0])
                self._Y_tracker[1] += abs(self._Y_tracker[0])
                    
            if self._Z_tracker[0] < 0:
                self._Z_tracker[2] = abs(self._Z_tracker[0])
                self._Z_tracker[1] += abs(self._Z_tracker[0])
                   
            print "==== Vertical ===="
            print "Lowest: "+str(self._Y_tracker[0])
            print "Highest: "+str(self._Y_tracker[1])
            print "Shift: "+str(self._Y_tracker[2])
            print "==== Horizontal X ===="
            print "Lowest: "+str(self._X_tracker[0])
            print "Highest: "+str(self._X_tracker[1])
            print "Shift: "+str(self._X_tracker[2])
            print "==== Horizontal Z ===="
            print "Lowest: "+str(self._Z_tracker[0])
            print "Highest: "+str(self._Z_tracker[1])
            print "Shift: "+str(self._Z_tracker[2])
            
            self.__schem = schematic.MCSchematic(shape=(self._X_tracker[1]+1, self._Y_tracker[1]+1, self._Z_tracker[1]+1))
            print self.__schem.size
            for x, y, z, block, data in self.block_data:
                x += self._X_tracker[2]
                y += self._Y_tracker[2]
                z += self._Z_tracker[2]
                self.__schem.Blocks[x,y,z] = int(block)
                self.__schem.Data[x,y,z] = int(data)
            
    def getSchematic(self):
        return self.__schem
'''
# find athoer way for this.
# keys are block ids in uppercase, values are tuples for ranges, lists for exact states
corrected_states = {'CHEST':(2,6)}

class BO3:
    def __init__(self, filename=''):
        if type(filename) in (str, unicode):
            self.delta_x, self.delta_y, self.delta_z = 0, 0, 0
            self.size_x, self.size_y, self.size_z = 0, 0, 0
            map_block = {}
            not_found = []
            tileentities_list = [a.lower() for a in TileEntity.baseStructures.keys()]
            for k, v in materials.block_map.items():
                map_block[v.replace('minecraft:', '')] = k

            def get_delta(x, y, z):
                if x < 0 and abs(x) > self.delta_x:
                    self.delta_x = abs(x)
                if y < 0 and abs(y) > self.delta_y:
                    self.delta_y = abs(y)
                if z < 0 and abs(z) > self.delta_z:
                    self.delta_z = abs(z)
                if x + self.delta_x >= self.size_x:
                    self.size_x = x + self.delta_x + 1
                if y + self.delta_y >= self.size_y:
                    self.size_y = y + self.delta_y + 1
                if z + self.delta_z >= self.size_z:
                    self.size_z = z + self.delta_z + 1

            raw_data = open(filename).read()
            lines = re.findall(r'^Block\(.*?\)|^RandomBlock\(.*?\)', raw_data, re.M)
            [get_delta(*b) for b in [eval(','.join(a.split('(')[1].split(')')[0].split(',', 3)[:3])) for a in lines]]
            self.__schem = schematic.MCSchematic(shape=(self.size_x, self.size_y, self.size_z))

            def get_block_data(args):
                x, y, z = args[:3]
                b = args[3]
                nbt_data = None
                if len(args) == 5 and args[4] != None:
                    f_name = os.path.join(os.path.dirname(filename), os.path.normpath(args[4]))
                    if os.path.exists(f_name):
                        nbt_data = nbt.load(f_name)
                    else:
                        print 'Could not find %s'%args[4]
                        print '  Canonical path: %s'%f_name
                x = int(x) + self.delta_x
                y = int(y) + self.delta_y
                z = int(z) + self.delta_z
                b_id, b_state = (b + ':0').split(':')[:2]
                if b_state:
                    b_state = int(b_state)
                else:
                    b_state = 0
                return x, y, z, b_id, b_state, nbt_data

            def get_randomblock_data(args):
                x, y, z = args[:3]
                obj = []
                bit_id = False
                bit_path = False
                bit_chance = False
                for arg in args[3:]:
                    if not bit_id:
                        obj.append(arg)
                        bit_id = True
                    elif arg.isdigit():
                        if not bit_path:
                            obj.append(None)
                            bit_path = True
                        obj.append(int(arg))
                        bit_chance = True
                    else:
                        obj.append(arg)
                        bit_path = True
                    if bit_id and bit_path and bit_chance:
                        if randint(1, 100) <= obj[2]:
                            break
                        obj = []
                        bit_id, bit_path, bit_chance = False, False, False
                #print 'Selected random object: %s'%obj
                return get_block_data((x, y, z, obj[0], obj[1]))

            def verify_state(id, state):
                states = corrected_states.get(id, None)
                if states:
                    if type(states) == tuple:
                        if state not in range(*states):
                            state = states[0]
                    elif type(states) == list:
                        if state not in states:
                            state = states[0]
                return state

            for line in lines:
                if line.startswith('Block') or line.startswith('RandomBlock'):
                    if line.startswith('Block'):
                        x, y, z, b_id, b_state, nbt_data = get_block_data(line.replace("Block(", "").replace(")","").strip().split(","))
                    else:
                        x, y, z, b_id, b_state, nbt_data = get_randomblock_data(line.replace("RandomBlock(", "").replace(")","").strip().split(","))

                    if map_block.get(b_id.lower(), None) != None:
                        b_idn = int(map_block[b_id.lower()])
                        if b_id.lower() in tileentities_list:
                            if nbt_data == None:
                                nbt_data = nbt.TAG_Compound()
                                nbt_data.add(nbt.TAG_String(name='id', value=b_id.capitalize()))
                            nbt_data.add(nbt.TAG_Int(name='x', value=x))
                            nbt_data.add(nbt.TAG_Int(name='y', value=y))
                            nbt_data.add(nbt.TAG_Int(name='z', value=z))
                            self.__schem.TileEntities.append(nbt_data)
                        self.__schem.Blocks[x, z, y] = b_idn
                        self.__schem.Data[x, z, y] = verify_state(b_id, b_state)
                    else:
                        print 'BO3 Block not found: %s'%b_id

        else:
            log.error('Wrong type for \'filename\': got %s'%type(filename))

    def getSchematic(self):
        return self.__schem


class BO2:
    _parser = ConfigParser.RawConfigParser()
    
    def __init__(self, filename=''):
        self.__meta = {}
        self.__blocks = {}
        # [0] is lowest point, [1] is highest point, [2] is the amount to shift by
        self._vertical_tracker = [0,0,0]
        self._horizontal_tracker_1 = [0,0,0]
        self._horizontal_tracker_2 = [0,0,0]
        if filename != '':
            self._parser.read(filename)
            self.__version = self._parser.get('META', 'version')
            for item in self._parser.items("META"):
                self.__meta[item[0]] = item[1]
                
            for block in self._parser.items("DATA"):
                
                if int(block[0].split(",")[2]) < self._vertical_tracker[0]:
                    self._vertical_tracker[0] = int(block[0].split(",")[2])
                if int(block[0].split(",")[2]) > self._vertical_tracker[1]:
                    self._vertical_tracker[1] = int(block[0].split(",")[2])
                    
                    
                if int(block[0].split(",")[0]) < self._horizontal_tracker_1[0]:
                    self._horizontal_tracker_1[0] = int(block[0].split(",")[0])
                if int(block[0].split(",")[0]) > self._horizontal_tracker_1[1]:
                    self._horizontal_tracker_1[1] = int(block[0].split(",")[0])
                    
                    
                if int(block[0].split(",")[1]) < self._horizontal_tracker_2[0]:
                    self._horizontal_tracker_2[0] = int(block[0].split(",")[1])
                if int(block[0].split(",")[1]) > self._horizontal_tracker_2[1]:
                    self._horizontal_tracker_2[1] = int(block[0].split(",")[1])
                    
            if self._vertical_tracker[0] < 0:
                self._vertical_tracker[2] = abs(self._vertical_tracker[0])
                self._vertical_tracker[1] += abs(self._vertical_tracker[0])
                
            if self._horizontal_tracker_1[0] < 0:
                self._horizontal_tracker_1[2] = abs(self._horizontal_tracker_1[0])
                self._horizontal_tracker_1[1] += abs(self._horizontal_tracker_1[0])
                
            if self._horizontal_tracker_2[0] < 0:
                self._horizontal_tracker_2[2] = abs(self._horizontal_tracker_2[0])
                self._horizontal_tracker_2[1] += abs(self._horizontal_tracker_2[0])
                
            self.__schem = schematic.MCSchematic(shape=(self._horizontal_tracker_2[1]+1, self._vertical_tracker[1]+1, self._horizontal_tracker_1[1]+1))
            for block in self._parser.items("DATA"):
                coords = block[0].split(",")
                x = int(coords[1])+self._horizontal_tracker_2[2]
                y = int(coords[0])+self._horizontal_tracker_1[2]
                z = int(coords[2])+self._vertical_tracker[2]
                self.__schem.Blocks[x,y,z] = block[1]
            
    def getSchematic(self):
        return self.__schem
    
    @property
    def meta(self):
        return self.__meta
    
    @property
    def blocks(self):
        return self.__blocks