## created 9/18/24
## TO- collect statannot functions previoulsy collected in /helper functions/ file, and have under one module
from ax_modifier_functions import *
from helper_functions import * 
import scipy
from scipy import stats
from stat_tests import * 
import warnings
from typing import List, Optional, Union

import matplotlib.pyplot as plt
import matplotlib.transforms as mtransforms
import numpy as np
import seaborn as sns
import logging 
import matplotlib
import custom_module_imports as cmi
annotator_default = cmi.sns_cfg.annotator_default

# Import ax_inference functions without circular import
# Define imports that will be used when module is part of a package
try:
    from plot_posthoc_test.ax_inference import get_x_ticks_as_df, get_hue_point_loc_df, get_hue_errorbar_loc_dict
# Fall back to direct import when run as a script
except ImportError:
    from ax_inference import get_x_ticks_as_df, get_hue_point_loc_df, get_hue_errorbar_loc_dict

## plotting functions
path_collection_type = matplotlib.collections.PathCollection
line_type = matplotlib.lines.Line2D
## child based functions-
def check_if_row_has_nan(input_array):
    return np.any(np.isnan(input_array),axis = 1)

def get_ax_children_types(ax_obj):
    ''' To- return list stating what type each child of the mplt ax object is'''
    return [type(x) for x in ax_obj.get_children()]


def return_ax_child_line_coor(ax_childs, ax_child_points_index):
    ''' Given a set of indices of the ax child objects between which to query (e.g. path collections index), find fully nonnan yvals in the lines (corresponding to the actual real vertical errorbar) and return coords'''
    #get errorbar lims via #get non nan values
    ci_info = []
    for count, i in enumerate(ax_child_points_index):
        #get range around points, looking back  
        if count == 0:
            range_start = 0
        else: 
            range_start = ax_child_points_index[count-1]+1
        range_end = i
        # main body
        child_range = ax_childs[range_start: range_end] #create list of ax children instances
        #store each entry in a list of 1 dict per line obj 
        cis = [{'child_index': count + range_start ,
                'child_x':np.round(x.get_xdata(),decimals = 2),
                'child_y':x.get_ydata(),
               'next_collection_index': i} for count, x in enumerate(child_range)] #each child N gets a dict N with information
        child = pd.DataFrame.from_records(cis)
        ci_info.append(child)
    # ci_x = [x.get_xdata() for x in child_range] # ci_y = [x.get_ydata() for x in child_range] #old way of getting x values
    coords = pd.concat(ci_info).reset_index()    
    return coords

# def return_point_in_one_sample():#THIS ONLY WORKS WITH 1 VALUEs
#     ci_nonnan_index = [count for count, x in enumerate([np.any(x) for x in np.isnan(ci_y)]) if x == False][0] #errorbar is entry with 0 nan values
#     #store as dict for transform in to df
#     curr_ci = {'ci_index': ci_nonnan_index + range_start, 'ci_xvals': ci_x[ci_nonnan_index], 'ci_yvals': ci_y[ci_nonnan_index] }
#     ci_info.append(curr_ci)
#     return pd.DataFrame.from_records(ci_info)

def is_val_between_range_min_max(value, range_array):
    ''' smple function'''
    is_lessthan_max = value < np.max(range_array)
    is_greaterthan_min = value> np.min(range_array)
    return is_lessthan_max & is_greaterthan_min

# Created more efficient version, defunct
# def get_errorbar_span_of_hue_loc(hue_point_x_loc, hue_point_y_loc, ax_child_df, size_match = 2):
#     '''checks 4 things: 1-2) is test_y value bewteen min/max of a line's span 3) is a row size == 2 [meaning probably line] and 4) is hue loc in a given ax child's x value'''
    
#     is_size_match = ax_child_df.y_is_2_elem #use pre-build bool
#     is_in_child_x_vals = test_val in ax_child_df.child_x
#     #if match first 2 vec, investigate w third
#     is_hue_point_in_range_bounds = is_val_between_range_min_max(hue_point_y_loc ,ax_child_df.child_y)
#     all_match = is_in_child_x_vals & is_size_match & is_hue_point_in_range_bounds
#     return all_match

def get_child_df_row(hue_cat_loc,hue_num_loc, bar_coords):
    ''' non vectorized function relying on vectorized subfuunctions'''
    ##run comparisons to get bool
    is_size_match = bar_coords.y_is_2_elem# print(is_size_match)
    is_in_child_x_vals = bar_coords.apply(lambda x:np.round(hue_cat_loc,decimals = 2) in x.child_x,axis = 1)
    is_hue_point_in_range_bounds = bar_coords.apply(lambda x: is_val_between_range_min_max(hue_num_loc,x.child_y),axis = 1)
    #these need to iterate over entire DF to get complete bool made
    bar_row_bool = is_hue_point_in_range_bounds & bar_coords.y_is_2_elem & is_in_child_x_vals
    row_match = bar_coords[bar_row_bool].drop([x for x in ['index','next_collection_index', 'child_index'] if x in bar_coords.columns],axis = 1)
    return row_match

