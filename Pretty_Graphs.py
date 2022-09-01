import matplotlib.pyplot as plt
import numpy as np
import datetime
from BKG_Dataholder import BKG_dataholder


#Very useful dictonary for ploting beam modes 
#Will implement an interal dictionary for plotting...
##################################################
#Each beam modes are indicated with numeric values 
# and their colors are chosen arbitrarily
STAGE_COLOR_PALETTE = {
    2 : "firebrick",
    3: "darkgray",
    4: "brown",
    5: "red",   
    6: "yellow",
    7: "darkgreen",
    8 : "orange",
    9 : "mediumpurple",
    10 : "darkgoldenrod",
    11 : "tab:blue",
    13 : "deepskyblue",
    14 : "cornflowerblue",
    19 : "red",
    21 : "black",
}



class Artist():

    def __init__(self,dataholder = None,n_plots = 3) -> None:
        self.dataholder = dataholder
        self.n_plots = n_plots

    @property
    def vac_clrs(self):
        """
        Gets color pallete for vacuum variables
        NOTE: Needs generalization!!
        """
        return ["green","black","mediumorchid","yellow",
                "red","blue","magenta","chocolate"]



    def make_plots(self,path = '',n_plots = None,
    start_plot=None,end_plot=None,
    bkg_logscale = False,bm_legend_outside = False):
        if n_plots is None:
            n_plots = self.n_plots
        else:
            assert n_plots == 2 or n_plots == 3, "Number of plots must be 2 or 3!"
        
        #Making figure
        frame, fig = plt.subplots(n_plots,1,figsize = (16,16))
        
        #Getting start and end times
        if start_plot is None:
            start_plot = np.min(self.dataholder.times)
        else:
            start_plot = start_plot

        if end_plot is None:
            end_plot = np.max(self.dataholder.times)
        else:
            end_plot = end_plot

        #Plotting Instantaneous Luminosity
        fig[0].plot(
            self.dataholder.times_lumi,
            self.dataholder.lumi,
            color = "tab:orange",
            linewidth = 2.5
        )
        #Setting ylabel for Luminosity plot
        fig[0].set_ylabel(r"Instantaneous luminosity [Hz/$\mu$b]",fontsize = 20)
        
        #Creating a twin axis for energy plot
        fig0_twin = fig[0].twinx()
        
        #Plotting energy
        fig0_twin.plot(
            self.dataholder.energy_b1["timestamp"],
            self.dataholder.energy_b1["value"],
            color = "tab:blue"
            )
        
        #Setting energy label
        fig0_twin.set_ylabel("Beam energy [GeV]",fontsize = 20)


        #Shading beam mode regions
        plot_beam_modes(fig[0],self.dataholder.beam_mode,start_plot,end_plot)
        for i in range(1,n_plots):
            plot_beam_modes(fig[i],self.dataholder.beam_mode,start_plot,end_plot,set_labels = False)
        

        #Beam mode legend
        legend_properties = {'weight':'bold',"size":15}
        
        if bm_legend_outside:
            fig[0].legend(bbox_to_anchor = (1.25,0.80),prop = legend_properties,)
        else:
            fig[0].legend(bbox_to_anchor = (0.018,0.80),prop = legend_properties,)
        
        #Center of mass energy
        sqrt_s = (self.dataholder.energy_b1["value"].values.max() + self.dataholder.energy_b2["value"].values.max())/1000
        
        #Setting title
        fig[0].set_title(f"2022, " + r"$\sqrt{s}$" + " = {:.1f} TeV".format(sqrt_s),
         loc = "right",fontsize = 20)


        #SETTING xlims and xticks labels
        t0 = start_plot
        t1 = end_plot
        fig[0].set_xlim(t0,t1)
        ticks = np.linspace(t0,t1,6,endpoint=True,dtype="int")
        lab = get_xlabels(ticks)
        fig[0].set_xticks(ticks)
        fig[0].set_xticklabels(lab,fontsize=20)
        fig[0]

        #SETTING yticks            
        yt_0 = np.linspace(
            self.dataholder.lumi.min(),
            1.1*self.dataholder.lumi.max(),
            4,dtype="int"
        )
        fig[0].set_yticks(yt_0)
        fig[0].set_yticklabels(yt_0,fontsize = 20)
        
        yt_1 = np.linspace(
            self.dataholder.energy_b1["value"].min(),
            1.05*self.dataholder.energy_b1["value"].max(),
            4,dtype="int"
        )
        fig0_twin.set_yticks(yt_1)
        fig0_twin.set_yticklabels(yt_1,fontsize = 20)
        
        #CMS watermark
        plt.text(0.005, 0.9, r"$\bf{CMS}$ $\it{Preliminary}$",fontsize = 20, transform=fig[0].transAxes)

        if bkg_logscale:
            fig[1].set_yscale("log")

        #Plotting Background
        fig[1].plot(
            self.dataholder.times,
            self.dataholder.plusz,
            color = "royalblue",
            label = "Beam 1 Background"
        )
        fig[1].plot(
            self.dataholder.times,
            self.dataholder.minusz,
            color = "firebrick",
            label = "Beam 2 Background"
        )
        #Getting backgound yticks
        #Setting ylabel for background plot
        fig[1].set_ylabel(r"Background [Hz/cm$^2$/10$^{11}$]",fontsize = 20)
        #Setting xticks for background plot
        fig[1].set_xticks(ticks)
        fig[1].set_xticklabels(lab,fontsize = 20)
        fig[1].set_xlim(start_plot,end_plot)
        #Setting yticks for background plot
        bkgmax,bkgmin = self.get_bacground_limits()
        if bkg_logscale:
            bkg_ticks = np.logspace(
                np.log10(bkgmin+1e-20),
                np.log10(1.2*bkgmax)
                ,6,dtype="float")
            bkg_labs = ["{:.2e}".format(b) for b in bkg_ticks]
        else:
            bkg_ticks = np.linspace(bkgmin,1.2*bkgmax,6,dtype="float")
            bkg_labs = ["{:.2f}".format(b) for b in bkg_ticks]
        fig[1].set_yticks(bkg_ticks)
        fig[1].set_yticklabels(bkg_labs)
        
        #Setting Background Plot legend
        fig[1].legend(prop=legend_properties, loc="upper left")
        #Vacuum figure
        fig_v = fig[n_plots-1]
        self.plot_vacuum(fig_v)

        #Getting Vacuum y ticks
        vmax,vmin = self.get_vacuum_limits()
        vac_ticks = np.linspace(vmin, 1.2*vmax, 6, dtype="float")
        vac_labs = ["{:.1e}".format(v) for v in vac_ticks]
        fig_v.set_yticks(vac_ticks)
        fig_v.set_yticklabels(vac_labs, fontsize=20)
        #Setting vacuum ylabel
        fig_v.set_ylabel("Vacuum pressure [mbar]", fontsize=19)
        #Setting vacuum xticks
        fig_v.set_xticks(ticks)
        fig_v.set_xticklabels(lab, fontsize=20)
        fig_v.set_xlim(start_plot, end_plot)



        #Setting start and stop time labels
        fig_v.set_xlabel("Start: {}       End: {}     Time: UTC".format(
                    datetime.datetime.utcfromtimestamp(start_plot),
                    datetime.datetime.utcfromtimestamp(end_plot) ),
                    fontsize = 20)

        #Setting vacuum plot legend
        fig_v.legend(loc="upper left", bbox_to_anchor=(
                    0.001, 1, 0, 0), prop=legend_properties)


        #Adjusting and saving figures
        plt.subplots_adjust(hspace=0.25)
        plt.savefig(path + "background_graphs_{}.pdf".format(
            1)#self.dataholder.fill_number)
            )



    def plot_vacuum(self,fig):
        for i,var in enumerate(self.dataholder.vacuum_variables):
            fig.plot(
                self.dataholder.times,
                self.dataholder.vacuum_data[var],
                color = self.vac_clrs[i],
                linewidth = 2.5,
                label = var.replace(".X.PR","")
            )


    def get_vacuum_limits(self):
        """
        Calculates maximal and minimal vacuum variable
        """
        biggest = 0
        smallest = 1e308
        for var in self.dataholder.vacuum_variables:
            M = self.dataholder.vacuum_data[var].max() 
            m = self.dataholder.vacuum_data[var].min()
            if M > biggest:
                biggest = M
            if m<smallest:
                smallest = m
            
        return biggest, smallest

        
    def get_bacground_limits(self):
        biggest = np.maximum(
            self.dataholder.plusz.max(),
            self.dataholder.minusz.max()
            )

        smallest = np.minimum(
            self.dataholder.plusz.min(),
            self.dataholder.minusz.min()
        )
        return biggest, smallest
        

