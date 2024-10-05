import os
import numpy as np
import pandas as pd
from os.path import join as pjoin
from nilearn.glm.second_level import SecondLevelModel
from nilearn.glm.second_level import make_second_level_design_matrix
from nilearn.glm import threshold_stats_img


def run_2nd_paired_ttest(subjects,contrast_id,cmap1s,cmap2s,datasink):
    # define the input maps
    second_level_input = cmap1s + cmap2s

    # model the effect of condition
    n_subjects = len(subjects)
    condition_effect = np.hstack(([-1] * n_subjects, [1] * n_subjects))

    subject_effect = np.vstack((np.eye(n_subjects), np.eye(n_subjects)))
    subjects = [f'S{i:03d}' for i in range(1, n_subjects + 1)]

    paired_design_matrix = pd.DataFrame(np.hstack((condition_effect[:, np.newaxis], subject_effect)),
                                        columns=[contrast_id] + subjects)

    # second level analysis
    mask_img = '/mnt/data/Template/tpl-MNI152NLin2009cAsym/tpl-MNI152NLin2009cAsym_res-02_desc-brain_mask.nii'
    second_level_model_paired = SecondLevelModel(smoothing_fwhm=6.0, mask_img=mask_img).fit(second_level_input, design_matrix=paired_design_matrix)
    stat_maps_paired = second_level_model_paired.compute_contrast(contrast_id, output_type='all')
    c_map = stat_maps_paired['effect_size']
    t_map = stat_maps_paired['stat']
    z_map = stat_maps_paired['z_score']

    # write the resulting stat images to file
    cmap_path = pjoin(datasink, '{}_tmap.nii.gz'.format(contrast_id))
    c_map.to_filename(cmap_path)

    tmap_path = pjoin(datasink, '{}_tmap.nii.gz'.format(contrast_id))
    t_map.to_filename(tmap_path)

    zmap_path = pjoin(datasink,'{}_zmap.nii.gz'.format(contrast_id))
    z_map.to_filename(zmap_path)


def run_2nd_ttest(subjects, cmap_template, datasink):
    # Select cmaps
    cmaps = [cmap_template.format(str(sub_id).zfill(3)) for sub_id in subjects]

    # Set design matrix
    design_matrix = pd.DataFrame([1] * len(cmaps), columns=['intercept'])
    # run glm
    glm_2nd = SecondLevelModel(smoothing_fwhm=6.0,mask_img='/mnt/data/Template/tpl-MNI152NLin2009cAsym/tpl-MNI152NLin2009cAsym_res-02_desc-brain_mask.nii')
    try:
        glm_2nd = glm_2nd.fit(cmaps, design_matrix=design_matrix)
        print("Model fitting successful.")
    except Exception as e:
        print(f"Error fitting model: {e}")
        return
    stats_map = glm_2nd.compute_contrast(second_level_contrast='intercept', output_type='all')
    t_map = stats_map['stat']
    z_map = stats_map['z_score']

    # write the resulting stat images to file
    t_image_path = os.path.join(datasink, 'mean_tmap.nii.gz')
    t_map.to_filename(t_image_path)

    z_image_path = os.path.join(datasink, 'mean_zmap.nii.gz')
    z_map.to_filename(z_image_path)


if __name__ == "__main__":
    participants_data = pd.read_excel("/mnt/workdir/Development_induction/Data/participants_TUS.xlsx")
    exp_sub_data = participants_data[participants_data['被试组别'] == '实验组']
    sub_ids = exp_sub_data['被试数据编号'].to_list()
    sub_ids.remove('sub-005')

    # configure
    data_root = '/mnt/workdir/Development_induction/Data/BIDS/derivatives/connectivity/seed_voxel/erie_lofc'
    condition_pairs = {'pre_vs_post1':['pre-rest','post-rest1'],
                       'pre_vs_post2':['pre-rest','post-rest2'],
                       'post1_vs_post2':['post-rest1','post-rest2']}
    templates = '/mnt/workdir/Development_induction/Data/BIDS/derivatives/connectivity/seed_voxel/erie_lofc/{}/{}_LOFC_seed_correlation_z.nii.gz'

    for contrast_name, pair_list in condition_pairs.items():
        first_con1, first_con2 = pair_list

        # create output directory
        datasink = pjoin(data_root, 'group', contrast_name)
        os.makedirs(datasink,exist_ok=True)
        print('glm',contrast_name,'start.')

        # calculate repeated measure effect
        first_cmap1 = [templates.format(first_con1, sub_id) for sub_id in sub_ids]
        first_cmap2 = [templates.format(first_con2, sub_id) for sub_id in sub_ids]
        run_2nd_paired_ttest(sub_ids, contrast_name, first_cmap1,first_cmap2, datasink)

    # create output directory pf prerest
    datasink = pjoin(data_root, 'group', 'pre-rest')
    os.makedirs(datasink,exist_ok=True)
    print('glm','pre-rest','start.')
    # calculate repeated measure effect
    prerest_cmap1 = '/mnt/workdir/Development_induction/Data/BIDS/derivatives/connectivity/seed_voxel/erie_lofc/pre-rest/{}_LOFC_seed_correlation_z.nii.gz'
    run_2nd_ttest(sub_ids, prerest_cmap1, datasink)

    # create output directory of post-rest1
    datasink = pjoin(data_root, 'group', 'post-rest1')
    os.makedirs(datasink,exist_ok=True)
    print('glm','post-rest1','start.')

    # calculate mean effect
    postrest1_cmap = '/mnt/workdir/Development_induction/Data/BIDS/derivatives/connectivity/seed_voxel/erie_lofc/post-rest1/{}_LOFC_seed_correlation_z.nii.gz'
    run_2nd_ttest(sub_ids, postrest1_cmap, datasink)

    # create output directory
    datasink = pjoin(data_root, 'group', 'post-rest2')
    os.makedirs(datasink,exist_ok=True)
    print('glm','post-rest2','start.')

    # calculate repeated measure effect
    postrest2_cmap = '/mnt/workdir/Development_induction/Data/BIDS/derivatives/connectivity/seed_voxel/erie_lofc/post-rest2/{}_LOFC_seed_correlation_z.nii.gz'
    run_2nd_ttest(sub_ids, postrest2_cmap, datasink)