def add_errorbar_loc_on_posthoc(posthoc_df, bar_coords, overwrite_num_loc= True):
    ''' merges posthoc df with newly created errorbar span detection. Overwrites g1_num_loc and g2_num_loc with max values of errorbar span'''
    success_rows, error_rows = [], []
    for row in posthoc_df.itertuples():
        group_info = row.g1_num_loc#=14.125, g2_num_loc=13.5, g1_cat_loc=-0.2, g2_cat_loc=-0.1, max_group_loc_val=14.125
        # print(row.g1_cat_loc, row.g1_num_loc,row.g2_cat_loc, row.g2_num_loc)
        g1_row_match = get_child_df_row(row.g1_cat_loc, row.g1_num_loc, bar_coords).assign(**{'g1_cat_loc':row.g1_cat_loc, 'g1_num_loc': row.g1_num_loc}).rename({x: "_".join(["g_1",x])for x in ['child_x','child_y']},axis = 1)
        g2_row_match = get_child_df_row(row.g2_cat_loc, row.g2_num_loc, bar_coords).assign(**{'g2_cat_loc':row.g2_cat_loc, 'g2_num_loc': row.g2_num_loc}).rename({x: "_".join(["g_2",x])for x in ['child_x','child_y']},axis = 1)

        success_rows.append(pd.concat([g1_row_match.reset_index(drop=True), g2_row_match[g2_row_match.columns.difference(g1_row_match.columns)].reset_index(drop=True)],axis = 1))

        if (g1_row_match.size == 0) |(g2_row_match.size == 0) :
            error_rows.append(row.Index)

    ebar_loc = pd.concat(success_rows)
    assert (len(error_rows)==0), f" len {error_rows} of error rows list"
    posthoc_df = posthoc_df.merge(ebar_loc, how = 'left', on = ['g1_num_loc', 'g2_num_loc', 'g1_cat_loc', 'g2_cat_loc'])
    if overwrite_num_loc:
        posthoc_df.loc[:, 'g1_num_loc'] = posthoc_df.apply(lambda x: x['g_1_child_y'].max(),axis = 1)
        posthoc_df.loc[:, 'g2_num_loc'] = posthoc_df.apply(lambda x: x['g_2_child_y'].max(),axis = 1)
    return posthoc_df