def plot_beam_modes(fig,beam_modes,fill_start,fill_stop,set_labels = True):
    """
    Arguments: 
    fig: figure object where to plot
    beam_modes: pandas DataFrame with columns [timestamp, time, cypher, mode]
    #
    timestamp: indicates the time of mesurement
    time: utcdatetime of corresponding timestamp 
    cypher: numeric value of beam mode
    mode: string indicating actual beam mode
    #

    fill_start: timestamp indicating fill start
    fill_stop: timestamp indicating fill end
    """
    N = len(beam_modes["time"])


    for i in range(0,N-1):
        if fill_start > beam_modes["timestamp"].iloc[i] or beam_modes["mode"].iloc[i] == "BEAMDUMP" or beam_modes["mode"].iloc[i] == "RAMPDOWN":
            continue
        if set_labels:
            lab = beam_modes["mode"].iloc[i]
        else:
            lab = None
            
        fig.axvspan(beam_modes["timestamp"].iloc[i],beam_modes["timestamp"].iloc[i+1],
            color = STAGE_COLOR_PALETTE[beam_modes["cypher"].iloc[i]],
            alpha = 0.3, label = lab
            )
    
    if set_labels:
        lab = beam_modes["mode"].iloc[N-1]
    else:
        lab = None

    #These are usually too short to be seen as regions of
    #graph so they are removed for clarity
    if beam_modes["mode"].iloc[N-1] == "BEAMDUMP" or beam_modes["mode"].iloc[N-1] == "RAMPDOWN":
        return
    fig.axvspan(beam_modes["timestamp"].iloc[N-1],fill_stop,
        color = STAGE_COLOR_PALETTE[beam_modes["cypher"].iloc[N-1]],
        alpha = 0.3, label = lab
        )




def get_xlabels(timestamps):
    """
        Gets label timestamps for x axis labels in UTC time
        Arguments:
        timestamps: iterable of locations where timesamp labels should
        be placed.
    """
    dates = []
    for t in timestamps:
        d = datetime.datetime.utcfromtimestamp(t)
        dates.append(
            datetime.time(hour = d.hour,
                            minute= d.minute,
                            second= d.second
                                )
        )
    return dates
