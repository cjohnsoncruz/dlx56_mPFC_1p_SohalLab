# stat_annotation_dependent_functions.py
# TO- hold previous version of functions that were dependent on stannot functions:

############################ old funcs
### ALTERATIONGS TO STATNNOT PACKAGE
##retrieve post-hoc testing information:
# #scipy helper funcion 
def get_posthoc_data_info(res):
    #TO- given a single annotation object, package the information into a dict and return it
    posthoc_info = {}
    g1,g2 = res.data.group1[1],  res.data.group2[1] # group_comp = " v ".join([g1, g2])                # print(group_comp)
    posthoc_info = {'subgroup': res.data.group1[0], 'group1': g1, 'group2': g2, 'pval': res.data.pvalue, 'test': res.data.test_short_name,
                                        'correction_method': res.data.correction_method, 'corrected_sig': res.data.corrected_significance}
    return posthoc_info
## NEW- 10/9/24 Custom stat annotation features 
## TO GET A SINGLE HUE x CATEGORY RESULT
def get_annot_posthoc_result_single_level_df(result_by_stage):
    """TO- given a list of annotations objects created by stannot running on a plot, extract the features of interest of the post-hoc test and concat into a df
    input- result_by_stage,a list of annotations objects"""
    ## main body 
    comp_list =  []     # result_by_stage = all_ax_annots#  [r for r in all_ax_annots]
    for stage in result_by_stage:    ## loop over all combos 
        for res in stage: #scroll through corrected_results
            comp = {'group1': res.data.group1, 'group2': res.data.group2,
                     'pval': res.data.pvalue, 'test': res.data.test_short_name,
                                'correction_method': res.data.correction_method,
                                  'corrected_sig': res.data.corrected_significance}
            comp_list.append(comp)
    posthoc_sig = pd.DataFrame(comp_list)
    return posthoc_sig

## TO GET MULTI HUE x CATEGORY
def get_annot_posthoc_result_df(result_by_stage):
    #result by stage- contains information 
    comp_dict,comp_list = {},  []     # result_by_stage = all_ax_annots#  [r for r in all_ax_annots]
    for stage in result_by_stage:    ## loop over all combos 
        stage_name = set([res.data.group1[0] for res in stage])    # print(stage_name)
        for count, phase in enumerate(stage_name):        # print(counter, phase)
            comp_dict[phase] = {}
            for res in stage: #scroll through corrected_results
                stage_group = res.data.group1[0]
                if stage_group == phase:
                    g1,g2 = res.data.group1[1],  res.data.group2[1] # group_comp = " v ".join([g1, g2])                # print(group_comp)
                    comp_dict[phase] = {'stage_group':stage_group, 'group1': g1, 'group2': g2, 'pval': res.data.pvalue, 'test': res.data.test_short_name,
                                        'correction_method': res.data.correction_method, 'corrected_sig': res.data.corrected_significance}
                    comp_list.append(comp_dict[phase])
    posthoc_sig = pd.DataFrame(comp_list)
    return posthoc_sig