## bottom up, but starting from close above points
def plot_sig_bars_w_comp_df_tight(
    ax_input, sig_comp_df, direction_to_plot = None,tight = None,
     tight_offset = None, offset_constant=None,align = None, debug = None):
    """ 
    Plot significance bars with comparison dataframe, using a tight layout.
    TO- given parameters, plot vertical lines between centers of datapoints of interest (pre-sorted), with significance star (pre-calculated)
    Parameters
    ax_input (matplotlib.axes.Axes): The input axis object.
    sig_comp_df (pandas.DataFrame): DataFrame with significance comparisons.
    direction_to_plot (str, optional): Direction to plot ('top_down', 'bottom_up'). Defaults to 'bottom_up'.
    tight (bool, optional): Whether to plot bars right above their corresponding values. Defaults to True.
    tight_offset (float, optional): Offset for tight layout. Defaults to 0.075. REfers to how far above the starting datapoint to begin drawing lines
    offset_constant (float, optional): Constant for offset. Defaults to 0.02. Refers to fig amount each line is moved above bbox
    debug (bool, optional): Whether to print debug information. Defaults to None.
    """
    ## plotting params    #set direction to plot ('top_down', 'bottom_up') #set whether bars are plotted right above their coresponding values, or not
    #default vcalues
    if direction_to_plot is None:
        direction_to_plot = 'bottom_up'
        line_start_y_pos = 0.8 #base case- plot upwards from 0.8 of ax size 
        
    if tight is None:
        tight = True #set whether or not to plot bars RIGHT above datapoints
        
    if tight_offset is None:
        tight_offset = 0.04 #fraction of ax to put between the point of interest and the line of sig post-hoc
    #params for offsetting
    line_height = 1.00 #base case- 1.01
    if offset_constant is None:
        offset_constant = 0.02 #what linear amount to add, in AX FRACTION AMOUNT 
    if align is None:
        horz_align = 'center' #horizontal alignment of star over line
        vert_align = 'center_baseline' #vertical alignment of star over line
        fontsize = 8 #font size of star
        fontweight = 'normal' #font weight of star, changed from light to normal
    #originall in ax fraction, I want in pixels?
    star_space_to_line = offset_constant*1
    
    #declare initial transforms of interest
    transform_ax_to_data = ax_input.transAxes + ax_input.transData.inverted() #create ax-display + display-data pipe
    transform_data_to_ax = transform_ax_to_data.inverted() # 
        #transData transforms: (DATA) -> (DISPLAY COORDINATES)     # transAxes transforms (AXES) -> (DISPLAY)     #all transforms -> display coords 
    trans = matplotlib.transforms.blended_transform_factory(x_transform = ax_input.transData,
                                                            y_transform = ax_input.transAxes)# the x coords of this transformation are data, and the y coord are axes
    ##set default bbox
    category_base_y_box = np.array([[0, 0],[0, 0]])#initialize box location for comparison # =[lower_x, lower_y] [upper_x, upper_y]
    ## main loop over categorical ticks, bottom up approach 
    for cat in sig_comp_df['category_compared_within'].unique():#iterate over each categorical tick value
        sig_comp_category = sig_comp_df.loc[sig_comp_df.category_compared_within == cat,:]
        #get max y position value for each category you're doing post-hoc comparisons within
        top_bbox = category_base_y_box #for first iter, set blank
        category_highest_y = top_bbox[1,1]
        if tight:
            #transform max group location from DATA to AXIS
            max_numeric_ax_value = sig_comp_category.loc[:, ['g1_num_loc','g2_num_loc']].max().values.max()    #get max val in the group of interest you're running posthocs on (x ticks of interest)    
            line_start_y_pos = transform_data_to_ax.transform((0,max_numeric_ax_value))[1]+tight_offset # data -> axes 
            if debug == True:
                print(f'tight format, max_numeric_ax_value = {max_numeric_ax_value}.  start y val  = {line_start_y_pos}')
            #transData transforms: (DATA) -> (DISPLAY COORDINATES)     # transAxes transforms (AXES) -> (DISPLAY)     
        for comp_count, comp in enumerate(sig_comp_category.itertuples()):
            x_vals = get_sig_bar_x_vals(comp) # [comp.g1_cat_loc, comp.g1_cat_loc, comp.g2_cat_loc, comp.g2_cat_loc]# list the 4 x coord for points that define the line
            ##max of numerical ax values is taken during INITIAL localization of points, not post errorbar detection
            y_vals =get_sig_bar_y_vals(bottom_val = line_start_y_pos,line_height = line_height) #  [comp.max_group_loc_val, comp.max_group_loc_val * h, comp.max_group_loc_val * h, comp.max_group_loc_val] # list 4 y coord for points that define the line
            #compare overlap of proposed y values, in data space 
            if debug == True:
                print(f"Comp: {comp_count} line overlap = ({y_vals[0]} <= {category_highest_y}). line x_vals, y_vals: {x_vals, y_vals}")
            line_overlap = (y_vals[0] <= category_highest_y )##check y overlap with previous bounding box,       #top right point y val in top_box defined by [1,1]
            if line_overlap: #if the top of the prev bbox overlaps with the current line, move the current line up to ABOVE top bbox
                y_vals = get_sig_bar_y_vals(category_highest_y+ offset_constant,line_height)             ## if overlaps with previous bounding box, adjust height by N
            #set position for star/sig. annotation
            text_x = (x_vals[0]+ x_vals[2])*.5
            #do you need to have additional space to line 
            text_y = y_vals[1] + star_space_to_line #what linear amount to separate star from line, in AX FRACTION AMOUNT 
            #plot annot line over pair 
            ax_input.plot(x_vals, y_vals, lw=annotator_default['line_width'], color = 'black',transform = trans, clip_on = False)
            #plot sig star over line
            star_str = convert_pvalue_to_asterisks(comp.pvalue)
            star_annot = ax_input.annotate(star_str, ha=horz_align, va=vert_align, fontsize =fontsize,fontweight = fontweight,
                                           xy = (text_x, text_y), xycoords = ('data', 'axes fraction'), 
                                           bbox = {'boxstyle': 'Square', 'pad': 0.05, 'fc': 'None', 'lw': 0})
             #CRITICAL STEP- UPDATE CANVAS BEFORE DRAWING TO ENSURE OVERLAP NOT AFFECTED
            ax_input.figure.canvas.draw()
            bbox_in_ax = ax_input.transAxes.inverted().transform(star_annot.get_window_extent()) #Get the artist's bounding box in display space.
            # ax.transData.inverted() is a matplotlib.transforms.Transform that goes from display coordinates to data coordinates
            top_bbox = bbox_in_ax      #detect overlap by storing, then comparing ot previous versions
            category_highest_y = max(category_highest_y, bbox_in_ax[1, 1] + 1*offset_constant) #star_space_to_line)

            if debug:
                print(f'text-y = {y_vals[1]} + {star_space_to_line}')
                print(f" annot bbox window extent {type(star_annot.get_window_extent())} ({star_annot.get_window_extent()}")
                print(f" annot bbox in transform ({star_annot.xycoords}) : ({star_annot.xy})")
                print(f"bbox transformed: {bbox_in_ax} \n")
   
