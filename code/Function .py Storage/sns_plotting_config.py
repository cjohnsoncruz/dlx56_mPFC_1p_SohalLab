# sns_plotting_config
#to- store commonalities in plot details
import seaborn as sns
import numpy as np
## set annotator defaults
annotator_default = {'hide_non_significant':True,'fontsize':7, 'line_width': 0.75,
                      'line_offset': 0,'text_offset': 0, 'use_fixed_offset': False,'line_height':0.0125}
## set plotting info
marker_list = ["o", "o", "o",  "x"] #, "o"]

## palette information 
color_list = ['black', 'red', 'dodgerblue', 'limegreen'] #https://matplotlib.org/stable/gallery/color/named_colors.html
geno_order = ['WT VEH', 'Het VEH', 'Het CLNZ', 'Het postCLNZ']
order = geno_order
##colorblind palettes-
colorblind_palette_geno = ['black', 'xkcd:vermillion', 'skyblue', 'limegreen']
colorblind_palette_generic = ['black', 'orange', 'sky blue', 'blue/green', 'yellow', 'blue', 'vermillion', 'reddish purple'] #names from https://www.nature.com/articles/nmeth.1618
colorblind_palette_xkcd = ['black', #black for no stage
                           'xkcd:bright orange', #Early IA Correct
                           'xkcd:sky blue', #Early IA Error
                           'xkcd:sunflower yellow',#late IA
                           'xkcd:purple', #Early RS Correct
                           'xkcd:kelly green',#Early RS Error
                           'xkcd:cobalt blue', #Late RS
                           ] #matching closely aboev paleete
alt_colors = ['xkcd:vermillion','xkcd:reddish purple',]
## stage ordering
phase_list_IA_RS_match= ['Early_IA_Correct','Early_RS_Correct','Early_IA_Error','Early_RS_Error', 'Late_IA', 'Late_RS']
phase_list_IA_RS_chrono= ['Early_IA_Correct','Early_IA_Error','Late_IA','Early_RS_Correct','Early_RS_Error', 'Late_RS']
stage_chrono_order = phase_list_IA_RS_chrono
stage_list_timeorder = phase_list_IA_RS_chrono
no_linestyle = ['none', 'none', 'none', 'none']
stage_palette_dict = {stage:color for stage,color in zip(stage_chrono_order,colorblind_palette_xkcd[1:])}
## color format
geno_color_dict_no_errorbar = {'hue': 'geno_day', 'palette' : color_list, 'hue_order' : geno_order}
#new, added WT CLNZ ## WT CLNZ inclusive layouts 
color_list_WT_CLNZ = ['black', 'grey', 'red', 'dodgerblue', 'limegreen']
geno_order_w_WT_CLNZ = ['WT VEH', 'WT CLNZ', 'Het VEH', 'Het CLNZ', 'Het postCLNZ']
format_no_eb_w_WT_CLNZ = {'hue': 'geno_day', 'palette' : color_list_WT_CLNZ, 'hue_order' : geno_order_w_WT_CLNZ}
geno_order_w_WT_CLNZ_no_eb = format_no_eb_w_WT_CLNZ
color_fmt_no_eb = geno_color_dict_no_errorbar
geno_color_dict= {'hue': 'geno_day', 'palette' : color_list, 'hue_order' : geno_order, 'errorbar': 'se'}
geno_color_dict_w_WT_CLNZ = {'hue': 'geno_day', 'palette' : color_list_WT_CLNZ, 'hue_order' : geno_order_w_WT_CLNZ, 'errorbar': 'se'}
## set aprams specific for each plot type 
marker_edge_width = 0.5
err_bar_width = 0.6 #smaller than normal width
pointplot_param_dict = {'dodge': 0.4,'capsize': 0.0, 'markers': 'o', 'errwidth': err_bar_width} #'err_kws': {'linewidth': 0.6}
swarmplot_param_dict = {'alpha': 0.9, 'marker': 'o', 'linewidth': marker_edge_width,  's': 3, 'edgecolors':'black'}
## colormaps to use
#for heatmaps
cmap = sns.color_palette('icefire', as_cmap = True)
#for rasters?
## set defaults for seaborn 
default_dpi = 300
## elsevier fig sizes https://www.elsevier.com/about/policies-and-standards/author/artwork-and-media-instructions/artwork-sizing
single_col_width = 3.54 #iinches, from website single_col
single_half_col_width = 5.5 #inches
double_col_width = 7.48 #inches
legend_defaults = {"mode": None, "labelspacing":0.0, "markerscale":1.25, 
                   "borderpad":0.1,'columnspacing' :0.3,'handletextpad' : 0.25,}
