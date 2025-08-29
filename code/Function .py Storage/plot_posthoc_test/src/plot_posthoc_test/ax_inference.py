
import numpy as np
import pandas as pd

# ax_inference.py
''' Functions for inferring information from matplotlib axes objects. '''
##AX INFERENCE HELPER FUNCTIONS
##get information about hue locs 
def get_hue_point_loc_df(ax_input, hue_order):
    """ 
    Get a DataFrame of the datapoints at each level of the hue variable.

    Parameters:
    ax_input (matplotlib.axes.Axes): The input axis object.
    hue_order (list): The order of the hue.

    Returns:
    pandas.DataFrame: DataFrame with hue point locations.
    """
    hue_loc_df = pd.DataFrame.from_dict(get_hue_point_loc_dict(ax_input, hue_order)).set_index('hue') #get array of numerical points and values for each hue level
    return hue_loc_df

def get_hue_errorbar_loc_dict(ax_input, hue_order):
    """ 
    Get a dictionary of the data errorbars at each level of the hue variable.

    Parameters:
    ax_input (matplotlib.axes.Axes): The input axis object.
    hue_order (list): The order of the hue in a list.

    Returns:
    dict: Dictionary with hue errorbar  locations.
    """
    hue_point_loc_dict = [{'hue': hue_order[count],
                            'data_locs':x.get_offsets().data} for count, x in enumerate(ax_input.collections)]
    return hue_point_loc_dict

    
def get_hue_point_loc_dict(ax_input, hue_order):
    """ 
    Get a dictionary of the datapoints at each level of the hue variable.

    Parameters:
    ax_input (matplotlib.axes.Axes): The input axis object.
    hue_order (list): The order of the hue.

    Returns:
    dict: Dictionary with hue point locations.
    """
    hue_point_loc_dict = [{'hue': hue_order[count], 'data_locs':x.get_offsets().data} for count, x in enumerate(ax_input.collections) if x.get_offsets().data.size > 0]
    return hue_point_loc_dict

def get_x_ticks_as_df(ticklabel_obj):
    """ 
    Get a DataFrame of the x-tick labels and their positions.

    Parameters:
    ticklabel_obj (list): List of tick label objects.

    Returns:
    pandas.DataFrame: DataFrame with x-tick labels and positions.
    """
    ticks_df = pd.DataFrame.from_records([{'tick_text':x.get_text(), 'tick_pos': x.get_position()} for x in ticklabel_obj])
    return ticks_df
 