## test running functinos
#common error- ValueError: Cannot set a DataFrame with multiple columns to the single column g1_num_loc- this is if you mistype the hue value or you use the wrong version of SNS 
def main_run_posthoc_tests_and_get_hue_loc_df(ax_input, plot_params, plot_obj, preset_comparisons,
                                               hue_var= None, test_name = None, hue_order = None, ax_var_is_hue=False,detect_error_bar = False,
                                               plot_type = None):
    """ 
    Run posthoc tests on all axis ticks, get hue levels for each axis tick, and join this to the dataframe produced.

    Parameters:
    ax_input (matplotlib.axes.Axes): The input axis object.
    plot_params (dict): Dictionary containing plot parameters.
    plot_obj (seaborn.axisgrid.FacetGrid): The plot object.
    preset_comparisons (list): List of preset comparisons.
    hue_var (str, optional): The hue variable. Defaults to None.
    test_name (str, optional): The name of the test. Defaults to None.
    hue_order (list, optional): The order of the hue. Defaults to None.
    ax_var_is_hue (bool, optional): Whether the axis variable is the hue. Defaults to False.

    Returns:
    pandas.DataFrame: DataFrame with posthoc test results and hue locations.
    """
    external_plot_type = plot_type 
    if plot_type is None: #default to pointplot
        plot_type = 'pointplot'
    
    if hue_var is None:
        hue_var = plot_params['hue']
    if hue_order is None:
        hue_order = plot_params['hue_order']
    if test_name is None:
        test_name = None
        # group_order- depends on if comparing within x axis, or within hues 
    if ax_var_is_hue: #you will use this to find the ordering of the hue collection points of interest
        group_order = plot_params['hue_order'] #order in collection = order in hue
    else: #if hue collection tiled over differnt x categories
        group_order = plot_params['order'] #order in collection = order in x category
    posthoc_df = run_posthoc_tests_on_all_ax_ticks(plot_params['data'], plot_obj = plot_obj, 
                                                   comparison_list =preset_comparisons, ax_grouping_col= plot_params['x'],
                                                   group_order = group_order, hue_col_name=hue_var, value_col_name = plot_params['y'],
                                                   test_name = test_name,ax_var_is_hue=ax_var_is_hue)## get df with info on post-hoc comparisons
    
    #locate hue points based on what plot you are working with     #e.g. pointplot uses collections, barplot doesn't 
    if plot_type in ['pointplot', 'stripplot']: #stripplot is a pointplot with jitter, so same logic applies
        hue_loc_df = get_hue_point_loc_df(ax_input, hue_order) # hue_loc_df = pd.DataFrame.from_dict(get_hue_point_loc_dict(plot_ax, geno_order)).set_index('hue') #get array of numerical points and values for each hue level
        #manually set cat compared within to single variable if hue == axis category
    if plot_type == 'barplot': #given barplot doesn't use colelctions, write custom script s to detect positions
        #get hue location via barplot  #barplot- non errorbar handling
        rects = [x for x in ax_input.get_children() if (isinstance(x, matplotlib.patches.Rectangle) and not np.isnan(x.get_height()))] #get non nan rects, which are REAL data 
        #barplot equivalent- manually gets x center and height (as starts at 0, equals to y pos), transforming to rectangle
        rect_count_loc = [(count, 
                           np.array([[x.get_center()[0], x.get_height()],
                                     [x.get_center()[0], x.get_height()]]) #repeat (x at center, y height) to allow for the errorbar dependent code to pick it up 
                          ) for count,x in enumerate(rects)if ((x is not ax_input.patch) and not np.isnan(x.get_height()))] #need to set list o list as np array for rpoper indexing
        
        hue_point_loc_dict = [{'hue': hue_order[count], 'data_locs': locs} for count,locs in rect_count_loc]
        hue_loc_df = pd.DataFrame(hue_point_loc_dict).set_index('hue')
    posthoc_df = get_hue_loc_on_axis(hue_loc_df, posthoc_df,plot_type =plot_type) #find pos in numerical ax of fig, then add as cols to df
    #store in posthoc_df
    if ax_var_is_hue: #you will use this to find the ordering of the hue collection points of interest
        posthoc_df['category_compared_within']= plot_params['x']
    
    if detect_error_bar: #NEW_ add errorbar locs to posthoc df        # logging.info('Error bar detected, moving bounds')
        if plot_type in ['pointplot']: #stripplot is a pointplot with jitter, so same logic applies
            ax_childs =plot_obj.get_children()
            ax_child_points_index = [count for count, x in enumerate( get_ax_children_types(plot_obj)) if x is path_collection_type]
            #merge errbarbar info with existing posthoc df 
            bar_coords =  return_ax_child_line_coor(ax_childs,ax_child_points_index)
        if plot_type == 'barplot':            #func- get bar coordinates
            #barplot- errorbar detection #adapting errorbar line inheritance 
            lines = [x for x in ax_input.get_children() if isinstance(x, matplotlib.lines.Line2D)]
            cis = [{'child_index': count,
                    'child_x':np.round(x.get_xdata(),decimals = 2),
                    'child_y':x.get_ydata(), } for count, x in enumerate(lines) if not np.isnan(x.get_ydata()).any()] #each child N gets a dict N with information
            bar_coords = pd.DataFrame.from_records(cis).reset_index()
            
        bar_coords['y_is_nonnan'] = bar_coords.child_y.apply(lambda x: np.logical_not(np.any(np.isnan(x))))
        bar_coords['y_is_2_elem'] =bar_coords.child_y.apply(lambda x:x.size == 2)
        ## merge bar corods 
        posthoc_df =add_errorbar_loc_on_posthoc(posthoc_df, bar_coords)
        #if using barplot- drop nan rows (as those arne't real lines)
        drop_nan_row= True
        if drop_nan_row:
            bar_coords=bar_coords[bar_coords['y_is_nonnan']]
    
    #final posthoc df editing 
    posthoc_df['max_group_loc_val'] = posthoc_df[['g1_num_loc', 'g2_num_loc']].max(axis = 1)    #now, detect max value get max of numerical ax values
    posthoc_df.loc[:, ['group_1_mean','group_1_sem','group_2_mean','group_2_sem']] = posthoc_df.loc[:, ['group_1_mean','group_1_sem','group_2_mean','group_2_sem']].round(4)
    #new- record what the comparison is, and what the hue level is
    posthoc_df['numeric_var'] = plot_params['y'] #add actual y column
    posthoc_df['hue_var'] = hue_var #add actual y column
    posthoc_df['x_category_var'] = plot_params['x'] #add actual y column
    posthoc_df['hue_is_x_axis'] = ax_var_is_hue #addbool for checking 
    return posthoc_df