############### CUSTOM ANNOTATION FUNCTIONS
## functions for custom annotations- adapted frmo statnnotation functions using ANNOTATOR object
from matplotlib import lines
##custom local anotator function
def custom_line_text_annotate_pair(annot_obj, annotation, ax_to_data, ann_list, orig_value_lim):
    #ADAPTED from nnnotator function
        group_coord_1,group_coord_2 = annotation.structs[0]['group_coord'], annotation.structs[1]['group_coord']
        group_i1,group_i2 = annotation.structs[0]['group_i'], annotation.structs[1]['group_i']
        # Find y maximum for all the y_stacks *in between* group1 and group2
        ystack_max =  np.nanargmax(annot_obj._value_stack_arr[1,np.where((group_coord_1 <= annot_obj._value_stack_arr[0, :]) & (annot_obj._value_stack_arr[0, :] <= group_coord_2))])
        i_value_max_in_range_g1_g2 = group_i1 +ystack_max 
        value = annot_obj._get_value_for_pair(i_value_max_in_range_g1_g2)
        # Determine lines in axes coordinates
        ax_line_group = [group_coord_1, group_coord_1, group_coord_2, group_coord_2]
        ax_line_value = [value, value + annot_obj.line_height, value + annot_obj.line_height, value]
        lists = ((ax_line_group, ax_line_value) if annot_obj.orient == 'v' else (ax_line_value, ax_line_group))
        points = [ax_to_data.transform((x, y)) for x, y in zip(*lists)]
        line_x, line_y = zip(*points)
        ## plot line itannot_obj 
        custom_plot_line(annot_obj,line_x, line_y)
        xy_params = annot_obj._get_xy_params(group_coord_1, group_coord_2, line_x, line_y)
        value_top_annot = value + annot_obj.line_height
        #OPTIONALLY ANNOTATE TEXT 
        if annotation.text is not None:
            ann = annot_obj.ax.annotate(annotation.text, textcoords='offset points',xycoords='data', ha='center', va='bottom',
                                        fontsize=annot_obj._pvalue_format.fontsize, clip_on=False, annotation_clip=False, **xy_params)
        #     ann_list.append(ann)
        #     set_lim = {'v': 'set_ylim','h': 'set_xlim'}[annot_obj.orient]
        #     getattr(annot_obj.ax, set_lim)(orig_value_lim)
        #     value_top_annot = annot_obj._annotate_pair_text(ann, value) #returns value_top_annot
        # # value_coord = {'h': 0, 'v': 1}[self.orient]
        # value_top_annot = (self.ax.transAxes.inverted().transform(value_top_display)[value_coord])
        # Fill the highest value position of the annotation into value_stack # for all positions in the range group_coord_1 to group_coord_2
        annot_obj._value_stack_arr[1, (group_coord_1 <= annot_obj._value_stack_arr[0, :]) & (annot_obj._value_stack_arr[0, :] <= group_coord_2)] = value_top_annot
        # Increment the counter of annotations in the value_stack array
        annot_obj._value_stack_arr[2, group_i1:group_i2 + 1] += 1

######
## TO- replace the existing line annotation
def custom_line_only_annotate_pair(annot_obj, annotation, ax_to_data, ann_list, orig_value_lim):
    #ADAPTED from nnnotator function
        group_coord_1,group_coord_2 = annotation.structs[0]['group_coord'], annotation.structs[1]['group_coord']
        group_i1,group_i2 = annotation.structs[0]['group_i'], annotation.structs[1]['group_i']
        # Find y maximum for all the y_stacks *in between* group1 and group2
        ystack_max =  np.nanargmax(annot_obj._value_stack_arr[1,np.where((group_coord_1 <= annot_obj._value_stack_arr[0, :]) & (annot_obj._value_stack_arr[0, :] <= group_coord_2))])
        i_value_max_in_range_g1_g2 = group_i1 +ystack_max 
        value = annot_obj._get_value_for_pair(i_value_max_in_range_g1_g2)
        # Determine lines in axes coordinates
        ax_line_group = [group_coord_1, group_coord_1, group_coord_2, group_coord_2]
        ax_line_value = [value, value + annot_obj.line_height, value + annot_obj.line_height, value]
        lists = ((ax_line_group, ax_line_value) if annot_obj.orient == 'v' else (ax_line_value, ax_line_group))
        points = [ax_to_data.transform((x, y)) for x, y in zip(*lists)]
        line_x, line_y = zip(*points)
        ## plot line itannot_obj 
        custom_plot_line(annot_obj,line_x, line_y)
        xy_params = annot_obj._get_xy_params(group_coord_1, group_coord_2, line_x, line_y)
        value_top_annot = value + annot_obj.line_height
        annot_obj._value_stack_arr[1, (group_coord_1 <= annot_obj._value_stack_arr[0, :]) & (annot_obj._value_stack_arr[0, :] <= group_coord_2)] = value_top_annot
        # Increment the counter of annotations in the value_stack array
        annot_obj._value_stack_arr[2, group_i1:group_i2 + 1] += 1

