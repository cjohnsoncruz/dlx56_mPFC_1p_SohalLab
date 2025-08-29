## TO- collect functions that act on matplotlib ax objects, and alter their attributes
############
#########major funcs
import matplotlib
from matplotlib import pyplot as plt
import seaborn as sns
import textwrap
import helper_functions
import sns_plotting_config as sns_cfg 

def add_ax_outline():
    ''' To- draw red boxes around the extent of axes listed in the figure automatically'''
# Force layout to finalize
plt.gcf().canvas.draw()
renderer = plt.gcf().canvas.get_renderer()
# Loop through all axes and draw tight bounding boxes
for i, ax in enumerate(plt.gcf().axes):
    bbox_display = ax.get_tightbbox(renderer)  # in display coords
    bbox_figure = bbox_display.transformed(plt.gcf().transFigure.inverted())  # to fig coords
    print(f"Axes {i}: x={bbox_figure.x0:.3f}, y={bbox_figure.y0:.3f}, w={bbox_figure.width:.3f}, h={bbox_figure.height:.3f}")
    rect = matplotlib.patches.Rectangle((bbox_figure.x0, bbox_figure.y0),bbox_figure.width,bbox_figure.height,
        transform=plt.gcf().transFigure,fill=False,edgecolor='red',linewidth=1.5,zorder=1000,clip_on=False)
    plt.gcf().add_artist(rect)

def add_ax_array_row_title(fig, row_titles:list, ax_array, **kwargs):
    ''' To, given an numpy array containing mpl axes, add N titles for each of the N rows'''
    #force figure rendering to get renderer obj
    fig.canvas.draw() # force a draw so that the Text has a renderer
    renderer = fig.canvas.get_renderer()
    #get extent of titles to allow pseudo -subfig plotting
    text_defaults = {**dict(ha='center', va='bottom',fontsize=6),**kwargs}
    for row_count, title in enumerate(row_titles):     # Compute a y position halfway through each row’s block
        title_text = ax_array[row_count,0].title
        bbox_disp = title_text.get_window_extent(renderer) # 3. get the bbox in display (pixel) coords
        bbox_fig = bbox_disp.transformed(fig.transFigure.inverted()) # 4. convert that Bbox into figure (0–1) coords   
        fig.text(0.5, bbox_fig.y1 + 0.025, title,text_defaults) # now overlay a centered title above each row

def get_move_legend_above_ax(plot_ax, bbox_to_anchor = None, **kwargs):
    ''' get legend object from plot_ax, and reshape an dmove legend to occur above current ax obj'''
    if bbox_to_anchor is None:
        bbox_to_anchor = (0.525, 1.0)

    #get legend info
    hand, labs =plot_ax.get_legend_handles_labels() 
    #remove legend 
    plot_ax.get_legend().remove()
    #move to location
    plot_ax.legend(hand, labs, bbox_to_anchor=bbox_to_anchor,loc = 'lower center', ncols = 4, frameon = False, **sns_cfg.legend_defaults)

def add_xtick_color_boxes(ax_plot, xtick_order: list, color_palette: dict, **kwargs):
    '''Add a colored box to each tick label'''
    # Set default box properties
    defaults = {
        'edgecolor': 'None',
        'alpha': 0.4,
        'pad': 1
    }
    box_props = {**defaults, **kwargs}  # User kwargs override defaults
    for label_count, label in enumerate(ax_plot.get_xticklabels()):
        label.set_bbox({
            'facecolor': color_palette[xtick_order[label_count]],
            **box_props
        })


def add_spaces_linebreak_to_stage_ticks(stage_ax_ticks): 
    ''' TO- given a list of ax ticks that consist of task stages with understores, replace the underscores with spaces, then insert a line break char at position 9 (where early IA/RS ends)'''
    labels_w_spaces = [x.get_text().replace("_", " ") for x in stage_ax_ticks]
    labels_wrapped = [x[:8] + "\n" + x[8:] for x in labels_w_spaces if x not in ["Late IA", "Late RS"]]
    return labels_wrapped 

def ax_add_stage_names_and_outline_points(ax_obj):
    #tweak asthetics by 1) outlining pointplot objects and 2) adding the 2 layer scheme 
    set_pointplot_edgecolor(ax_obj, edge_color = 'black', linewidth = sns_cfg.marker_edge_width)# replaces: # for s in sc.collections:# s.set_edgecolor("black"), s.set_linewidth(marker_edge_width)
    sec, sec2, is_dict = set_stage_xticks_2_layer(ax_obj, sns_cfg.phase_list_IA_RS_chrono)


## functions for altering xtick labels to be 2 layered, with optional lines involved in them
def set_stage_xticks_2_layer(plot_ax, stage_order):
    
    ## given ordering of xposition, get the list of what ticks are belonging to what task stage
    is_dict = helper_functions.get_bool_category_vecs(stage_order)
    ## combine bool lists with str categories to create new
    early_and_rule = helper_functions.get_early_rule_str_list(is_dict)
    correct_and_error = helper_functions.get_correct_error_str_list(is_dict)
    ## add second layer of labels
    plot_ax.set_xticks(plot_ax.get_xticks(), correct_and_error) #change current ticks to correct/error label only
    sec = plot_ax.secondary_xaxis(location=0) #add 2ndary access to list Early/late RS/IA
    sec.set_xticks(ticks = helper_functions.get_unique_stage_mean_xtick_loc(plot_ax.get_xticks(), early_and_rule),
                labels=['\n\n' + e for e in set(early_and_rule)])
    sec.tick_params('x', length=0)
    # add lines between the 2 axis layers:
    sec2 = add_ax_secondary_ticks(plot_ax, loc = [1.5, 2.5, 4.5], tick_len = 25, tick_width =1)
    return sec, sec2, is_dict