## ad hue vs ax order 
def run_posthoc_tests_on_all_ax_ticks(plot_data, plot_obj, 
comparison_list, ax_grouping_col,
group_order, hue_col_name, value_col_name,
test_name = None, ax_var_is_hue = False):
    """ 
    Run posthoc tests on all axis ticks.

    Parameters:
    plot_data (pandas.DataFrame): The plot data.
    plot_obj (seaborn.axisgrid.FacetGrid): The plot object.
    comparison_list (list): List of comparisons.
    ax_grouping_col (str): The column name for axis grouping.
    group_order (iterable): The order of the groups.
    hue_col_name (str): The hue column name.
    value_col_name (str): The value column name.
    test_name (str, optional): The name of the test. Defaults to 'MWU'.
    ax_var_is_hue (bool, optional): Whether the axis variable is the hue. Defaults to False.

        Returns: pandas.DataFrame: DataFrame with posthoc test results.
    """
    if test_name is None:
        test_name = 'MWU'
    
    compare_stats_df = []
    #if the ax levels = the hue levels, don't filter the plot data by what ax group col you're on
    if ax_var_is_hue:
        
        print(f"With axis variable == Hue variable:")
        for geno_pair in comparison_list: #iterate over ex. (WT VEH to HET VEH), do stats on each
            posthoc_output= run_posthoc_test_on_tick_hue_groups(plot_data,
                                                                    geno_pair[0], geno_pair[1], geno_pair,group_order,
                                                                    hue_col_name, value_col_name,test_name = test_name,ax_var_is_hue = ax_var_is_hue)
            compare_stats_df.append(posthoc_output)
    else:
    #iterate through the different categories to compare hue level values within
        for ax_category_level in plot_data[ax_grouping_col].unique():        # print(ax_category_level)
            for geno_pair in comparison_list: #iterate over ex. (WT VEH to HET VEH), do stats on each
                posthoc_output= run_posthoc_test_on_tick_hue_groups(plot_data.loc[plot_data[ax_grouping_col] ==  ax_category_level,:],
                                                                    geno_pair[0], geno_pair[1], ax_category_level, group_order,
                                                                    hue_col_name, value_col_name,test_name = test_name)
                compare_stats_df.append(posthoc_output)
    stat_table = pd.DataFrame.from_records(compare_stats_df)
    # after producing stat result table, merge with df of x tick labels and their positions
    if not(ax_var_is_hue):#transform list of xticklabels to pandas df and merge ## inserted 10.16.24- automerge the xticks
        stat_table = stat_table.merge(get_x_ticks_as_df(plot_obj.get_xticklabels()), left_on = 'category_compared_within', right_on = 'tick_text') 
    return stat_table

##active_unit_df
def run_posthoc_test_on_tick_hue_groups(ax_tick_data, hue_group_1, hue_group_2, ax_category_level,group_order,
                                         hue_col_name, value_cols_name,test_name = None,ax_var_is_hue = False):
    """ 
    Run posthoc test on tick hue groups. Use existing dataframe filtered by the current axis levels, and perform stats on the hue groups.

    Parameters:
    ax_tick_data (pandas.DataFrame): The axis tick corresponding dataframe.
    hue_group_1 (str): The first hue group.
    hue_group_2 (str): The second hue group.
    ax_category_level (str): The axis category level.
    group_order (iterable): The order of the groups.
    hue_col_name (str): The hue column name.
    value_cols_name (str): The value column name.
    test_name (str, optional): The name of the test. Defaults to 'MWU'.
    ax_var_is_hue (bool, optional): Whether the axis variable is the hue. Defaults to False.

    Returns:    dict: Dictionary with the posthoc test results.
    """
    ##define test to run
    if test_name is None:
        test_name = 'MWU'
    ## extract groups from the dataframe containing data corresponding to the ax tick in question
    # ax_tick_data =plot_data.loc[plot_data[ax_grouping_col] ==  ax_category_level,:]
    data_group_1= ax_tick_data.loc[ax_tick_data[hue_col_name] == hue_group_1,:]
    data_group_2= ax_tick_data.loc[ax_tick_data[hue_col_name] == hue_group_2,:]
    ## get values from each grup
    data_group_1_values = data_group_1[value_cols_name].values
    data_group_2_values =data_group_2[value_cols_name].values
    ## run stats on group values
    result_dict = get_pair_stat_test_result(test_name, ax_category_level,group_order, hue_group_1, hue_group_2, data_group_1_values,data_group_2_values,ax_var_is_hue)
    ##new- 5/12/25- record the ax category level, and the hue group names
    result_dict['categorical_subgroup'] = ax_category_level
    return result_dict
    
    ## custom function to do stats on grups of interest