def custom_plot_line(annot_obj, line_x, line_y):
    if annot_obj.loc == 'inside':
        annot_obj.ax.plot(line_x, line_y, lw=annot_obj.line_width, c=annot_obj.color, clip_on=False)
    else:
        line = lines.Line2D(line_x, line_y, lw=annot_obj.line_width,c=annot_obj.color, transform=annot_obj.ax.transData)
        line.set_clip_on(False)
        annot_obj.ax.add_line(line)

## funcition DAG
#call 1- get_plot_posthoc_test_annots_by_stage_group()
# in call 1: 
    # ->    for loop through x axis categories:  (stages )
                # do call 2: get_geno_comparisons_stratefied_by_phase()
                    # call 2 returns get list of HUEs (e.g. geno-day levels) to compare
                #do call 3 with call 2 output list: plot_custom_posthoc_annot()
                    #call 3: creates annotator object with input pairs 
                    #call 3: configure anntoator object with input test
                # do call 4 with call 3 annotator object, custom_annotate()
                    # call 4:for list of annotation comparison pairs input into call 4, 
                    #do call 5: custom_line_only_annotate_pair() for each of those pairs 

    
## major func- loop
def get_plot_posthoc_test_annots_by_stage_group(ax_plot,plot_params, stage_list, geno_order, annot_params = None, combos_to_skip = None):
    """#TO- given an ax, and plot in ax, created by info in plot params, a list of task stages to iterate over (usually on the x axis),
    # return-  annot_obj_store, a dict where key:value is stage_name : annotator object created on that stage
    #all ax annot, a list of each *annotation* object for the stage being iterated over,
    # stage_geno_pairs, the dict where key:value is task_stage: (concatenated tuples containing what groups to do post-hoc omparisons at for each level fo task stage)
    """
        # set default aprams for annotation
    if annot_params is None: #if no input aprams given
        annot_params = {'test': 'Mann-Whitney','loc':'outside', 'comparisons_correction': "BY"}
    if combos_to_skip is None:
        combos_to_skip =  [ sorted(['Het postCLNZ', 'WT VEH']), sorted(['Het CLNZ', 'WT VEH']), sorted(['Het CLNZ', 'Het postCLNZ'])]
        ## make storage
    annot_obj_store, stage_geno_pairs, all_ax_annots =  {}, {},[]#Create list of all possible comparisosn for use in evaluating p-value
    stage_list_clean = [s.replace("_", " ") for s in stage_list]
    print(annot_params)
    for stage_count, stage in enumerate(stage_list):#loop through all phases to make dict of what comparisons to perform within a given set of cells (stratefied within a given phase)
        stage_geno_pairs[stage] =   get_geno_comparisons_stratefied_by_phase(stage, geno_order, combos_to_skip=combos_to_skip)
        annotator_obj, output_annotations  = plot_custom_posthoc_annot(ax_plot,  stage_geno_pairs[stage], plot_params, annotator_default, **annot_params)
        all_ax_annots.append(output_annotations)# #store info about annotations
        annot_obj_store[stage] = annotator_obj##
    return annot_obj_store, all_ax_annots,stage_geno_pairs

def plot_custom_posthoc_annot(ax_plot, posthoc_pairs, plot_params, annotator_default, test = None, loc = None,  **kwargs):
    """ adaptation of normal statannot module plotting function to allow for smaller lines added """
    #set default parameters for plotting 
    if loc == None:
        loc = 'outside'
    if test == None:
        test = 'Mann-Whitney'  
    if 'line_height' not in annotator_default.keys():
        annotator_default['line_height'] = 0.0125
    if 'line_height' in kwargs.keys():
        annotator_default['line_height'] = kwargs['line_height']    # comparisons_correction= "BY",   #run custom annotation on ax_to_plot
    annot_obj = Annotator( ax = ax_plot,pairs = posthoc_pairs, verbose = 0, **plot_params) #setplot context
    annot_obj = annot_obj.configure( line_offset_to_group = 0,  loc = loc, test=test, **annotator_default, **kwargs).apply_test() #set params for nanotation
    _, annotations = custom_annotate(annot_obj) #returns self.ax, self.annotations objects
    return annot_obj, annotations
    # def _update_value_for_loc(self):
        # if self._loc == 'outside':
            # self._value_stack_arr[1, :] = 1