##context at 0.75 scale
mid_scale_rc =  {'pdf.fonttype': 42, 'pdf.use14corefonts': False,
                 'svg.fonttype': None,'ps.fonttype': 42,'font.size': 6,
 'axes.labelsize': 6, 'axes.titlesize': 6, 'figure.titlesize': 6,
 'xtick.labelsize': 6, 'ytick.labelsize': 6,
 'legend.fontsize': 6, 'legend.title_fontsize': 6,
 'axes.linewidth': 1.0, 'grid.linewidth': 0.8,
 'lines.linewidth': 0.75, 'lines.markersize': 2.0,'patch.linewidth': 0.75,
 'xtick.major.width': 1.0, 'ytick.major.width': 1.0,
 'xtick.minor.width': 0.8, 'ytick.minor.width': 0.8,
 'xtick.major.size': 4, 'ytick.major.size': 4, 
 'xtick.minor.size': 3, 'ytick.minor.size': 3,
 "axes.spines.top":False, "axes.spines.right":False,
  'figure.constrained_layout.use': True,'savefig.dpi': default_dpi, 'figure.dpi': default_dpi,
  'savefig.bbox':'tight'}
sns_context = {'font_scale': 0.75, 'rc' :{**mid_scale_rc}}
mid_scale_dict = sns_context
## for posthoc comparison 
preset_comparison_list = [(geno_order[0], geno_order[1]),
                           (geno_order[1], geno_order[2]),
                             (geno_order[1], geno_order[3])]
comparison_list_w_WT_CLNZ = [(geno_order_w_WT_CLNZ[0], geno_order_w_WT_CLNZ[1]), # [('WT VEH', 'WT CLNZ'),
                             (geno_order_w_WT_CLNZ[0], geno_order_w_WT_CLNZ[2]), #  ('WT VEH', 'Het VEH'),
                             (geno_order_w_WT_CLNZ[2], geno_order_w_WT_CLNZ[3]), #  ('Het VEH', 'Het CLNZ'),
                             (geno_order_w_WT_CLNZ[2], geno_order_w_WT_CLNZ[4])] #  ('Het CLNZ', 'Het postCLNZ')]




# elseiver information
fig_size_dict = {'1_col':single_col_width,'1.5_col':single_half_col_width,'2_col':double_col_width,}## set up col width
single_col_width = 3.54 #iinches, from website single_col # single_half_col_width = 5.5 #inches # double_col_width = 7.48 #inches


stage_to_fig = { ('Early_IA_Error_v_Early_RS_Error', 'Early_IA_Error'): 5,
                ('Early_IA_Error_v_Early_RS_Error', 'Early_RS_Error'): 5,
                ('Early_IA_Correct_v_Early_RS_Correct', 'Early_IA_Correct'): 6,
                ('Early_IA_Correct_v_Early_RS_Correct', 'Early_RS_Correct'): 6,
                ('Early_IA_Correct_v_Late_IA', 'Early_IA_Correct'): 7,
                ('Early_IA_Correct_v_Late_IA', 'Late_IA'): 7,
                ('Late_IA_v_Early_RS_Correct', 'Late_IA'): 7,
                ('Late_IA_v_Early_RS_Correct', 'Early_RS_Correct'): 7,
                ('Early_RS_Correct_v_Late_RS', 'Early_RS_Correct'): 's_4',
                ('Early_RS_Correct_v_Late_RS', 'Late_RS'): 's_4',
                ('Early_RS_Correct_v_Early_RS_Error', 'Early_RS_Correct'): 's_3',
                ('Early_RS_Correct_v_Early_RS_Error', 'Early_RS_Error'): 's_3',
                ('out_of_distribution'): 9
               }