def get_pair_stat_test_result(
    test_name, ax_category_level,group_order, group_1_name, group_2_name,
    data_group_1_values,data_group_2_values,ax_var_is_hue = False):
    """     Run statistical test on data groups.

    Parameters:
    test_name (str): The name of the test.
    ax_category_level (str): The axis category level.
    group_order (iterable): The order of the groups.
    group_1_name (str): The name of the first group.
    group_2_name (str): The name of the second group.
    data_group_1_values (numpy.ndarray): Values of the first group.
    data_group_2_values (numpy.ndarray): Values of the second group.
    ax_var_is_hue (bool, optional): Whether the axis variable is the hue. Defaults to False.

    Returns:
    dict: Dictionary with the statistical test results.
    """
    '''Run stats test on data_group_1_values and data_group_2_values (user input for test )
    ax order- tells you what order elements in the hue category levels are spread across the ax, so you can use later for indexing'''
    ## run stats on group values
    stat_result= []
    use_robust_cohen_d = True
    use_robust_cohen_d_coefficient = False
    if test_name == 'custom':
            print('custom test ran')
    elif test_name == 'MWU':
            stat_result = stats.mannwhitneyu(data_group_1_values, data_group_2_values)
    elif test_name == 'bootstrap_sdev_overlap':
            stat_result = test_group_mean_separation(data_group_1_values, data_group_2_values)
    
    elif test_name == 'cohen_d':
            stat_result = test_group_mean_cohen_d(data_group_1_values, data_group_2_values,
             use_robust_cohen_d = use_robust_cohen_d,
             use_robust_cohen_d_coefficient = use_robust_cohen_d_coefficient)
            
    elif test_name == '2_sample_t_test':
            stat_result = stats.ttest_ind(data_group_1_values, data_group_2_values, equal_var = False) #equal_var = True, run 2 sample ttset, if false, run welch's test for unequal var
    elif test_name == 'permutation_test':
            stat_result =  run_permutation_test_on_diff_of_vector_means( data_group_1_values, data_group_2_values, 10000) #set to .values as original output is dict, and rounding a rdict fails 
    
    #record the stat values (mean, sem etc)     
    if test_name == 'bootstrap_sdev_overlap':
        group_mean_dict ={'group_1_mean':stat_result['group_1_mean'], 'group_1_sem':stat_result['group_1_std'],
                            'group_2_mean':stat_result['group_2_mean'], 'group_2_sem':stat_result['group_2_std']}
        stat_result = [stat_result['mean_diff_more_than_sdevs'], stat_result['pseudo_pvalue']]

    elif test_name == 'cohen_d':
        group_mean_dict ={'group_1_mean':stat_result['group_1_mean'], 'group_1_sem':stat_result['group_1_std'],
                            'group_2_mean':stat_result['group_2_mean'], 'group_2_sem':stat_result['group_2_std']}
        stat_result = [stat_result['cohen_d'], stat_result['pseudo_pvalue'], stat_result['permutation_test_pvalue']]#pseudo-pvalue is U3 of cohen d #new- add permutation test pvalue
        if use_robust_cohen_d:
            test_name = {True: "Corrected", False:""}[use_robust_cohen_d_coefficient]+ 'robust_cohen_d' #add note for if you were corrected 
    else:
        group_mean_dict = {'group_1_mean':np.nanmean(data_group_1_values), 'group_1_sem':scipy.stats.sem(data_group_1_values,nan_policy = 'omit' ),
                            'group_2_mean':np.nanmean(data_group_2_values), 'group_2_sem':scipy.stats.sem(data_group_2_values,nan_policy = 'omit')}
    #pack and return result dict
    # print(group_order)
    if ax_var_is_hue: #if x categorical ticks = hue groups, find index of group1 name in hue order
        group_pos = {'group_1_order_pos': get_match_index_in_iterable(group_order, group_1_name),
                   'group_2_order_pos': get_match_index_in_iterable(group_order, group_2_name)}
    else: #else, find index of ax_category_tick name in xtick order, to pull correct point loc (say of wt-veh, at late IA tick)
        group_pos = {'group_1_order_pos': get_match_index_in_iterable(group_order, ax_category_level),
                   'group_2_order_pos': get_match_index_in_iterable(group_order, ax_category_level)}
        #get where the groups being compared, are listed in the data collections f
 

    result_dict = {'category_compared_within': ax_category_level,
     'group_1': group_1_name, 'group_2':group_2_name,
     'group_1_n':data_group_1_values.shape, 
     'group_2_n':data_group_2_values.shape,
     **group_mean_dict,
     'test_name': test_name, 
     'stat_result': np.round(stat_result, 5),
      'pvalue': stat_result[1],
      **group_pos}
    return result_dict
    ## build custom plotting ufnction

