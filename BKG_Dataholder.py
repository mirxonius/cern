import numpy as np
import tables as t
import pandas as pd
import datetime
import os
import json

VACUUM_PATH = "/home/mirksonius/Desktop/Vacuum_Data/"

BEAM_PATH = "/home/mirksonius/Desktop/Fill_info/beam/"

FILL_PATH = "/home/mirksonius/Desktop/22_fills/"

VACUUM_VARIABLES = [
    "VGI.183.1L5.X.PR",
    "VGI.183.1R5.X.PR",
    "VGI.220.1L5.X.PR",
    "VGI.220.1R5.X.PR",
    "VGPB.147.5L8.B.PR",
    "VGPB.147.5L8.R.PR",
    "VGPB.183.1L5.X.PR",
    "VGPB.183.1R5.X.PR",
    "VGPB.220.1R5.X.PR",
    "VGPB.220.1L5.X.PR",
    "VGPB.7.4L5.X.PR",
    "VGPB.7.4R5.X.PR"
]

COLLIMATOR_VARIABLES = [        
        ":SET_LD",
        #":SET_LU",
        ":SET_RD",
        #":SET_RU"
        ]

class BKG_dataholder():
    """
    Used for collecting, visualizing, and analisys of
    BCM1F background, collimator position, beam mode, beam energy and
    vacuum data.
    Also stores luminosity data.
    """
    def __init__(self,fill_path:str, fill_number:int,
                collimator_path:str = None,
                vacuum_path:str = None,
                beam_path:str = None)->None:
        """
        Esential arguments are fill_path and fill_number,
        collimator_path, vacuum_path and beam_path can be given to acquire 
        their respective data.
        """
        self.fill_path = fill_path
        self.fill_number = fill_number
        self.file_names = os.listdir(self.fill_path + str(self.fill_number))
        self.collimator_path = collimator_path
        if self.collimator_path is not None:
            self.collimator_variables = [
                        ":SET_LD",
                        #":SET_LU",
                        ":SET_RD",
                        #":SET_RU"
                        ]
            
        self.vacuum_path = vacuum_path
        #NOTE: FINISH VACUUM VARIABLES
        if self.vacuum_path is not None:
            self._vacuum_variables = [
                "VGI.183.1L5.X.PR",
                "VGI.183.1R5.X.PR",
                "VGI.220.1L5.X.PR",
                "VGI.220.1R5.X.PR",
                "VGPB.147.5L8.B.PR",
                "VGPB.147.5L8.R.PR",
                "VGPB.183.1L5.X.PR",
                "VGPB.183.1R5.X.PR",
                "VGPB.220.1R5.X.PR",
                "VGPB.220.1L5.X.PR",
                "VGPB.7.4L5.X.PR",
                "VGPB.7.4R5.X.PR"
            ]
        
        self.beam_path = beam_path
        if self.beam_path is not None:
            self.beam_variables = {
                "energy_b1":"LHC.BCCM.B1.A:BEAM_ENERGY",
                #"ENERGY_B1":"LHC.BCCM.B1.B:BEAM_ENERGY", 
                "energy_b2":"LHC.BCCM.B2.A:BEAM_ENERGY",
                #"LHC.BCCM.B2.B:BEAM_ENERGY",
                "mode":"LHC.CISA.CCR:BEAM_MODE"}
              
                #"""
                #Hardcoded beam mode from timber
                #Might not be correct!!!
                #"""
            self.beam_mode_cypher = {
                    2 : "SETUP",
                    3 : "INJPROB",
                    4: "INJSTUP",
                    5 : "INJPHYS",
                    6 : "PRERAM",
                    7 : "RAMP",
                    8 : "FLATTOP",
                    9 : "SQUEEZE",
                    10 : "ADJUST",
                    11 : "STABLE",
                    14 : "RAMPDOWN",
                    13 : "BEAMDUMP",
                    19 : "CYCLING",
                    21 : "NOBEAM"
                }
                
        
        
        
    @property
    def plusz(self):
        if hasattr(self,"plusz_data"):
            return self.plusz_data
        else:
            print("No data gathered!")
            return -1
        
    
    
    @property
    def minusz(self):
        if hasattr(self,"minusz_data"):
            return self.minusz_data
        else:
            print("No data gathered!")
            return -1
        
    @property
    def lumi(self):
        if hasattr(self,"lumi_data"):
            return self.lumi_data
        else:
            print("No data gathered!")
            return -1
        
    @property
    def times(self):
        if hasattr(self,"times_data"):
            return self.times_data
        else:
            print("No data gathered!")
            return -1
                        
    @property
    def colliding_bunches(self):
        if not hasattr(self,"_colliing_bunches"):
            self._colliding_bunches = self.get_colliding_bunches()
        return self._colliding_bunches

    @property
    def noncolliding1(self):
        if not hasattr(self,"_noncolliding1"):
            self._noncolliding1 = self.get_noncolliding_bunches(1,2)
        return self._noncolliding1
    
    @property
    def noncolliding2(self):
        if not hasattr(self,"_noncolliding2"):
            self._noncolliding2 = self.get_noncolliding_bunches(2,1)
        return self._noncolliding2


    @property
    def vacuum_variables(self):
        return self._vacuum_variables
    
    @vacuum_variables.setter
    def vacuum_variables(self,vars):
        self._vacuum_variables = vars

    def get_fill_data(self):
        """
        NOTE: This method should be run before 
        getting the collimator,vacuum or beam data
        Or the plot_plusz,plot_minusz,plot_lumi methods!
        #################################################
        Initialized attributes:
        self.plusz_data
        self.minusz_data 
        self.lumi_data 
        self.times_data
        Stores data from files into appropreate attributes.
        """
        self.plusz_data = np.empty(0)
        self.minusz_data = np.empty(0)
        self.lumi_data = np.empty(0)
        self.times_data = np.empty(0)
        for i, name in enumerate(self.file_names):
            with t.open_file(self.fill_path + str(self.fill_number) +'/'+ name, 'r') as f:
                print("Opening file {}".format(name))
                if f.root.bcm1fbkg.col("timestampsec").size != 0:
                    t1,t2 = pd.to_datetime(f.root.bcm1fbkg.col("timestampsec")[[0,-1]],unit = 's')
                    print("File {} starts at {} and ends at {}".format(name,t1,t2))
                    self.plusz_data = np.hstack(
                    [self.plusz_data,f.root.bcm1fbkg.col("plusz")]
                    )
                    self.minusz_data = np.hstack(
                    [self.minusz_data,f.root.bcm1fbkg.col("minusz")]
                    )
                    self.lumi_data = np.hstack(
                    [self.lumi_data,f.root.bcm1flumi.col("avg")]
                    )
                    self.times_data = np.hstack(
                    [self.times_data,f.root.bcm1fbkg.col("timestampsec")]
                    )

                    if not hasattr(self,"_colliding_bunches") and f.root.__contains__("beam"):
                        colliding = f.root.beam.col("collidable").nonzero()[1]
                        colliding = np.unique(colliding)  
                        if colliding.size != 0:
                            self._colliding_bunches = colliding

                #NOTE: Dopuni za noncolliding bunches

                else:
                    print("Empty file : {}".format(name))            
    
    def get_colliding_bunches(self):
        for i,name in enumerate(self.file_names):
            with t.open_file(self.fill_path + str(self.fill_number)+'/' + name,'r') as f:
                if f.root.__contains__("beam"):
                    colliding = f.root.beam.col("collidable").nonzero()[1]
                    colliding = np.unique(colliding)
                    if colliding.size != 0:
                        return colliding
        print("No colliding bunches")
        return None
                
    def get_noncolliding_bunches(self,beam, irrelevant_beam):

        for name in self.file_names:
            with t.open_file(self.fill_path + str(self.fill_number) +'/'+ name, 'r') as f:
                if f.root.__contains__("beam"):
                    int1 = f.root.beam.col("bxconfig" + str(beam))
                    int2 = f.root.beam.col("bxconfig" + str(irrelevant_beam))
                    if int1.size == 0 or int2.size == 0:
                        continue
                    
                    int1 = int1[0,:]
                    int2 = int2[0,:]
                    noncol = np.where(
                    np.logical_and(int1 != 0 , int2 == 0)
                    )[0]
                    noncol = np.unique(noncol)
                    if noncol.size != 0:
                        return noncol
        print(f"No noncolliding bunches in beam {beam}!")
        return None
        
    def get_empty_bunches(self):
        for name in self.file_names:
            with t.open_file(self.fill_path + str(self.fill_number) +'/'+ name, 'r') as f:
                if f.root.__contains__("beam"):
                    int1 = f.root.beam.col("bxconfig1")
                    int2 = f.root.beam.col("bxconfig2")
                    if int1.size == 0 or int2.size == 0:
                        continue
                    
                    int1 = int1[0,:]
                    int2 = int2[0,:]
                    empty = np.where(
                    np.logical_and(int1 == 0 , int2 == 0)
                    )[0]
                    empty = np.unique(empty)
                    if empty.size != 0:
                        return empty
        return None



    def get_vacuum_data(self):
        if self.vacuum_path is None:
            print("No vacuum path is given")
            return -1
        vac_data_dict = dict()
        with open(self.vacuum_path+"vacuum_"+str(self.fill_number)+".json",'r') as f:
            vac_data_dict = json.load(f)
        
        self.vac_dict = dict()
        for var in self.vacuum_variables:
            vac_df = pd.DataFrame()
            vac_df["value"] = vac_data_dict[var][1]
            vac_df["timestamp"] = vac_data_dict[var][0]
            vac_df["time"] = pd.to_datetime(vac_df["timestamp"],unit = "s")
            self.vac_dict.update({var:vac_df.copy()})
    
    @property
    def vacuum_data(self):
        return self.vac_dict

    def fill_vacuum(self,vacuum_variables,interpolation_times):
        """
        Vacuum variables usually have smaller time
        resolution than background variables, in order
        to compare them we want the two data sets to have the same
        dimensionality.
        We achieve this by interpolating vacuum variables.
        
        Arguments:
        vacuum_variables: list or vacuum variable to be interpolated
        interpolation_times: array of times at which to interpolate

        Returns:
        filled_vacuum: dict of variable names and interpolated values.

        """
        filled_vacuum = dict()

        if not isinstance(vacuum_variables, list):
            times = self.vac_dict[vacuum_variables]["timestamp"]
            values = self.vac_dict[vacuum_variables]["value"]
            filled_vacuum[vacuum_variables] = np.interp(interpolation_times, times,values)
            return filled_vacuum

        for var in vacuum_variables:
            times = self.vac_dict[var]["timestamp"]
            values = self.vac_dict[var]["value"]
            filled_vacuum[var] = np.interp(interpolation_times, times,values)
        
        return filled_vacuum





    def get_collimator_data(self):
        self.collimators_b1 = []
        self.collimators_b2 = []
        if self.collimator_path is None:
            print("No collimator path is given!")
            return -1
        
        coll_data_dict = dict()
        with open(self.collimator_path + "collimator_data_" + str(self.fill_number)+".json",
                  'r') as f:
            coll_data_dict = json.load(f)

        self.coll_dict = dict()
        collimators = coll_data_dict.keys()
        for collimator in collimators:
            if collimator[-1] == "1":
                self.collimators_b1.append(collimator)
            elif collimator[-1] == "2":
                self.collimators_b2.append(collimator)
            coll_df = pd.DataFrame()
            variable_dict = {}
            for key in coll_data_dict[collimator].keys():
                times,pos = coll_data_dict[collimator][key]
                pos.append(pos[-1])
                times.append(self.fill_end)
                coll_df["position"] = pos.copy()
                coll_df["timestamp"] = times.copy()            
                coll_df["time"] = pd.to_datetime(times.copy(),unit = "s")
                
                variable_dict.update({key:coll_df.copy()})
                self.coll_dict.update({collimator:variable_dict})
        

        
    def get_beam_data(self):
        if self.beam_path is None:
            print("No beam path given!")
            return -1
        
        beam_data_dict = dict()
        with open(self.beam_path + "/beam_data_" + str(self.fill_number) + ".json",
                 "r") as f:
            beam_data_dict = json.load(f)
        
        
    
        self.beam_mode = pd.DataFrame()
        self.energy_b1 = pd.DataFrame()
        self.energy_b2 = pd.DataFrame()
        
        self.fill_start = beam_data_dict["start"]
        self.fill_end = beam_data_dict["stop"]

        times, values = beam_data_dict[self.beam_variables["mode"]]
        self.beam_mode["timestamp"] = times.copy()
        self.beam_mode["time"] = pd.to_datetime(times,unit = "s")
        self.beam_mode["cypher"] = values.copy()
        self.beam_mode["mode"] = [self.beam_mode_cypher[val] for val in values]
        
        times,values = beam_data_dict[self.beam_variables["energy_b1"]]
        self.energy_b1["timestamp"] = times.copy()
        self.energy_b1["time"] = pd.to_datetime(times,unit = "s")
        self.energy_b1["value"] = values.copy()
        
        times,values = beam_data_dict[self.beam_variables["energy_b2"]]
        self.energy_b2["timestamp"] = times.copy()
        self.energy_b2["time"] = pd.to_datetime(times,unit = "s")
        self.energy_b2["value"] = values.copy()
        
    @property
    def fill_end_dt(self):
        if not hasattr(self, "fill_end"):
            self.get_beam_data()
        return datetime.datetime.utcfromtimestamp(self.fill_end)


    @property
    def fill_start_dt(self):
        if not hasattr(self, "fill_start"):
            self.get_beam_data()
        return datetime.datetime.utcfromtimestamp(self.fill_start)






    