def custom_annotate(annot_obj, annot_type = None,  line_offset=None, line_offset_to_group=None):
    """Add configured annotations to the plot. alters code from the statannotations module for ease of use 
    original file- Annotator.annotate()
    returns: annot_obj._get_output(), which = (ax_obj, [annotations_list])"""
    from statannotations.stats.StatResult import StatResult
    ## annotator object dependent functions
    annot_obj._check_has_plotter()
    annot_obj._update_value_for_loc()
    offset_func = annot_obj.get_offset_func(annot_obj.loc)
    annot_obj.value_offset, annot_obj.line_offset_to_group = offset_func(line_offset, line_offset_to_group)
    annot_obj.validate_test_short_name()    
    orig_value_lim = annot_obj._plotter.get_value_lim()
    ax_to_data = annot_obj._plotter.get_transform_func('ax_to_data')
    #loop over annotati9ons
    ann_list = []
    for annotation in annot_obj.annotations:
        if annot_obj.hide_non_significant and isinstance(annotation.data, StatResult) and not annotation.data.is_significant:
            continue
        if annot_type == None:
            custom_line_only_annotate_pair(annot_obj, annotation, ax_to_data=ax_to_data, ann_list=ann_list,
                                             orig_value_lim=orig_value_lim)
    # reset transformation
    y_stack_max = max(annot_obj._value_stack_arr[1, :])
    ax_to_data = annot_obj._plotter.get_transform_func('ax_to_data')
    lim_offset = 1.02
    value_lims = (([(0, 0), (0, max(lim_offset * y_stack_max, 1))] if annot_obj.loc == 'inside' else [(0, 0), (0, 1)]) if annot_obj.orient == 'v' 
                  else ([(0, 0), (max(lim_offset * y_stack_max, 1), 0)] if annot_obj.loc == 'inside' else [(0, 0), (1, 0)]))
    set_lims = annot_obj.ax.set_ylim if annot_obj.orient == 'v' else annot_obj.ax.set_xlim
    transformed = ax_to_data.transform(value_lims)    # set_lims(transformed[:, 1 if annot_obj.orient == 'v' else 0])
    return annot_obj._get_output() #returns (ax_obj, [annotations_list])

##################### END CUSTOM ANNOTATION ###########################
## post hoc specific testing
def correct_posthoc_geno_compared_in_phase_FDR(ax_of_plot, comparisons_to_make, plot_params):
    is_posthoc_sig = dict()
    for phase in comparisons_to_make.keys():    # #OPTION2- perform FDR on each phase set comparison (FDR within early IA error etc)
        annotator = Annotator( ax_of_plot,comparisons_to_make[phase], verbose = 0, **plot_params);
        _, corrected_results = annotator.configure(test="Mann-Whitney", comparisons_correction="BY",  hide_non_significant=True).apply_and_annotate();
        is_posthoc_sig[phase], comp_dict = get_posthoc_significance_from_statannot(corrected_results)    #get significance output
    is_posthoc_sig_phase = pd.concat([val for val in is_posthoc_sig.values()], axis = 1)
    return is_posthoc_sig_phase, corrected_results

def get_posthoc_significance_from_statannot(corrected_results):
    comp_dict = {}
    phase_list = [res.data.group1[0] for res in corrected_results]
    for count, phase in enumerate(set(phase_list)):
        # print(counter, phase)
        comp_dict[phase.removesuffix("_max")] = {}
        for res in corrected_results: #scroll through corrected_results
            if res.data.group1[0] == phase:
                g1 = res.data.group1[1]
                g2 = res.data.group2[1]
                group_comp = " v ".join([g1, g2])
                comp_dict[phase.removesuffix("_max")][group_comp] = res.data.corrected_significance
    is_posthoc_sig = pd.DataFrame(comp_dict)
    return is_posthoc_sig, comp_dict