def get_hue_loc_on_axis(hue_loc_df, posthoc_df, detect_error_bar = False,plot_type ='pointplot'): 
    """ 
    Add numerical and categorical axis locations to the posthoc comparison dataframe. Main function creating/label numeric loc on axis 
    NEW (2.6.25)- add detect errorbar  to automatically detect errorbar, and move point marked for symbol loc if so 
    Parameters:
    hue_loc_df (pandas.DataFrame): DataFrame with hue locations.
    posthoc_df (pandas.DataFrame): DataFrame with posthoc comparisons.

    given hue_loc_df listing where each point for the given hue categories are located, use the pre-existing post hoc comparison df
    and add a new column to dataframe indicating y/numerical ax loc for each comparison 
    g1/2_num_loc: the value of position of group 1/2 (usually on the y axis) on the numerical axis used
    g1/2_cat_loc: the value of point of group 1/2 (usually on the x axis) on the categorical axis used
    group_1/2_order_pos is used to to know what the values are 
    Returns:    pandas.DataFrame: Updated DataFrame with axis locations.    
    """
        ## get loc of points on the numerical ax (usually y but not always)
        #index into hueloc df, with index = hue Group_1 name of posthoc df ; then, get list of point vals in collection; then, 
    posthoc_df['hue_group_1_locs'] = posthoc_df.apply(lambda x: hue_loc_df.loc[x['group_1']], axis = 1) #elem index = what x tick num elem is centered on
    posthoc_df['hue_group_2_locs'] = posthoc_df.apply(lambda x: hue_loc_df.loc[x['group_2']], axis = 1) #elem index = what x tick num elem is centered on

#NEW_ strip/swarm plot- get the y loc of the points in the collection, and add to posthoc df
    if plot_type == 'stripplot': #if you are using the default pointplot, need to locate xydata in multi element list
        #strip plot data saves an array of points, so need to get the max value of the y locs in the collection and mean of x locs
        posthoc_df['g1_num_loc'] = posthoc_df.apply(lambda x: np.max(x['hue_group_1_locs'][:,1]), axis = 1) #x['group_1_order_pos'][0] = position of group 1 being used, in ordered list of collections 
        posthoc_df['g2_num_loc'] = posthoc_df.apply(lambda x: np.max(x['hue_group_2_locs'][:,1]), axis = 1) #x['group_1_order_pos'][0] = position of group 1 being used, in ordered list of collections 
        ## get location of poitns on the categorical axis (usually x but not always)
        posthoc_df['g1_cat_loc'] = posthoc_df.apply(lambda x: np.mean(x['hue_group_1_locs'][:,0]), axis = 1) #x['group_1_order_pos'][0] = position of group 1 being used, in ordered list of collections 
        posthoc_df['g2_cat_loc'] = posthoc_df.apply(lambda x: np.mean(x['hue_group_2_locs'][:,0]), axis = 1)#x['group_1_order_pos'][0] = position of group 1 being used, in ordered list of collections

    if plot_type == 'pointplot': #if you are using the default pointplot, need to locate xydata in multi element list
        posthoc_df['g1_num_loc'] = posthoc_df.apply(lambda x: x['hue_group_1_locs'][x['group_1_order_pos'][0],1], axis = 1) #x['group_1_order_pos'][0] = position of group 1 being used, in ordered list of collections 
        posthoc_df['g2_num_loc'] = posthoc_df.apply(lambda x: x['hue_group_2_locs'][x['group_2_order_pos'][0],1], axis = 1) #x['group_1_order_pos'][0] = position of group 1 being used, in ordered list of collections 
        ## get location of poitns on the categorical axis (usually x but not always)
        posthoc_df['g1_cat_loc'] = posthoc_df.apply(lambda x: x['hue_group_1_locs'][x['group_1_order_pos'][0],0], axis = 1) #x['group_1_order_pos'][0] = position of group 1 being used, in ordered list of collections 
        posthoc_df['g2_cat_loc'] = posthoc_df.apply(lambda x: x['hue_group_2_locs'][x['group_2_order_pos'][0],0], axis = 1) #x['group_1_order_pos'][0] = position of group 1 being used, in ordered list of collections


    if plot_type == 'barplot': #if you are using the default pointplot, need to locate xydata in multi element list
        posthoc_df['g1_num_loc'] = posthoc_df.apply(lambda x: x['hue_group_1_locs'][0,1], axis = 1) #x['group_1_order_pos'][0] = position of group 1 being used, in ordered list of collections 
        posthoc_df['g2_num_loc'] = posthoc_df.apply(lambda x: x['hue_group_2_locs'][0,1], axis = 1) #x['group_1_order_pos'][0] = position of group 1 being used, in ordered list of collections 
        ## get location of poitns on the categorical axis (usually x but not always)
        posthoc_df['g1_cat_loc'] = posthoc_df.apply(lambda x: x['hue_group_1_locs'][0,0], axis = 1) #x['group_1_order_pos'][0] = position of group 1 being used, in ordered list of collections 
        posthoc_df['g2_cat_loc'] = posthoc_df.apply(lambda x: x['hue_group_2_locs'][0,0], axis = 1) #x['group_1_order_pos'][0] = position of group 1 being used, in ordered list of collections
    #MOVED EARLIER    #get max of numerical ax values
    # posthoc_df['max_group_loc_val'] = posthoc_df[['g1_num_loc', 'g2_num_loc']].max(axis = 1)
    return posthoc_df 


