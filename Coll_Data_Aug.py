import numpy as np
import pandas as pd



COLLIMATOR_VARIABLES = [        
        ":SET_LD",
        #":SET_LU",
        ":SET_RD",
        #":SET_RU"
        ]


class Coll_Data_Augmentator():

    def __init__(self,coll_dict:dict,before_ip:list,
    beam_1:list,beam_2:list,variables:list = COLLIMATOR_VARIABLES,times = None):
        self.coll_dict = coll_dict
        self.colls = list(self.coll_dict.keys())
        self.beam1 = beam_1
        self.beam2 = beam_2
        self.before_ip = before_ip
        self.variables = variables
        self.beams = {1:self.beam1,2:self.beam2}
        #Hardcoded: NEEDS FIXING!!!
        self.vertical = [ "TCTPV.4L5.B1","TCTPV.4R5.B2"]
        self.horizontal = [ "TCTPH.4L5.B1","TCTPH.4R5.B2",]
        self.scrapers = [
                    'TCL.4R5.B1', 
                    'TCL.5R5.B1',
                    'TCL.6R5.B1', 
                    'TCL.4L5.B2', 
                    'TCL.5L5.B2', 
                    'TCL.6L5.B2'
                        ]

        self.hv_pairs = {1:(self.before_ip[0],self.before_ip[2]),
                         2:(self.before_ip[1],self.before_ip[3])}
    
        self.augmented = {}
        self.extended = False

        if times is not None:
            self.extend_data(times)
        
        

    def extend_data(self,times):
        new_data = {}
        for c in self.coll_dict.keys():
            var_data = {}
            for var in self.variables:
                collimator = self.coll_dict[c]
                t_coll = collimator[c+var]["timestamp"]
                pos = collimator[c+var]["position"]
                var_data.update( {c+var : pd.DataFrame(
                    data = {"timestamp":times,
                            "position": np.interp(times,t_coll,pos)
                            #self.extend_positions(collimator,c+var,times)
                    })})
            new_data.update({c : var_data})
        self.extended = True
        self.coll_dict = new_data


    def area(self,beam:int):
        if self.extended == False:
            print("Data not extended!!")
            return -1
        

        area = []
        h,v =  self.hv_pairs[beam]
        hor = self.coll_dict[h]
        vert = self.coll_dict[v]
        ud_h = list(hor.keys())
        ud_v = list(vert.keys())

        hgap = hor[ud_h[0]]["position"].values - hor[ud_h[1]]["position"].values
        vgap = vert[ud_v[0]]["position"].values - vert[ud_v[1]]["position"].values
        area = hgap*vgap
        return np.array(area)

    def get_unique_positions(self,coll,var):
        return np.unique(
                self.coll_dict[coll][ var]["position"],
                return_index = True
            )
    

    def distribution_over_pos(self,coll,var,bkg,times):
        pos,idx = self.get_unique_positions(coll,var)
        bkg_pos = {}
        for p in pos:        
            ts = self.coll_dict[coll][var].loc[
                self.coll_dict[coll][var]["position"] == p]
            print(ts.index) 
            placeholder = bkg[ts.index]
            bkg_pos[p] = placeholder[np.nonzero(placeholder)]
        return bkg_pos

    def get_vertical(self):
        vert = {v:self.coll_dict[v][v + self.variables[0]] for v in self.vertical}
        return vert

    def get_horizontal(self):
        hor = {h:self.coll_dict[h][h + self.variables[0]] for h in self.horizontal}
        return hor

        
    def get_scrapers(self):
        scr = {s:self.coll_dict[s][s + self.variables[0]] for s in self.scrapers}
        return scr