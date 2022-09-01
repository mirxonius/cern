import numpy as np
import tables as t
import pandas as pd
import datetime
import os
import json

from BKG_Dataholder import BKG_dataholder
from Coll_Data_Aug import Coll_Data_Augmentator


class Data_Augmentator():
    """
    Should recieve background data,
    filled vacuum data, filled collimator data
    and the corresponding beam mode data
    in the form of a bakground dataholder
    """

    def __init__(self,bkg_dh:BKG_dataholder = None,vac_vars = None):
        self.bkg = bkg_dh
        if vac_vars is not None:
            self.vacuum_variables = vac_vars
        else:
            self.vacuum_variables = self.bkg.vacuum_variables   
    
        self.all_data

    @property
    def times(self):
        if not hasattr(self, '_times'):
            self._times = self.bkg.times[
                self.bkg.times >= self.bkg.beam_mode["timestamp"].iloc[0]]

        return self._times

    @property
    def times_lumi(self): 
        if not hasattr(self, "_times_lumi"):
            self._times_lumi = self.bkg.times_lumi[
                self.bkg.times_lumi >= self.bkg.beam_mode["timestamp"].iloc[0]]
            
        return self._times_lumi

    @property
    def cypher(self):
        if not hasattr(self, "_cypher"):
            self._cypher = np.zeros(self.times.shape)
            N = len(self.bkg.beam_mode["timestamp"])
            for i in range(0, N):
                t = self.bkg.beam_mode["timestamp"].iloc[i]
                idx = self.times >= t
                self._cypher[idx] = self.bkg.beam_mode["cypher"].iloc[i]
                
        return self._cypher

    @property
    def mode(self):
        if not hasattr(self, "_mode"):
            bmc = self.bkg.beam_mode_cypher
            self._mode = []
            for c in self.cypher:
                self._mode.append(bmc[c])

            self._mode = np.array(self._mode)

        return self._mode


    @property
    def plusz(self):
        if not hasattr(self, "_plusz"):
            idx = np.argwhere(self.bkg.times >= self.bkg.beam_mode["timestamp"].iloc[0]
            )[0,0]

            self._plusz = self.bkg.plusz[idx:]
        return self._plusz



    @property
    def minusz(self):
        if not hasattr(self, "_minusz"):
            idx = np.argwhere(self.bkg.times >= self.bkg.beam_mode["timestamp"].iloc[0]
            )[0,0]
            self._minusz = self.bkg.minusz[idx:]
        return self._minusz
    


    @property
    def lumi(self):
        if not hasattr(self, "_lumi"):
            idx = np.argwhere(
                self.bkg.times >= self.bkg.beam_mode["timestamp"].iloc[0]
                )[0,0]
            
            self._lumi = self.bkg.lumi[idx:]
        return self._lumi
        

    @property
    def vacuum_data(self):
        if not hasattr(self, "_vacuum_data"):
            self._vacuum_data = self.bkg.fill_vacuum(self.vacuum_variables,self.times)
        return self._vacuum_data

    @property
    def vacuum_variables(self):
        return self._vacuum_variables
    
    @vacuum_variables.setter
    def vacuum_variables(self,vars):
        self._vacuum_variables = vars

    @property
    def collimator_dataholder(self):
        if not hasattr(self, '_collimators'):
            BEFORE_IP = [
            "TCTPH.4L5.B1",
            "TCTPH.4R5.B2",
            "TCTPV.4L5.B1",
            "TCTPV.4R5.B2"
            ]

            cda = Coll_Data_Augmentator(
                            coll_dict =self.bkg.coll_dict,
                            before_ip = BEFORE_IP,
                            beam_1 = self.bkg.collimators_b1, 
                            beam_2 = self.bkg.collimators_b2,
                            times =self.times,
                            variables = self.bkg.collimator_variables)
            cda.extend_data(self.times)
        
            self._collimator_dataholder = cda

        return self._collimator_dataholder

    @property
    def coll_dict(self):
        return self.collimator_dataholder.coll_dict
    
    @property
    def collimators(self):
        return self.collimator_dataholder.colls
    
    @property
    def collimator_variables(self):
        return self.collimator_dataholder.variables

    @property
    def beam1_collimators(self):
        return self.collimator_dataholder.beam1

    @property
    def beam2_collimators(self):
        return self.collimator_dataholder.beam2
    @property
    def vertical_collimators(self):
        return self.collimator_dataholder.vertical
    @property
    def horizontal_collimators(self):
        return self.collimator_dataholder.horizontal
    @property
    def scrapers(self):
        return self.collimator_dataholder.scrapers
    



    @property
    def fill_number(self):
        return self.bkg.fill_number

    @property
    def energy_b1(self):
        return self.bkg.energy_b1

    @property
    def energy_b2(self):
        return self.bkg.energy_b2

    @property
    def beam_mode(self):
        return self.bkg.beam_mode

    @property
    def all_data(self):
        if not hasattr(self, '_all_data'):
            if not np.array_equal(self.times,self.lumi):
                self.align_data()

            data = {
                "timestamp":self.times,
                "lumi":self.lumi,
                "plusz":self.plusz,
                "minusz":self.minusz,
            }
            for var in self.vacuum_data.keys():
                data.update({var:self.vacuum_data[var]})
            
            for col in self.collimators:
                for var in self.collimator_variables:
                    data.update({
                        col + var:self.coll_dict[col][col + var]["position"].values
                    })

            data.update({"beam_mode_cypher":self.cypher})
            data.update({"beam_mode":self.mode})

            self._all_data = pd.DataFrame(
                data = data, columns = data.keys())
            
        
        return self._all_data

    @property
    def bacground_df(self):
        return self.all_data[
            ["timestamp","beam_mode","lumi","plusz","minusz"]
            ]

    @property
    def collimator_df(self):
        collims = ["timestamp","beam_mode"]
        for col in self.collimators:
            for var in self.collimator_variables:
                collims.append(
                    col + var
                )
        return self.all_data[collims]

    @property
    def vacuum_df(self):
        vacs = ["timestamp","beam_mode"]
        vacs = vacs + self.vacuum_variables
        return self.all_data[vacs]

    def align_data(self):
        """
        Somtimes it is the case that
        lumi data and background data are not
        recorded at the same intants.
        This function find the timestamps that
        are the same for both lumi and background data.
        """
        idx_bkg = []
        idx_lumi = []
        N = len(self.times_lumi)
        Nbkg = len(self.times)
        last_found = 0
        for i,tmp in enumerate(self.times):
            for j in range(last_found,N):
                if tmp == self.times_lumi[j]:
                    idx_bkg.append(i)
                    idx_lumi.append(j)
                    last_found = j
                    break
                    
        print("Background points removed: {}\nPrecetnage removed: {}%".format(
            Nbkg- len(idx_bkg), 100*(1-len(idx_bkg)/Nbkg)
        ))

        print("Luminosity points removed: {}\nPrecetnage removed: {}%".format(
            N- len(idx_lumi), 100*(1-len(idx_lumi)/N)
        ))

        self._plusz = self.plusz[idx_bkg]
        self._minusz = self.minusz[idx_bkg]
        self._mode = self.mode[idx_bkg]
        self._cypher = self.cypher[idx_bkg]
        self._times = self.times[idx_bkg]

        self._lumi = self.lumi[idx_lumi]
        self._times_lumi = self.times_lumi[idx_lumi]