## custom stat annotation functions 
def convert_pvalue_to_asterisks(pvalue):
    if pvalue < 0.001:
        return "***"
    elif pvalue < 0.01:
        return "**"
    elif pvalue < 0.05:
        return "*"
    return "ns"


def get_sig_bar_x_vals(comparison_tuple):
    """ 
    Get the x-values for the significance bar.

    Parameters:
    comparison_tuple (namedtuple): Tuple with comparison information.

    Returns:
    list: List of x-values for the significance bar.
    """
    x_vals = [comparison_tuple.g1_cat_loc, comparison_tuple.g1_cat_loc,
              comparison_tuple.g2_cat_loc, comparison_tuple.g2_cat_loc]# list the 4 x coord for points that define the line
    return x_vals

def get_sig_bar_y_vals(bottom_val = None, line_height= 1.01):
    """ 
    Get the y-values for the significance bar.
    Parameters:
    bottom_val (float, optional): The bottom value for the bar. Defaults to 0.95.
    line_height (float, optional): The height of the line. Defaults to 1.01.

    Returns:
    list: List of y-values for the significance bar.
    """
    """ comparison tuple max y value is multipled by offset factor"""
    if bottom_val is None:
        bottom_val = 0.95 #for ax relative point plotting
    # bottom_val = comparison_tuple.max_group_loc_val * offset_factor #for data point plotting
    y_vals = [bottom_val,bottom_val* line_height, bottom_val*line_height,bottom_val]# list the 4 x coord for points that define the line
    return y_vals


###############
###############
##DEPRECATED, DEFAULT TO USING THE TIGHT VERSION
## main stat annotation function- no alterations possible NOW DEFUNCT
def plot_sig_bars_w_comp_df(ax_input, sig_comp_df, direction_to_plot = None):
    print(f"WARNING- Deprecated function, use plot_sig_bars_w_comp_df_tight instead")
    """ 
    Plot significance bars with comparison dataframe.

    Parameters:
    ax_input (matplotlib.axes.Axes): The input axis object.
    sig_comp_df (pandas.DataFrame): DataFrame with significance comparisons.
    direction_to_plot (str, optional): Direction to plot ('top_down', 'bottom_up'). Defaults to 'bottom_up'.
 TO- given parameters, plot vertical lines between centers of datapoints of interest (pre-sorted), with significance star (pre-calculated)"""
    ## plotting params
    if direction_to_plot is None:#set direction to plot ('top_down', 'bottom_up')
        direction_to_plot = 'bottom_up'

    line_height = 1.01
    offset_constant = 0.03 #what linear amount to add
    star_space_to_line = offset_constant/5
    trans = matplotlib.transforms.blended_transform_factory(x_transform = ax_input.transData,y_transform = ax_input.transAxes)# the x coords of this transformation are data, and the y coord are axes
    ## main loop over categorical ticks
    for cat in sig_comp_df.category_compared_within:#iterate over each categorical tick value
        top_bbox = np.array([[0, 0],[0, 0]])#initialize box location for comparison # =[lower_x, lower_y] [upper_x, upper_y]
        for comp in sig_comp_df.loc[sig_comp_df.category_compared_within == cat,:].itertuples():
            x_vals = get_sig_bar_x_vals(comp) # [comp.g1_cat_loc, comp.g1_cat_loc, comp.g2_cat_loc, comp.g2_cat_loc]# list the 4 x coord for points that define the line
            y_vals =get_sig_bar_y_vals(0.95,line_height) #  [comp.max_group_loc_val, comp.max_group_loc_val * h, comp.max_group_loc_val * h, comp.max_group_loc_val] # list 4 y coord for points that define the line
            line_overlap = (top_bbox[0,1] >= y_vals[0])##check overlap with previous bounding box
            if line_overlap: #if the top of the prev bbox overlaps with the current line, move the current line up to ABOVE top bbox
                y_vals = get_sig_bar_y_vals(top_bbox[1,1]+offset_constant,line_height)             ## if overlaps with previous bounding box, adjust height by N
            text_x = (x_vals[0]+ x_vals[2])*.5
            text_y = y_vals[1] + star_space_to_line
            #plot sig star over line
            ax_input.plot(x_vals, y_vals, lw=annotator_default['line_width'], color = 'black', transform = trans, clip_on = False)
            star_annot = ax_input.annotate(convert_pvalue_to_asterisks(comp.pvalue),
             xy = (text_x, text_y), xycoords = ('data', 'axes fraction'),
                            ha='center', va='baseline', fontsize = 6,)# bbox = {'boxstyle': 'Square, pad = 0.0', 'fc': 'lightblue', 'lw': 0})
            bbox_in_ax = ax_input.transAxes.inverted().transform(star_annot.get_window_extent()) # to get ax coordinates of bounding box (transform from  Return the Bbox bounding the text, in display units.)
            top_bbox = bbox_in_ax      #detect overlap by storing, then comparing ot previous versions