####### subfuncs

def set_ax_title_xlabel_ylabel(ax, label_dict):
    if 'title' in label_dict.keys():
        title_obj = label_dict['title']
        if type(title_obj) == dict:
            ax.set_title(**title_obj)
        else:
            ax.set_title(title_obj)
    if 'xlabel' in label_dict.keys():
        ax.set_xlabel(label_dict['xlabel'])
    if 'ylabel' in label_dict.keys():
        ax.set_ylabel(label_dict['ylabel'])
    if 'xlim' in label_dict.keys():
        ax.set_xlim(label_dict['xlim'])
    if 'xticks' in label_dict.keys():
        ax.set_xticks(label_dict['xticks'])
    if 'yticks' in label_dict.keys():
        ax.set_yticks(label_dict['yticks'])
    if 'ylim' in label_dict.keys():
        ax.set_ylim(label_dict['ylim'])
    if 'xtick_rotation' in label_dict.keys():
        ax.set_xticklabels(ax.get_xticklabels(), **label_dict['xtick_rotation'])
    if 'ytick_rotation' in label_dict.keys():
        ax.set_yticklabels(ax.get_yticklabels(), **label_dict['ytick_rotation'])
    if 'despine' in label_dict.keys():
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
    if 'legend_false' in label_dict.keys():
        ax.get_legend().remove()
    if 'plot_xy_r_val' in label_dict.keys(): #if present, annotate with r value position
        _,_,_= get_add_pval_rval_text(ax, 0.1, 0.4, label_dict['plot_xy_r_val']['x'],label_dict['plot_xy_r_val']['y'])
    # if 'legend' in label_dict.keys():
    #     ax.legend_.remove()
    if 'xticktop' in label_dict.keys():
        ax.xaxis.tick_top()

        
set_labels = set_ax_title_xlabel_ylabel  #alias for ax level alteration  

##helper func for turning sns pointplot edge colors to black + custom lim
def set_pointplot_edgecolor(sns_obj, edge_color = None, linewidth = None):
    if edge_color == None:
        edge_color = 'black'
    if linewidth == None:
        linewidth = 0.6
    for s in sns_obj.collections:
        s.set_edgecolor(edge_color), s.set_linewidth(linewidth)
outline_points = set_pointplot_edgecolor #alias for pointplot edge color alteration

#minor polishing funcs
def drop_ax_legend_despine(ax_plot):
    ax_plot.get_legend().remove()
    sns.despine(ax = ax_plot)
#subplots adjust
def add_suptitle_and_subplot_adjust(fig_obj, title_str, adjust_float = None, fontsize = None):
    if adjust_float is not None:
        fig_obj.subplots_adjust(top = adjust_float)
    if fontsize == None:
        fontsize = 6
    fig_obj.suptitle(title_str, fontsize = fontsize)

def get_xtick_pos_text_list(ax, tick_to_plot):
    #TO: get list of [x_pos, x_tick_text] for all xticks
    #tick_to_plot:list of str values to keep of known tick labels
    #ax = ax lol
    x_ticks = ax.get_xticklabels()
    new_labels = [[l.get_position()[0],l.get_text()] for l in x_ticks if l.get_text() in tick_to_plot]
    return new_labels

def set_xticklabel_text_wrap(ax, **kwargs): #
#doc on textwrap label = https://docs.python.org/3/library/textwrap.html #base params {'width': 70, 'break_long_words' : True, 'break_on_hyphens': True}
    ax.set_xticks(ax.get_xticks(), [textwrap.fill(x.get_text().replace("_", "-"),**kwargs) for x in ax.get_xticklabels()]) 

def set_xticklabel_underscore_to_space(ax, **kwargs): #
    ax.set_xticks(ax.get_xticks(), [x.get_text().replace("-", " ") for x in ax.get_xticklabels()])

def label_despine_ax(ax, label_dict):
    set_labels(ax, label_dict)
    ax, (handles, labels) = despine_remove_legend(ax)
    return ax, (handles, labels)

def despine_remove_legend(ax):
    #to- despine ax of interest + remove labels     #returns: ax obj, (handles_labels)
    sns.despine(ax = ax)
    handles, labels = ax.get_legend_handles_labels()#get legend information then remove
    ax.get_legend().remove()
    return ax, (handles, labels)
## ax level functions-- add more ticks/layers
def add_ax_secondary_ticks(ax_obj, loc, tick_len, tick_width):
    sec2 = ax_obj.secondary_xaxis(location=0)
    sec2.set_xticks(loc, labels=[], )
    sec2.tick_params('x', length=tick_len, width=tick_width)
    return sec2
