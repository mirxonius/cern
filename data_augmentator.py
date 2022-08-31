from tkinter import N
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

    @property
    def times(self):
        if not hasattr(self, '_times'):
            self._times = self.bkg.times[
                self.bkg.times >= self.bkg.beam_mode["timestamp"].iloc[0]]

        return self._times


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
    def collimator_data(self):
        if not hasattr(self, '_collimator_data'):
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
        
            self._collimator_data = cda.coll_dict

        return self._collimator_data


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
    def complete_data(self):
        if not hasattr(self, '_complete_data'):
            data = {
                "timestamp":self.times,
                "lumi":self.lumi,
                "plusz":self.plusz,
                "minusz":self.minusz,
            }
            for var in self.vacuum_data.keys():
                data.update({var:self.vacuum_data[var]})
            
            #NOTE: treba dodati isto za kolimatore

            data.update({"beam_mode_cypher":self.cypher})
            data.update({"beam_mode":self.mode})

            self._complete_data = pd.DataFrame(
                data = data, columns = data.keys())
            
        
        return self._complete_data